"""Routes for UC1: register a parcel and list the courier's parcels."""
from fastapi import APIRouter

from app.controllers.parcel_dependencies import Courier, Registration
from app.schemas.parcels import ParcelSummaryOut, RegisteredParcelOut, RegisterParcelIn, error_responses
from app.services.registration_service import ParcelForm

router = APIRouter(prefix="/api/parcels", tags=["Registration"])


@router.post("", status_code=201, responses=error_responses(400, 401, 403, 409, 503))
def register_parcel(body: RegisterParcelIn, courier_id: Courier, service: Registration) -> RegisteredParcelOut:
    parcel = service.register_parcel(courier_id, ParcelForm(**body.model_dump()))
    return RegisteredParcelOut.model_validate(parcel)


@router.get("", responses=error_responses(400, 401, 403))
def list_parcels(courier_id: Courier, service: Registration, status: str | None = None) -> list[ParcelSummaryOut]:
    return [ParcelSummaryOut.model_validate(parcel) for parcel in service.list_parcels(courier_id, status)]
