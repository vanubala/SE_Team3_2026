"""Database engine and the unit of work of one request."""
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from .repositories.locker_repository import LockerRepository
from .repositories.parcel_repository import ParcelRepository


def make_engine(url: str) -> Engine:
    if url == "sqlite://":
        # In-memory database for tests: every session must use the same connection.
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(url)


class UnitOfWork:
    """Repositories of one request. Their changes are committed or rolled back together."""

    def __init__(self, session: Session):
        self.session = session
        self.parcels = ParcelRepository(session)
        self.lockers = LockerRepository(session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()
