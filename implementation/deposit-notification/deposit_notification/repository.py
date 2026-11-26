"""SQLAlchemy adapter that reuses UC5's LockerRepository operations.

Pass the existing LockerRepository and the database owner's ORM classes into
this adapter. It intentionally does not define duplicate team models. The
service owns commit/rollback, matching the UC5 repository contract.
"""
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .contracts import AssignedCompartment, DepositCommitResult
from .service import DepositConflict, ParcelNotFound, PickupCodeCollision


class LockerRepositoryPort(Protocol):
    """Structural contract implemented by Raed's UC5 LockerRepository.

    Both adapters share its SQLAlchemy Session; UC3 owns the surrounding
    transaction and calls occupy_compartment only for RESERVED compartments.
    """

    session: Session

    def get_compartment_for_update(self, compartment_id: UUID) -> Any | None: ...

    def occupy_compartment(self, compartment_id: UUID) -> bool: ...


class SQLAlchemyDepositRepository:
    def __init__(
        self,
        locker_repository: LockerRepositoryPort,
        *,
        parcel_model: type[Any],
        compartment_model: type[Any],
        locker_model: type[Any],
        pickup_code_model: type[Any],
    ) -> None:
        self.locker_repository = locker_repository
        self.session: Session = locker_repository.session
        self._parcel = parcel_model
        self._compartment = compartment_model
        self._locker = locker_model
        self._pickup_code = pickup_code_model

    def commit(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            if self._is_pickup_code_hash_collision(exc):
                self.session.rollback()
                raise PickupCodeCollision from exc
            raise

    def rollback(self) -> None:
        self.session.rollback()

    @staticmethod
    def _is_pickup_code_hash_collision(exc: IntegrityError) -> bool:
        original = exc.orig
        constraint_name = getattr(
            getattr(original, "diag", None), "constraint_name", None
        )
        message = str(original).lower()
        return (
            constraint_name == "uq_pickup_codes_code_hash"
            or ("code_hash" in message and "unique" in message)
        )

    @staticmethod
    def _coerce_id(model: type[Any], field: str, value: str | UUID) -> Any:
        try:
            python_type = model.__table__.columns[field].type.python_type
        except (AttributeError, KeyError, NotImplementedError):
            return value
        if python_type is UUID:
            try:
                return UUID(str(value))
            except ValueError as exc:
                raise ParcelNotFound("Invalid identifier") from exc
        try:
            return python_type(value)
        except (TypeError, ValueError) as exc:
            raise ParcelNotFound("Invalid identifier") from exc

    @staticmethod
    def _value(value: Any) -> Any:
        return getattr(value, "value", value)

    @staticmethod
    def _same_id(left: Any, right: Any) -> bool:
        return str(left) == str(right)

    @staticmethod
    def _as_utc(value: datetime | None) -> datetime:
        if value is None:
            raise DepositConflict("Parcel deposit timestamps are incomplete")
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def get_assigned_compartment(
        self, parcel_id: str, locker_id: str
    ) -> AssignedCompartment:
        parcel_key = self._coerce_id(self._parcel, "parcel_id", parcel_id)
        parcel = self.session.scalar(
            select(self._parcel).where(self._parcel.parcel_id == parcel_key)
        )
        if parcel is None:
            raise ParcelNotFound("Parcel not found")
        if self._value(parcel.status) != "ASSIGNED" or parcel.compartment_id is None:
            raise DepositConflict("Parcel is not awaiting deposit")

        compartment = self.session.get(self._compartment, parcel.compartment_id)
        if compartment is None:
            raise ParcelNotFound("Assigned compartment not found")
        locker_key = self._coerce_id(self._compartment, "locker_id", locker_id)
        if not self._same_id(compartment.locker_id, locker_key):
            raise DepositConflict("Parcel is assigned to a different locker")
        if self._value(compartment.status) != "RESERVED":
            raise DepositConflict("Assigned compartment is not reserved or is in maintenance")
        locker_key_for_model = self._coerce_id(
            self._locker, "locker_id", str(compartment.locker_id)
        )
        locker = self.session.get(self._locker, locker_key_for_model)
        if locker is None:
            raise ParcelNotFound("Locker not found")
        if self._value(locker.operational_status) != "ONLINE":
            raise DepositConflict("Locker station is not online")

        return AssignedCompartment(
            parcel_id=str(parcel.parcel_id),
            locker_id=str(compartment.locker_id),
            compartment_id=str(compartment.compartment_id),
            compartment_number=int(compartment.compartment_number),
        )

    def confirm_assigned_deposit(
        self,
        *,
        parcel_id: str,
        locker_id: str,
        compartment_id: str,
        code_id: UUID,
        code_hash: str,
        deposited_at: datetime,
        pickup_deadline: datetime,
    ) -> DepositCommitResult:
        parcel_key = self._coerce_id(self._parcel, "parcel_id", parcel_id)
        compartment_key = self._coerce_id(
            self._compartment, "compartment_id", compartment_id
        )
        locker_key = self._coerce_id(self._compartment, "locker_id", locker_id)

        parcel = self.session.scalar(
            select(self._parcel)
            .where(self._parcel.parcel_id == parcel_key)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if parcel is None:
            raise ParcelNotFound("Parcel not found")

        compartment = self.locker_repository.get_compartment_for_update(compartment_key)
        if compartment is None:
            raise ParcelNotFound("Assigned compartment not found")
        if not self._same_id(compartment.locker_id, locker_key):
            raise DepositConflict("Terminal locker does not own this compartment")
        if not self._same_id(parcel.compartment_id, compartment.compartment_id):
            raise DepositConflict("Parcel is assigned to a different compartment")

        locker_key_for_model = self._coerce_id(
            self._locker, "locker_id", str(compartment.locker_id)
        )
        locker = self.session.get(self._locker, locker_key_for_model)
        if locker is None:
            raise ParcelNotFound("Locker not found")

        state = self._value(parcel.status)
        compartment_state = self._value(compartment.status)
        if state == "READY_FOR_PICKUP":
            if parcel.deposited_at is None or parcel.pickup_deadline is None:
                raise DepositConflict("Parcel deposit is incomplete")
            if compartment_state not in ("OCCUPIED", "MAINTENANCE"):
                raise DepositConflict("Parcel and compartment states do not match")
            return self._result(parcel, compartment, locker, already_processed=True)
        if state != "ASSIGNED":
            raise DepositConflict("Parcel is not assigned and awaiting deposit")

        if compartment_state == "RESERVED":
            # Match UC5's RESERVED -> OCCUPIED operation and version increment.
            if not self.locker_repository.occupy_compartment(compartment_key):
                raise DepositConflict("Compartment changed before deposit confirmation")
        elif compartment_state == "MAINTENANCE":
            # The door was already opened before maintenance was set. Sensors now
            # confirm a physical deposit, so record it but preserve MAINTENANCE.
            # UC5's occupy_compartment correctly returns False for this state.
            pass
        else:
            raise DepositConflict("Compartment is not reserved for this parcel")

        parcel.status = "READY_FOR_PICKUP"
        parcel.deposited_at = deposited_at
        parcel.pickup_deadline = pickup_deadline
        self.session.add(
            self._pickup_code(
                code_id=self._coerce_id(self._pickup_code, "code_id", code_id),
                parcel_id=parcel.parcel_id,
                code_hash=code_hash,
                failed_attempts=0,
                locked_until=None,
                issued_at=deposited_at,
                expires_at=pickup_deadline,
                used_at=None,
            )
        )
        try:
            self.session.flush()
        except IntegrityError as exc:
            if self._is_pickup_code_hash_collision(exc):
                self.session.rollback()
                raise PickupCodeCollision from exc
            raise
        return self._result(parcel, compartment, locker, already_processed=False)

    @staticmethod
    def _result(
        parcel: Any, compartment: Any, locker: Any, *, already_processed: bool
    ) -> DepositCommitResult:
        return DepositCommitResult(
            already_processed=already_processed,
            parcel_id=str(parcel.parcel_id),
            locker_id=str(compartment.locker_id),
            compartment_id=str(compartment.compartment_id),
            compartment_number=int(compartment.compartment_number),
            recipient_contact=str(parcel.recipient_contact),
            locker_address=str(locker.address),
            locker_gps_location=str(locker.gps_location),
            opening_hours=str(locker.opening_hours),
            locker_instructions=getattr(locker, "instructions", None),
            deposited_at=SQLAlchemyDepositRepository._as_utc(parcel.deposited_at),
            pickup_deadline=SQLAlchemyDepositRepository._as_utc(parcel.pickup_deadline),
        )
