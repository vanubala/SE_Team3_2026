"""UC3 business rules, independent of FastAPI and SQLAlchemy."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from .contracts import (
    DepositConfirmationOutcome,
    DepositConfirmationRequest,
    DepositConfirmationResponse,
    DepositRepository,
    DepositUnlockRequest,
    DepositUnlockResponse,
    CompartmentDoorGateway,
    ParcelDeposited,
    TerminalContext,
)
from .security import PickupCodeIssuer


class ParcelNotFound(Exception):
    """The parcel, locker, or assigned compartment does not exist."""


class DepositConflict(Exception):
    """The parcel is not assigned here or the sensor report is incomplete."""


class DepositForbidden(Exception):
    """The kiosk identity does not match the requested locker."""


class DepositHardwareUnavailable(Exception):
    """The assigned compartment could not be opened."""


class PickupCodeCollision(Exception):
    """A generated PIN hash already exists in the database."""


class PickupCodeUnavailable(Exception):
    """A unique pickup PIN could not be reserved after several attempts."""


class DepositService:
    def __init__(
        self,
        repository: DepositRepository,
        code_issuer: PickupCodeIssuer,
        door_gateway: CompartmentDoorGateway,
    ) -> None:
        self._repository = repository
        self._code_issuer = code_issuer
        self._door_gateway = door_gateway

    def request_unlock(
        self, request: DepositUnlockRequest, terminal: TerminalContext
    ) -> DepositUnlockResponse:
        if request.locker_id != terminal.locker_id:
            raise DepositForbidden("This terminal cannot operate the requested locker")
        assigned = self._repository.get_assigned_compartment(request.parcel_id, terminal.locker_id)
        try:
            self._door_gateway.unlock_compartment(
                locker_id=assigned.locker_id,
                compartment_id=assigned.compartment_id,
            )
        except Exception as exc:
            raise DepositHardwareUnavailable(
                "The assigned compartment could not be unlocked"
            ) from exc
        return DepositUnlockResponse(
            parcelId=assigned.parcel_id,
            compartmentId=assigned.compartment_id,
            compartmentNumber=assigned.compartment_number,
            doorCommand="UNLOCK",
        )

    def confirm_deposit(
        self, request: DepositConfirmationRequest, terminal: TerminalContext
    ) -> DepositConfirmationOutcome:
        if not request.door_closed:
            raise DepositConflict("The compartment door must be closed")
        if not request.parcel_detected:
            raise DepositConflict("The kiosk did not detect a parcel in the compartment")

        deposited_at = datetime.now(timezone.utc)
        pickup_deadline = deposited_at + timedelta(days=7)
        committed = None
        issued_code = None
        for _ in range(5):
            candidate = self._code_issuer.issue()
            try:
                committed = self._repository.confirm_assigned_deposit(
                    parcel_id=request.parcel_id,
                    locker_id=terminal.locker_id,
                    compartment_id=request.compartment_id,
                    code_id=candidate.code_id,
                    code_hash=candidate.code_hash,
                    deposited_at=deposited_at,
                    pickup_deadline=pickup_deadline,
                )
                self._repository.commit()
            except PickupCodeCollision:
                self._repository.rollback()
                continue
            except Exception:
                self._repository.rollback()
                raise
            issued_code = candidate
            break

        if committed is None or issued_code is None:
            raise PickupCodeUnavailable("Could not reserve a unique pickup PIN")

        event = None
        if not committed.already_processed:
            event = ParcelDeposited(
                event_id=uuid4(),
                parcel_id=committed.parcel_id,
                recipient_contact=committed.recipient_contact,
                pickup_code=issued_code.plaintext,
                locker_address=committed.locker_address,
                locker_gps_location=committed.locker_gps_location,
                opening_hours=committed.opening_hours,
                locker_instructions=committed.locker_instructions,
                compartment_number=committed.compartment_number,
                pickup_deadline=committed.pickup_deadline,
            )

        response = DepositConfirmationResponse(
            parcelId=committed.parcel_id,
            status="READY_FOR_PICKUP",
            pickupDeadline=committed.pickup_deadline,
            notificationTriggered=event is not None,
        )
        return DepositConfirmationOutcome(response=response, event=event)
