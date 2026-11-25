"""Routes for UC2: available compartments and assignment."""
from uuid import UUID

from fastapi import APIRouter, Depends

from .dependencies import Assignment, Courier, current_courier
from .schemas import AssignIn, AssignmentOut, AvailableCompartmentsOut, CompartmentOut, error_responses

router = APIRouter(prefix="/api", tags=["Assignment"], dependencies=[Depends(current_courier)])


@router.get("/lockers/{locker_id}/compartments", responses=error_responses(400, 401, 403, 404, 409))
def get_available_compartments(locker_id: UUID, size: str, service: Assignment) -> AvailableCompartmentsOut:
    recommended, compartments = service.get_available_and_recommended_compartments(locker_id, size)
    return AvailableCompartmentsOut(
        locker_id=locker_id,
        recommended_compartment_id=recommended.compartment_id,
        available_compartments=[CompartmentOut.model_validate(c) for c in compartments],
    )


@router.post("/parcels/{parcel_id}/assign", responses=error_responses(400, 401, 403, 404, 409))
def assign_compartment(parcel_id: UUID, body: AssignIn, courier_id: Courier, service: Assignment) -> AssignmentOut:
    parcel, compartment = service.assign_compartment(courier_id, parcel_id, body.locker_id, body.compartment_id)
    return AssignmentOut(
        parcel_id=parcel.parcel_id,
        status=parcel.status,
        locker_id=compartment.locker_id,
        compartment_id=compartment.compartment_id,
        compartment_number=compartment.compartment_number,
    )
