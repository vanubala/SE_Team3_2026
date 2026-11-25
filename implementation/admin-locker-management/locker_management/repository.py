"""Data access for lockers and compartments.

Methods never commit: the calling service owns the transaction, so a
compartment update and a parcel update can succeed or fail together (NFR_04).
"""
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from .models import (
    ACTIVE_PARCEL_STATUSES,
    Compartment,
    CompartmentStatus,
    Locker,
    LockerStatus,
    Parcel,
)


class LockerRepository:
    def __init__(self, session: Session):
        self.session = session

    # Monitoring ---------------------------------------------------------------

    def find_all_with_compartments(self) -> list[Locker]:
        statement = (
            select(Locker)
            .options(selectinload(Locker.compartments))
            .order_by(Locker.name, Locker.locker_id)
        )
        return list(self.session.scalars(statement))

    # Administration -----------------------------------------------------------

    def get_locker_for_update(self, locker_id: UUID) -> Locker | None:
        return self.session.scalar(
            select(Locker).where(Locker.locker_id == locker_id)
            .with_for_update().execution_options(populate_existing=True)
        )

    def get_compartment_for_update(self, compartment_id: UUID) -> Compartment | None:
        return self.session.scalar(
            select(Compartment).where(Compartment.compartment_id == compartment_id)
            .with_for_update().execution_options(populate_existing=True)
        )

    def has_active_parcel(self, compartment_id: UUID) -> bool:
        return self.session.scalar(
            select(Parcel.parcel_id).where(
                Parcel.compartment_id == compartment_id,
                Parcel.status.in_(ACTIVE_PARCEL_STATUSES),
            ).limit(1)
        ) is not None

    def count_active_parcels(self, locker_id: UUID) -> int:
        return self.session.scalar(
            select(func.count()).select_from(Parcel)
            .join(Compartment, Parcel.compartment_id == Compartment.compartment_id)
            .where(
                Compartment.locker_id == locker_id,
                Parcel.status.in_(ACTIVE_PARCEL_STATUSES),
            )
        )

    def set_locker_status(self, locker_id: UUID, status: LockerStatus) -> None:
        self.session.execute(
            update(Locker).where(Locker.locker_id == locker_id)
            .values(operational_status=status.value)
        )

    def set_compartment_status(
        self, compartment_id: UUID, status: CompartmentStatus, expected_version: int
    ) -> bool:
        """False means another transaction changed the compartment first."""
        result = self.session.execute(
            update(Compartment).where(
                Compartment.compartment_id == compartment_id,
                Compartment.version == expected_version,
            ).values(status=status.value, version=Compartment.version + 1)
        )
        return result.rowcount == 1

    # Used by the assignment, deposit and pickup services -----------------------

    def reserve_compartment(self, locker_id: UUID, compartment_id: UUID) -> bool:
        """AVAILABLE -> RESERVED (UC2), only if the station is ONLINE."""
        # The shared lock stops an administrator taking the station out of
        # service while the reservation is in progress.
        locker_status = self.session.scalar(
            select(Locker.operational_status)
            .where(Locker.locker_id == locker_id).with_for_update(read=True)
        )
        if locker_status != LockerStatus.ONLINE:
            return False
        return self._transition(
            compartment_id, CompartmentStatus.AVAILABLE, CompartmentStatus.RESERVED,
            locker_id=locker_id,
        )

    def occupy_compartment(self, compartment_id: UUID) -> bool:
        """RESERVED -> OCCUPIED (UC3)."""
        return self._transition(
            compartment_id, CompartmentStatus.RESERVED, CompartmentStatus.OCCUPIED
        )

    def release_compartment(self, compartment_id: UUID) -> bool:
        """OCCUPIED -> AVAILABLE (UC4).

        False if not OCCUPIED. In particular a compartment put in MAINTENANCE
        while it held the parcel stays in MAINTENANCE after collection.
        """
        return self._transition(
            compartment_id, CompartmentStatus.OCCUPIED, CompartmentStatus.AVAILABLE
        )

    def _transition(
        self, compartment_id: UUID, current: CompartmentStatus, new: CompartmentStatus,
        locker_id: UUID | None = None,
    ) -> bool:
        statement = update(Compartment).where(
            Compartment.compartment_id == compartment_id,
            Compartment.status == current.value,
        )
        if locker_id is not None:
            statement = statement.where(Compartment.locker_id == locker_id)
        result = self.session.execute(
            statement.values(status=new.value, version=Compartment.version + 1)
        )
        return result.rowcount == 1
