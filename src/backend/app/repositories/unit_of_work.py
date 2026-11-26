"""The repositories of one request, for parcel registration and assignment."""
from sqlalchemy.orm import Session

from app.repositories.locker_repository import LockerRepository
from app.repositories.parcel_repository import ParcelRepository


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
