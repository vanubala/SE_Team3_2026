"""SQLite repository: persistence and atomic duplicate prevention."""
from pathlib import Path
import sqlite3


class DuplicateTrackingNumber(Exception):
    pass


class ParcelRepository:
    def __init__(self, database_path: str):
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS parcels (
                    parcel_id TEXT PRIMARY KEY,
                    tracking_number TEXT NOT NULL UNIQUE,
                    courier_id TEXT NOT NULL,
                    size TEXT NOT NULL CHECK (size IN ('SMALL', 'MEDIUM', 'LARGE')),
                    expected_delivery_at TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status = 'REGISTERED'),
                    pickup_deadline TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_parcels_courier ON parcels(courier_id)")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def exists_tracking_number(self, tracking_number: str) -> bool:
        with self._connect() as db:
            return db.execute(
                "SELECT 1 FROM parcels WHERE tracking_number = ?", (tracking_number,)
            ).fetchone() is not None

    def save(self, parcel: dict) -> dict:
        try:
            with self._connect() as db:
                db.execute("""
                    INSERT INTO parcels (parcel_id, tracking_number, courier_id, size,
                                         expected_delivery_at, notes, status, pickup_deadline, created_at)
                    VALUES (:parcel_id, :tracking_number, :courier_id, :size,
                            :expected_delivery_at, :notes, :status, :pickup_deadline, :created_at)
                """, parcel)
        except sqlite3.IntegrityError as exc:
            # Unique constraint is authoritative, even for concurrent requests.
            if "UNIQUE constraint failed" in str(exc) or "PRIMARY KEY" in str(exc):
                raise DuplicateTrackingNumber from exc
            raise
        return parcel

    def list_for_courier(self, courier_id: str, limit: int = 50) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("""
                SELECT parcel_id, tracking_number, size, expected_delivery_at,
                       notes, status, pickup_deadline, created_at
                FROM parcels WHERE courier_id = ?
                ORDER BY created_at DESC, parcel_id DESC LIMIT ?
            """, (courier_id, limit)).fetchall()
        return [dict(row) for row in rows]
