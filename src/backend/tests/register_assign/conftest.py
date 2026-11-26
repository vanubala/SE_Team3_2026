import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db.models import Base, User
from app.main import create_app
from app.repositories.unit_of_work import UnitOfWork
from register_assign.support import COURIERS, JWT_SECRET, NAMESPACE, POSTGRESQL_URL, add_locker, uid

DATABASES = ["sqlite"] + ([pytest.param("postgresql", marks=pytest.mark.postgres)] if POSTGRESQL_URL else [])


@pytest.fixture
def settings() -> Settings:
    return Settings(database_url="sqlite+pysqlite://", jwt_secret=JWT_SECRET, parcel_id_namespace=NAMESPACE)


def sqlite_engine():
    engine = create_engine("sqlite+pysqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def enforce_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    return engine


@pytest.fixture(params=DATABASES)
def engine(request):
    """The shared tables, created and dropped for each test, with the couriers of COURIERS as users."""
    engine = sqlite_engine() if request.param == "sqlite" else create_engine(POSTGRESQL_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(User(user_id=uid(name), name=name, email=f"{name}@example.test", password_hash="not-used",
                             role="COURIER") for name in COURIERS)
        session.commit()
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


@pytest.fixture
def client(settings, engine):
    with TestClient(create_app(settings, engine=engine)) as client:  # "with" runs the startup and shutdown code
        yield client
