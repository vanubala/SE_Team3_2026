"""Route dependencies: the current courier, the unit of work and the services."""
from collections.abc import Iterator
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..database import UnitOfWork
from ..errors import NotAuthenticated, NotCourier
from ..services.assignment_service import AssignmentService
from ..services.registration_service import RegistrationService

_bearer = HTTPBearer(auto_error=False)


def current_courier(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> UUID:
    """Checks the bearer token and returns the courier's user ID (the sub claim).
    Raises NotAuthenticated for a missing or invalid token, NotCourier for another role."""
    settings = request.app.state.settings
    if credentials is None:
        raise NotAuthenticated("Valid courier authentication is required")
    try:
        claims = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            # Only HS256 is accepted. A token with another algorithm, or with "none" (no signature), is rejected.
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "role", "exp", "iss", "aud"]},
        )
        courier_id = UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise NotAuthenticated("Invalid or expired authentication token") from exc
    if claims["role"] != "COURIER":
        raise NotCourier("Courier role required")
    return courier_id


def unit_of_work(request: Request) -> Iterator[UnitOfWork]:
    session = request.app.state.sessions()
    try:
        yield UnitOfWork(session)
    finally:
        session.close()


Courier = Annotated[UUID, Depends(current_courier)]
Work = Annotated[UnitOfWork, Depends(unit_of_work)]


def registration_service(uow: Work, request: Request) -> RegistrationService:
    return RegistrationService(uow, request.app.state.settings.parcel_id_namespace)


def assignment_service(uow: Work) -> AssignmentService:
    return AssignmentService(uow)


Registration = Annotated[RegistrationService, Depends(registration_service)]
Assignment = Annotated[AssignmentService, Depends(assignment_service)]
