"""Business rules for registration; no HTTP dependencies."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from fastapi import HTTPException
from .config import Settings
from .models import ParcelRegistrationRequest
from .repository import DuplicateTrackingNumber, ParcelRepository


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class RegistrationService:
    def __init__(self, repository: ParcelRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    def register(self, request: ParcelRegistrationRequest, courier_id: str) -> dict:
        if self.repository.exists_tracking_number(request.barcode):
            raise HTTPException(status_code=409, detail="A parcel with this barcode is already registered")

        # HMAC preserves the design's hash-derived ID while preventing public guessing.
        # Unique tracking numbers map to unique identifiers with negligible collision risk.
        parcel_id = hmac.new(
            self.settings.parcel_id_secret.encode("utf-8"),
            request.barcode.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        now = datetime.now(timezone.utc)
        # Working assumption from Modular-Design.md; review business rule with team.
        pickup_deadline = request.expected_delivery_at + timedelta(hours=self.settings.pickup_window_hours)
        parcel = {
            "parcel_id": parcel_id,
            "tracking_number": request.barcode,
            "courier_id": courier_id,
            "size": request.size.value,
            "expected_delivery_at": iso_utc(request.expected_delivery_at),
            "notes": request.notes,
            "status": "REGISTERED",
            "pickup_deadline": iso_utc(pickup_deadline),
            "created_at": iso_utc(now),
        }
        try:
            return self.repository.save(parcel)
        except DuplicateTrackingNumber as exc:
            raise HTTPException(status_code=409, detail="A parcel with this barcode is already registered") from exc

    def list_parcels(self, courier_id: str) -> list[dict]:
        return self.repository.list_for_courier(courier_id)
