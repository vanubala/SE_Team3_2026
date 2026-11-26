"""Test data and tokens for the registration and assignment tests."""
import os
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy.orm import Session

from app.db.models import Compartment, Locker

JWT_SECRET = "test-secret-" + "x" * 53  # 65 bytes; the HS512 test needs at least 64
NAMESPACE = uuid.UUID("6f1c2d4e-9a7b-4c3d-8e2f-1a2b3c4d5e6f")
NOW = datetime(2026, 11, 25, 9, 0, tzinfo=UTC)
TOMORROW = NOW + timedelta(days=1)
COURIERS = ("courier-1", "courier-2")  # users that exist in every test database

# Database tests run on in-memory SQLite, and also on PostgreSQL if TEST_DATABASE_URL is set.
POSTGRESQL_URL = os.environ.get("TEST_DATABASE_URL")


def uid(name: str) -> uuid.UUID:
    """Fixed UUID for a test name, e.g. uid("comp-04")."""
    return uuid.uuid5(uuid.NAMESPACE_URL, name)


def add_locker(session: Session, locker="loc-belval-01", status="ONLINE", compartments=()) -> None:
    """Adds a locker with compartments given as (name, number, size, status). IDs are uid(name)."""
    session.add(Locker(
        locker_id=uid(locker),
        name="Belval Plaza Station",
        address="1 Avenue du Swing, Belval",
        gps_location="49.5,5.95",
        opening_hours="24/7",
        operational_status=status,
    ))
    session.flush()  # the locker must exist before its compartments (foreign key)
    for compartment, number, size, compartment_status in compartments:
        session.add(Compartment(
            compartment_id=uid(compartment),
            locker_id=uid(locker),
            compartment_number=number,
            size_category=size,
            status=compartment_status,
        ))
    session.commit()


def token(role="COURIER", courier="courier-1", expires_in=timedelta(hours=1), secret=JWT_SECRET,
          algorithm="HS256", **changes) -> str:
    """Builds a test token for the courier uid(courier). Other keyword arguments replace claims; None removes one."""
    issued = datetime.now(UTC)
    claims = {"sub": str(uid(courier)), "role": role, "iss": "smart-locker-auth", "aud": "smart-locker-api",
              "iat": issued, "exp": issued + expires_in, **changes}
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, secret, algorithm=algorithm)


def auth(**claims) -> dict:
    return {"Authorization": f"Bearer {token(**claims)}"}
