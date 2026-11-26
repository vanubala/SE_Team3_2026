"""REST contracts and integration ports for UC3 deposit handling."""
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class DepositUnlockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    locker_id: str = Field(alias="lockerId", min_length=1, max_length=100)
    parcel_id: str = Field(alias="parcelId", min_length=1, max_length=100)


class DepositUnlockResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    parcel_id: str = Field(alias="parcelId")
    compartment_id: str = Field(alias="compartmentId")
    compartment_number: int = Field(alias="compartmentNumber")
    door_command: Literal["UNLOCK"] = Field(default="UNLOCK", alias="doorCommand")


class DepositConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)
    parcel_id: str = Field(alias="parcelId", min_length=1, max_length=100)
    compartment_id: str = Field(alias="compartmentId", min_length=1, max_length=100)
    door_closed: StrictBool = Field(alias="doorClosed")
    parcel_detected: StrictBool = Field(alias="parcelDetected")


class DepositConfirmationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    parcel_id: str = Field(alias="parcelId")
    status: Literal["READY_FOR_PICKUP"]
    pickup_deadline: datetime = Field(alias="pickupDeadline")
    notification_triggered: bool = Field(alias="notificationTriggered")


@dataclass(frozen=True)
class TerminalContext:
    """Identity supplied by the kiosk-auth dependency during app integration."""
    locker_id: str


@dataclass(frozen=True)
class AssignedCompartment:
    parcel_id: str
    locker_id: str
    compartment_id: str
    compartment_number: int


@dataclass(frozen=True)
class DepositCommitResult:
    already_processed: bool
    parcel_id: str
    locker_id: str
    compartment_id: str
    compartment_number: int
    recipient_contact: str
    locker_address: str
    locker_gps_location: str
    opening_hours: str
    locker_instructions: str | None
    deposited_at: datetime
    pickup_deadline: datetime


@dataclass(frozen=True)
class ParcelDeposited:
    """Transient post-commit event; plaintext PIN must never be persisted or logged."""
    event_id: UUID
    parcel_id: str
    recipient_contact: str
    pickup_code: str
    locker_address: str
    locker_gps_location: str
    opening_hours: str
    locker_instructions: str | None
    compartment_number: int
    pickup_deadline: datetime


@dataclass(frozen=True)
class DepositConfirmationOutcome:
    response: DepositConfirmationResponse
    event: ParcelDeposited | None


@dataclass(frozen=True)
class IssuedPickupCode:
    code_id: UUID
    plaintext: str
    code_hash: str


class DepositRepository(Protocol):
    def commit(self) -> None:
        """Commit the unit of work after a successful deposit."""

    def rollback(self) -> None:
        """Roll back the unit of work after a failed deposit."""

    def get_assigned_compartment(
        self, parcel_id: str, locker_id: str
    ) -> AssignedCompartment:
        """Find a parcel in ASSIGNED state at this locker."""

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
        """Atomically update parcel, compartment and hashed pickup-code records."""


class CompartmentDoorGateway(Protocol):
    def unlock_compartment(self, *, locker_id: str, compartment_id: str) -> None:
        """Send the assigned compartment's physical unlock command."""


class PickupNotificationGateway(Protocol):
    async def send_pickup_notification(
        self, *, destination: str, message: str, idempotency_key: str
    ) -> None:
        """Adapter around the team's SMS/email provider."""
