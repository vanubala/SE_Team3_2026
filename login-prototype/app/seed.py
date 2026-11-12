"""Company accounts that exist from the first start.

Administrator accounts are hardcoded: they cannot be created through the
system, neither by sign-up nor by any API. Courier accounts are seeded the
same way in this prototype; letting an administrator create couriers is a
later use case.

Only IDs, names and companies are hardcoded here. Passwords are never stored
in the code: they are either generated on each start or taken from the
--staff-password option, and only their scrypt hashes reach the database.
"""
from datetime import datetime
import secrets

from .repository import UserRepository
from .security import hash_password

STAFF_ACCOUNTS = (
    # login ID   role             name               company
    ("AD00001", "ADMINISTRATOR", "Morgan Weber",    "Smart Locker Operations"),
    ("AD00002", "ADMINISTRATOR", "Lea Schmit",      "Smart Locker Operations"),
    ("CO00001", "COURIER",       "Tom Muller",      "Demo Logistics"),
    ("CO00002", "COURIER",       "Sara Hoffmann",   "Demo Logistics"),
    ("CO00003", "COURIER",       "Jonas Klein",     "Demo Express"),
)


def seed_staff_accounts(repository: UserRepository, shared_password: str | None,
                        now: datetime) -> list[dict]:
    """Create or refresh the staff accounts. Returns the passwords for display."""
    issued = []
    for login_id, role, name, company in STAFF_ACCOUNTS:
        password = shared_password or secrets.token_urlsafe(9)
        repository.upsert_staff(login_id=login_id, role=role, name=name, company=company,
                                password_hash=hash_password(password), now=now)
        issued.append({"loginId": login_id, "role": role, "name": name, "password": password})
    return issued
