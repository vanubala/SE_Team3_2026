"""Reading lockers and compartments, and reserving a compartment."""
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.models import Compartment, CompartmentStatus, Locker, LockerStatus


class LockerRepository:
    def __init__(self, session: Session):
        self.session = session

    def find_locker(self, locker_id: UUID) -> Locker | None:
        # populate_existing: read the row again, so a status change committed in the meantime is seen.
        return self.session.get(Locker, locker_id, populate_existing=True)

    def find_compartment(self, compartment_id: UUID) -> Compartment | None:
        return self.session.get(Compartment, compartment_id)

    def find_available_compartments(self, locker_id: UUID, sizes: list[str]) -> list[Compartment]:
        query = select(Compartment).where(
            Compartment.locker_id == locker_id,
            Compartment.status == CompartmentStatus.AVAILABLE,
            Compartment.size_category.in_(sizes),
        )
        return list(self.session.scalars(query))
    
    def find_all_compartments(self, locker_id: UUID) -> list[Compartment]:
        query = (
            select(Compartment)
            .where(Compartment.locker_id == locker_id)
            .order_by(Compartment.compartment_number)
        )
        return list(self.session.scalars(query))
    
    def reserve_compartment(self, locker_id: UUID, compartment_id: UUID) -> bool:
        # Shared lock on the locker row, so the locker cannot be set offline during the reservation. The caller commits.
        locker_status = self.session.scalar(
            select(Locker.operational_status).where(Locker.locker_id == locker_id).with_for_update(read=True)
        )
        if locker_status != LockerStatus.ONLINE:
            return False
        # Only updates the compartment if it is still AVAILABLE. version is the optimistic-locking counter of the table.
        result = self.session.execute(
            update(Compartment)
            .where(
                Compartment.compartment_id == compartment_id,
                Compartment.locker_id == locker_id,
                Compartment.status == CompartmentStatus.AVAILABLE,
            )
            .values(status=CompartmentStatus.RESERVED, version=Compartment.version + 1)
        )
        return result.rowcount == 1
