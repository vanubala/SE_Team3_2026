import os
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import UnitOfWork, make_engine
from app.main import create_app
from app.models import Base, Compartment, Locker

JWT_SECRET = "test-secret-" + "x" * 53  # 65 bytes; the HS512 test needs at least 64
NAMESPACE = uuid.UUID("6f1c2d4e-9a7b-4c3d-8e2f-1a2b3c4d5e6f")
NOW = datetime(2026, 11, 25, 9, 0, tzinfo=UTC)
TOMORROW = NOW + timedelta(days=1)


def uid(name: str) -> uuid.UUID:
    """Fixed UUID for a test name, e.g. uid("comp-04")."""
    return uuid.uuid5(uuid.NAMESPACE_URL, name)


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite://", jwt_secret=JWT_SECRET, parcel_id_namespace=NAMESPACE)


# Database tests run on in-memory SQLite, and also on PostgreSQL if TEST_DATABASE_URL is set.
# Tables are created and dropped for each test.
POSTGRESQL_URL = os.environ.get("TEST_DATABASE_URL")
DATABASES = ["sqlite"] + ([pytest.param("postgresql", marks=pytest.mark.postgresql)] if POSTGRESQL_URL else [])


@pytest.fixture(params=DATABASES)
def engine(request):
    engine = make_engine("sqlite://" if request.param == "sqlite" else POSTGRESQL_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def uow(session) -> UnitOfWork:
    return UnitOfWork(session)


def add_locker(session, locker="loc-belval-01", status="ONLINE", compartments=()):
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


@pytest.fixture
def belval(session):
    """One locker in service: two small, two medium and one large compartment, one medium already reserved."""
    add_locker(session, compartments=[
        ("comp-01", 1, "SMALL", "AVAILABLE"),
        ("comp-02", 2, "SMALL", "AVAILABLE"),
        ("comp-03", 3, "MEDIUM", "RESERVED"),
        ("comp-04", 4, "MEDIUM", "AVAILABLE"),
        ("comp-09", 9, "LARGE", "AVAILABLE"),
    ])
    return uid("loc-belval-01")


def token(role="COURIER", courier="courier-1", expires_in=timedelta(hours=1), secret=JWT_SECRET,
          algorithm="HS256", **changes) -> str:
    """Builds a test token for the courier uid(courier). Other keyword arguments replace claims; None removes one."""
    issued = datetime.now(UTC)
    claims = {"sub": str(uid(courier)), "role": role, "iss": "smart-locker-auth", "aud": "smart-locker-api",
              "iat": issued, "exp": issued + expires_in, **changes}
    return jwt.encode({k: v for k, v in claims.items() if v is not None}, secret, algorithm=algorithm)


def auth(**claims) -> dict:
    return {"Authorization": f"Bearer {token(**claims)}"}


@pytest.fixture
def client(settings, engine):
    with TestClient(create_app(settings, engine)) as client:  # "with" runs the startup and shutdown code
        yield client
