"""Business rules for UC5. No HTTP code here."""
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from .models import Compartment, CompartmentStatus, Locker, LockerStatus, SizeCategory
from .repository import LockerRepository


class LockerManagementError(Exception):
    pass


class NotFoundError(LockerManagementError):
    pass


class ConflictError(LockerManagementError):
    pass


class InvalidStatusError(LockerManagementError):
    pass


class StorageError(LockerManagementError):
    pass


@dataclass(frozen=True)
class Occupancy:
    total: int
    available: int
    reserved: int
    occupied: int
    maintenance: int
    occupancy_rate: float
    available_by_size: dict[str, int]


@dataclass(frozen=True)
class LockerOverview:
    locker: Locker
    occupancy: Occupancy
    compartments: list[Compartment]


@dataclass(frozen=True)
class StatusChange:
    target_id: UUID
    status: str
    warning: str | None = None


class LockerManagementService:
    def __init__(self, repository: LockerRepository):
        self.repository = repository

    def get_overview(self) -> list[LockerOverview]:
        """Every station with its occupancy figures (FR_09)."""
        with self._storage_errors():
            return [
                LockerOverview(locker, _occupancy(locker.compartments), locker.compartments)
                for locker in self.repository.find_all_with_compartments()
            ]

    def change_compartment_status(
        self, compartment_id: UUID, status: CompartmentStatus
    ) -> StatusChange:
        """Block a compartment or restore it to service (FR_10)."""
        # RESERVED and OCCUPIED result from parcel operations, never from an admin.
        if status not in (CompartmentStatus.AVAILABLE, CompartmentStatus.MAINTENANCE):
            raise InvalidStatusError("Status must be AVAILABLE or MAINTENANCE.")

        with self._transaction():
            compartment = self.repository.get_compartment_for_update(compartment_id)
            if compartment is None:
                raise NotFoundError(f"Compartment {compartment_id} does not exist.")

            version = compartment.version
            has_parcel = self.repository.has_active_parcel(compartment_id)
            if status == CompartmentStatus.AVAILABLE and has_parcel:
                raise ConflictError(
                    f"Compartment {compartment.compartment_number} still has an active parcel. "
                    "Resolve the parcel before making it AVAILABLE."
                )
            warning = None
            if status == CompartmentStatus.MAINTENANCE and has_parcel:
                warning = (
                    "This compartment still has an active parcel. "
                    "No new parcel can be assigned to it."
                )
            if compartment.status != status and not self.repository.set_compartment_status(
                compartment_id, status, version
            ):
                raise ConflictError(
                    "The compartment was changed by someone else. Reload it and try again."
                )
        return StatusChange(compartment_id, status.value, warning)

    def change_locker_status(self, locker_id: UUID, status: LockerStatus) -> StatusChange:
        """Take a whole station out of service or restore it (FR_10).

        Compartment statuses are left as they are, so restoring the station does
        not restore compartments that were individually under maintenance.
        """
        with self._transaction():
            locker = self.repository.get_locker_for_update(locker_id)
            if locker is None:
                raise NotFoundError(f"Locker {locker_id} does not exist.")
            warning = None
            if status != LockerStatus.ONLINE:
                parcels = self.repository.count_active_parcels(locker_id)
                if parcels:
                    warning = (
                        f"This station still has {parcels} active parcel(s). "
                        "No new parcels can be assigned to it."
                    )
            self.repository.set_locker_status(locker_id, status)
        return StatusChange(locker_id, status.value, warning)

    @contextmanager
    def _storage_errors(self):
        try:
            yield
        except SQLAlchemyError as exc:
            raise StorageError("Locker data is temporarily unavailable.") from exc

    @contextmanager
    def _transaction(self):
        session = self.repository.session
        with self._storage_errors():
            try:
                yield
                session.commit()
            except Exception:
                session.rollback()
                raise


def _occupancy(compartments: list[Compartment]) -> Occupancy:
    total = len(compartments)
    counts = Counter(c.status for c in compartments)
    free_sizes = Counter(
        c.size_category for c in compartments if c.status == CompartmentStatus.AVAILABLE
    )
    in_use = counts["RESERVED"] + counts["OCCUPIED"]
    return Occupancy(
        total=total,
        available=counts["AVAILABLE"],
        reserved=counts["RESERVED"],
        occupied=counts["OCCUPIED"],
        maintenance=counts["MAINTENANCE"],
        occupancy_rate=round(100 * in_use / total, 1) if total else 0.0,
        available_by_size={size.value: free_sizes[size.value] for size in SizeCategory},
    )
