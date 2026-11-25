"""Routes for UC1: register a parcel and list the courier's parcels."""
from fastapi import APIRouter

from ..services.registration_service import ParcelForm
from .dependencies import Courier, Registration
from .schemas import ParcelSummaryOut, RegisteredParcelOut, RegisterParcelIn, error_responses

router = APIRouter(prefix="/api/parcels", tags=["Registration"])


@router.post("", status_code=201, responses=error_responses(400, 401, 403, 409, 500))
def register_parcel(body: RegisterParcelIn, courier_id: Courier, service: Registration) -> RegisteredParcelOut:
    parcel = service.register_parcel(courier_id, ParcelForm(**body.model_dump()))
    return RegisteredParcelOut.model_validate(parcel)


@router.get("", responses=error_responses(400, 401, 403))
def list_parcels(courier_id: Courier, service: Registration, status: str | None = None) -> list[ParcelSummaryOut]:
    return [ParcelSummaryOut.model_validate(parcel) for parcel in service.list_parcels(courier_id, status)]
