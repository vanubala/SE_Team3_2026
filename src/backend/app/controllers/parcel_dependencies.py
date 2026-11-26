"""Route dependencies of parcel registration and assignment: the courier, the unit of work and the services."""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.unit_of_work import UnitOfWork
from app.security.dependencies import require_courier
from app.security.tokens import Principal
from app.services.assignment_service import AssignmentService
from app.services.registration_service import RegistrationService


def current_courier(principal: Annotated[Principal, Depends(require_courier)]) -> UUID:
    """Returns the user ID of the logged-in courier. require_courier answers 401 or 403 otherwise."""
    return principal.user_id


def unit_of_work(db: Annotated[Session, Depends(get_db)]) -> UnitOfWork:
    return UnitOfWork(db)


Courier = Annotated[UUID, Depends(current_courier)]
Work = Annotated[UnitOfWork, Depends(unit_of_work)]


def registration_service(uow: Work, request: Request) -> RegistrationService:
    return RegistrationService(uow, request.app.state.parcel_id_namespace)


def assignment_service(uow: Work) -> AssignmentService:
    return AssignmentService(uow)


Registration = Annotated[RegistrationService, Depends(registration_service)]
Assignment = Annotated[AssignmentService, Depends(assignment_service)]
