"""Request and response bodies, as in Schemas-Endpoints.md sections 2.2, 2.3 and 3."""
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PlainSerializer
from pydantic.alias_generators import to_camel


def iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


# A date and time sent as UTC with a trailing Z, for example "2026-11-19T15:10:00Z".
UtcDateTime = Annotated[datetime, PlainSerializer(iso_utc, return_type=str)]


class RequestBody(BaseModel):
    # Only camelCase field names are accepted and unknown fields are rejected, so a client cannot set
    # fields such as status (mass assignment).
    model_config = ConfigDict(alias_generator=to_camel, extra="forbid")


class ResponseBody(BaseModel):
    # Filled from the database objects; sent with camelCase names.
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class RegisterParcelIn(RequestBody):
    tracking_number: str
    size_category: str
    recipient_contact: str
    expected_delivery: datetime
    preferred_locker_id: UUID | None = None
    notes: str | None = None


class RegisteredParcelOut(ResponseBody):
    parcel_id: UUID
    tracking_number: str
    status: str
    preferred_locker_id: UUID | None
    registered_at: UtcDateTime


class ParcelSummaryOut(ResponseBody):
    parcel_id: UUID
    tracking_number: str
    size_category: str
    status: str
    preferred_locker_id: UUID | None
    expected_delivery: UtcDateTime | None


class CompartmentOut(ResponseBody):
    compartment_id: UUID
    compartment_number: int
    size_category: str
    status: str


class AvailableCompartmentsOut(ResponseBody):
    locker_id: UUID
    recommended_compartment_id: UUID
    available_compartments: list[CompartmentOut]


class AssignIn(RequestBody):
    locker_id: UUID
    compartment_id: UUID


class AssignmentOut(ResponseBody):
    parcel_id: UUID
    status: str
    locker_id: UUID
    compartment_id: UUID
    compartment_number: int


class ErrorOut(BaseModel):
    """The error body of every route (Schemas-Endpoints.md section 3)."""

    timestamp: str
    status: int
    error: str
    message: str


def error_responses(*statuses: int) -> dict[int | str, dict]:
    """Documents the error body for these statuses in the OpenAPI page at /docs."""
    return {status: {"model": ErrorOut} for status in statuses}
