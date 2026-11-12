"""DTOs and domain model for courier parcel registration."""
from datetime import datetime, timezone
from enum import Enum
import re
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParcelSize(str, Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class ParcelRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    barcode: str = Field(min_length=3, max_length=64)
    size: ParcelSize
    expected_delivery_at: datetime = Field(alias="expectedDeliveryAt")
    notes: str = Field(default="", max_length=500)

    @field_validator("barcode")
    @classmethod
    def valid_barcode(cls, barcode: str) -> str:
        barcode = barcode.strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{2,63}", barcode):
            raise ValueError("Barcode must be 3–64 characters (letters, digits, _ or -)")
        return barcode

    @field_validator("expected_delivery_at")
    @classmethod
    def delivery_in_future(cls, when: datetime) -> datetime:
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError("Expected delivery must include a time-zone offset")
        when = when.astimezone(timezone.utc)
        if when <= datetime.now(timezone.utc):
            raise ValueError("Expected delivery must be in the future")
        return when

    @field_validator("notes")
    @classmethod
    def sanitize_notes(cls, notes: str) -> str:
        # Remove disallowed control characters without rewriting legitimate instructions.
        cleaned = "".join(ch for ch in notes if ch in "\t\n" or ord(ch) >= 32)
        return cleaned.strip()


class ParcelResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    parcel_id: str = Field(alias="parcelId")
    tracking_number: str = Field(alias="trackingNumber")
    size: ParcelSize
    expected_delivery_at: datetime = Field(alias="expectedDeliveryAt")
    notes: str
    status: str
    pickup_deadline: datetime = Field(alias="pickupDeadline")
    created_at: datetime = Field(alias="createdAt")


class RegistrationSuccess(BaseModel):
    status: str = "SUCCESS"
    parcel_id: str = Field(alias="parcelId")
    parcel: ParcelResponse
