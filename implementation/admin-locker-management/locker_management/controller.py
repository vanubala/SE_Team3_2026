"""AdminLockerController: HTTP only, delegates to LockerManagementService."""
from typing import Callable, Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy.orm import Session

from .models import CompartmentStatus, LockerStatus, SizeCategory
from .repository import LockerRepository
from .service import LockerManagementService, LockerOverview


class _Schema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CompartmentStatusRequest(_Schema):
    model_config = ConfigDict(extra="forbid")
    status: Literal["AVAILABLE", "MAINTENANCE"]


class LockerStatusRequest(_Schema):
    model_config = ConfigDict(extra="forbid")
    operational_status: LockerStatus


class CompartmentStatusResponse(_Schema):
    compartment_id: UUID
    status: CompartmentStatus
    warning: str | None = None


class LockerStatusResponse(_Schema):
    locker_id: UUID
    operational_status: LockerStatus
    warning: str | None = None


class OccupancyResponse(_Schema):
    total: int
    available: int
    reserved: int
    occupied: int
    maintenance: int
    occupancy_rate: float
    available_by_size: dict[SizeCategory, int]


class CompartmentResponse(_Schema):
    compartment_id: UUID
    number: int
    size: SizeCategory
    status: CompartmentStatus


class LockerResponse(_Schema):
    locker_id: UUID
    name: str
    operational_status: LockerStatus
    occupancy: OccupancyResponse
    compartments: list[CompartmentResponse]


class AdminLockerController:
    """`require_admin` and `get_session` are injected so that the shared RBAC
    middleware and database session can be plugged in at integration."""

    def __init__(self, require_admin: Callable, get_session: Callable):
        self.router = APIRouter(
            prefix="/api/admin", tags=["Admin lockers"], dependencies=[Depends(require_admin)]
        )

        def get_service(session: Session = Depends(get_session)) -> LockerManagementService:
            return LockerManagementService(LockerRepository(session))

        @self.router.get("/lockers", response_model=list[LockerResponse])
        def list_lockers(service: LockerManagementService = Depends(get_service)):
            return [_locker_response(overview) for overview in service.get_overview()]

        @self.router.patch(
            "/compartments/{compartment_id}/status",
            response_model=CompartmentStatusResponse, response_model_exclude_none=True,
        )
        def change_compartment_status(
            compartment_id: UUID, body: CompartmentStatusRequest,
            service: LockerManagementService = Depends(get_service),
        ):
            change = service.change_compartment_status(
                compartment_id, CompartmentStatus(body.status)
            )
            return CompartmentStatusResponse(
                compartment_id=change.target_id, status=change.status, warning=change.warning
            )

        @self.router.patch(
            "/lockers/{locker_id}",
            response_model=LockerStatusResponse, response_model_exclude_none=True,
        )
        def change_locker_status(
            locker_id: UUID, body: LockerStatusRequest,
            service: LockerManagementService = Depends(get_service),
        ):
            change = service.change_locker_status(locker_id, body.operational_status)
            return LockerStatusResponse(
                locker_id=change.target_id, operational_status=change.status,
                warning=change.warning,
            )


def _locker_response(overview: LockerOverview) -> LockerResponse:
    locker, occupancy = overview.locker, overview.occupancy
    return LockerResponse(
        locker_id=locker.locker_id,
        name=locker.name,
        operational_status=locker.operational_status,
        occupancy=OccupancyResponse(**vars(occupancy)),
        compartments=[
            CompartmentResponse(
                compartment_id=c.compartment_id, number=c.compartment_number,
                size=c.size_category, status=c.status,
            )
            for c in overview.compartments
        ],
    )
