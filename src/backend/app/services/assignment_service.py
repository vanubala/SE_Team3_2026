"""Compartment assignment (UC2, FR_04, NFR_04)."""
from uuid import UUID

from app.db.models import Compartment, LockerStatus, Parcel, ParcelStatus, SizeCategory
from app.repositories.unit_of_work import UnitOfWork
from app.services.parcel_errors import (
    CompartmentNotFound,
    CompartmentTaken,
    CompartmentTooSmall,
    LockerNotFound,
    LockerUnavailable,
    NoCompartmentAvailable,
    ParcelNotFound,
    ParcelNotRegistered,
)
from app.services.sizes import SIZE_RANK, parse_size


def fitting_sizes(parcel_size: SizeCategory) -> list[SizeCategory]:
    return [size for size, rank in SIZE_RANK.items() if rank >= SIZE_RANK[parcel_size]]


def select_smallest_fitting_compartment(compartments: list[Compartment]) -> list[Compartment]:
    return sorted(compartments, key=lambda c: (SIZE_RANK[c.size_category], c.compartment_number))


class AssignmentService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_available_and_recommended_compartments(
        self, locker_id: UUID, parcel_size: str
    ) -> tuple[Compartment, list[Compartment]]:
        """Returns the recommended compartment and all AVAILABLE compartments of the locker that fit
        the parcel, smallest first. The locker must be ONLINE.
        Raises InvalidParcelData, LockerNotFound, LockerUnavailable or NoCompartmentAvailable."""
        size = parse_size(parcel_size)
        self._check_locker_in_service(locker_id)
        options = self.uow.lockers.find_available_compartments(locker_id, fitting_sizes(size))
        if not options:
            raise NoCompartmentAvailable("No suitable compartment available at this locker")
        ordered = select_smallest_fitting_compartment(options)
        return ordered[0], ordered

    def assign_compartment(
        self, courier_id: UUID, parcel_id: UUID, locker_id: UUID, compartment_id: UUID
    ) -> tuple[Parcel, Compartment]:
        """Reserves the compartment and sets the parcel to ASSIGNED. Only the courier who registered the
        parcel can do this. Returns the parcel and the compartment.
        Raises ParcelNotFound (also for another courier's parcel), ParcelNotRegistered, LockerNotFound,
        LockerUnavailable, CompartmentNotFound, CompartmentTooSmall or CompartmentTaken.
        Nothing is changed when an error is raised."""
        try:
            parcel = self.uow.parcels.find_by_id(parcel_id)
            # Same error as for a missing parcel, so other couriers' parcel IDs are not revealed.
            if parcel is None or parcel.registered_by_courier_id != courier_id:
                raise ParcelNotFound("Parcel not found")
            if parcel.status != ParcelStatus.REGISTERED:
                raise ParcelNotRegistered("Parcel is not waiting for a compartment")
            self._check_locker_in_service(locker_id)
            compartment = self.uow.lockers.find_compartment(compartment_id)
            if compartment is None or compartment.locker_id != locker_id:
                raise CompartmentNotFound("Compartment not found at this locker")
            if SIZE_RANK[compartment.size_category] < SIZE_RANK[parcel.size_category]:
                raise CompartmentTooSmall("Compartment is too small for this parcel")
            if not self.uow.lockers.reserve_compartment(locker_id, compartment_id):
                # The compartment was taken or the locker went offline; check the locker again for the right error.
                self._check_locker_in_service(locker_id)
                raise CompartmentTaken("Compartment no longer available")
            if not self.uow.parcels.update_assignment(parcel_id, compartment_id):
                raise ParcelNotRegistered("Parcel is not waiting for a compartment")
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return parcel, compartment

    def _check_locker_in_service(self, locker_id: UUID) -> None:
        locker = self.uow.lockers.find_locker(locker_id)
        if locker is None:
            raise LockerNotFound("Locker not found")
        if locker.operational_status != LockerStatus.ONLINE:
            raise LockerUnavailable("Locker is not in service")
