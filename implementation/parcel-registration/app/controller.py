"""HTTP controller for the register/list parcel operations."""
from fastapi import APIRouter, Depends, HTTPException, status
from .auth import require_courier
from .config import Settings
from .models import ParcelRegistrationRequest, RegistrationSuccess, ParcelResponse
from .service import RegistrationService


def make_registration_router(service: RegistrationService, settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/api/parcels", tags=["Courier parcels"])
    courier_dependency = require_courier(settings)

    @router.post("", response_model=RegistrationSuccess, status_code=status.HTTP_201_CREATED)
    def register_parcel(payload: ParcelRegistrationRequest, courier_id: str = Depends(courier_dependency)):
        parcel = service.register(payload, courier_id)
        return {
            "status": "SUCCESS",
            "parcelId": parcel["parcel_id"],
            "parcel": _public_response(parcel),
        }

    @router.get("", response_model=list[ParcelResponse])
    def list_parcels(courier_id: str = Depends(courier_dependency)):
        return [_public_response(p) for p in service.list_parcels(courier_id)]

    return router


def _public_response(parcel: dict) -> dict:
    return {
        "parcelId": parcel["parcel_id"],
        "trackingNumber": parcel["tracking_number"],
        "size": parcel["size"],
        "expectedDeliveryAt": parcel["expected_delivery_at"],
        "notes": parcel["notes"],
        "status": parcel["status"],
        "pickupDeadline": parcel["pickup_deadline"],
        "createdAt": parcel["created_at"],
    }
