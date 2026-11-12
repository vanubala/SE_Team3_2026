"""SQLite storage for accounts and one-time codes."""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3
import uuid

from .identifiers import Identifier, IdentifierKind

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id         TEXT PRIMARY KEY,
    role            TEXT NOT NULL CHECK (role IN ('COURIER', 'ADMINISTRATOR', 'CUSTOMER')),
    login_id        TEXT UNIQUE,
    email           TEXT UNIQUE,
    phone           TEXT UNIQUE,
    name            TEXT NOT NULL,
    company         TEXT,
    password_hash   TEXT,
    verified        INTEGER NOT NULL DEFAULT 0,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TEXT,
    created_at      TEXT NOT NULL,
    -- Staff sign in with a company ID and a password. Senders/recipients sign in
    -- with an email or phone number and never hold a company ID or a password.
    CHECK (
        (role IN ('COURIER', 'ADMINISTRATOR')
            AND login_id IS NOT NULL AND password_hash IS NOT NULL)
        OR
        (role = 'CUSTOMER'
            AND login_id IS NULL AND password_hash IS NULL
            AND (email IS NOT NULL OR phone IS NOT NULL))
    ),
    CHECK (
        login_id IS NULL
        OR (role = 'COURIER' AND login_id GLOB 'CO[0-9][0-9][0-9][0-9][0-9]')
        OR (role = 'ADMINISTRATOR' AND login_id GLOB 'AD[0-9][0-9][0-9][0-9][0-9]')
    )
);

CREATE TABLE IF NOT EXISTS one_time_codes (
    code_id    TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    purpose    TEXT NOT NULL CHECK (purpose IN ('LOGIN', 'REGISTER')),
    code_hash  TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at    TEXT
);

CREATE INDEX IF NOT EXISTS idx_codes_user ON one_time_codes(user_id, purpose);
"""

_LOOKUP_COLUMN = {
    IdentifierKind.COURIER_ID: "login_id",
    IdentifierKind.ADMIN_ID: "login_id",
    IdentifierKind.EMAIL: "email",
    IdentifierKind.PHONE: "phone",
}


def _iso(moment: datetime) -> str:
    return moment.isoformat(timespec="seconds")


class UserRepository:
    def __init__(self, database_path: str):
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def _db(self):
        conn = sqlite3.connect(self.database_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _one(self, sql: str, params: tuple) -> dict | None:
        with self._db() as db:
            row = db.execute(sql, params).fetchone()
        return dict(row) if row else None

    # Lookups -----------------------------------------------------------------

    def get(self, user_id: str) -> dict | None:
        return self._one("SELECT * FROM users WHERE user_id = ?", (user_id,))

    def find_by_identifier(self, identifier: Identifier) -> dict | None:
        column = _LOOKUP_COLUMN[identifier.kind]
        return self._one(f"SELECT * FROM users WHERE {column} = ?", (identifier.value,))

    def list_users(self) -> list[dict]:
        with self._db() as db:
            rows = db.execute("""
                SELECT * FROM users
                ORDER BY CASE role WHEN 'ADMINISTRATOR' THEN 0 WHEN 'COURIER' THEN 1 ELSE 2 END,
                         login_id, created_at
            """).fetchall()
        return [dict(row) for row in rows]

    # Accounts ----------------------------------------------------------------

    def upsert_staff(self, *, login_id: str, role: str, name: str, company: str,
                     password_hash: str, now: datetime) -> None:
        with self._db() as db:
            db.execute("""
                INSERT INTO users (user_id, role, login_id, name, company, password_hash,
                                   verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(login_id) DO UPDATE SET
                    name = excluded.name,
                    company = excluded.company,
                    password_hash = excluded.password_hash,
                    failed_attempts = 0,
                    locked_until = NULL
            """, (uuid.uuid4().hex, role, login_id, name, company, password_hash, _iso(now)))

    def create_customer(self, *, name: str, identifier: Identifier, now: datetime) -> dict:
        user_id = uuid.uuid4().hex
        email = identifier.value if identifier.kind is IdentifierKind.EMAIL else None
        phone = identifier.value if identifier.kind is IdentifierKind.PHONE else None
        with self._db() as db:
            db.execute("""
                INSERT INTO users (user_id, role, email, phone, name, verified, created_at)
                VALUES (?, 'CUSTOMER', ?, ?, ?, 0, ?)
            """, (user_id, email, phone, name, _iso(now)))
        return self.get(user_id)

    def update_name(self, user_id: str, name: str) -> None:
        with self._db() as db:
            db.execute("UPDATE users SET name = ? WHERE user_id = ?", (name, user_id))

    def mark_verified(self, user_id: str) -> None:
        with self._db() as db:
            db.execute("UPDATE users SET verified = 1 WHERE user_id = ?", (user_id,))

    # Failed attempts and lockout ----------------------------------------------

    def register_failure(self, user_id: str, *, max_attempts: int, lock_until: datetime) -> bool:
        """Count one failed attempt. Returns True when this attempt locks the account."""
        with self._db() as db:
            attempts = db.execute("SELECT failed_attempts FROM users WHERE user_id = ?",
                                  (user_id,)).fetchone()[0] + 1
            if attempts >= max_attempts:
                db.execute("UPDATE users SET failed_attempts = 0, locked_until = ? WHERE user_id = ?",
                           (_iso(lock_until), user_id))
                # Any outstanding code is thrown away; a new one must be requested.
                db.execute("DELETE FROM one_time_codes WHERE user_id = ? AND used_at IS NULL",
                           (user_id,))
                return True
            db.execute("UPDATE users SET failed_attempts = ? WHERE user_id = ?", (attempts, user_id))
            return False

    def clear_failures(self, user_id: str) -> None:
        with self._db() as db:
            db.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE user_id = ?",
                       (user_id,))

    # One-time codes ------------------------------------------------------------

    def add_code(self, *, user_id: str, purpose: str, code_hash: str,
                 now: datetime, expires: datetime) -> None:
        with self._db() as db:
            # Only the newest code for a purpose is valid.
            db.execute("DELETE FROM one_time_codes WHERE user_id = ? AND purpose = ? AND used_at IS NULL",
                       (user_id, purpose))
            db.execute("""
                INSERT INTO one_time_codes (code_id, user_id, purpose, code_hash, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (uuid.uuid4().hex, user_id, purpose, code_hash, _iso(now), _iso(expires)))

    def latest_code(self, user_id: str, purpose: str) -> dict | None:
        return self._one("""
            SELECT * FROM one_time_codes
            WHERE user_id = ? AND purpose = ? AND used_at IS NULL
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, purpose))

    def consume_code(self, code_id: str, now: datetime) -> None:
        with self._db() as db:
            db.execute("UPDATE one_time_codes SET used_at = ? WHERE code_id = ?", (_iso(now), code_id))
