"""HTTP controller for UC3 physical terminal deposit endpoints."""
from collections.abc import Callable

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from .contracts import (
    DepositConfirmationRequest,
    DepositConfirmationResponse,
    DepositUnlockRequest,
    DepositUnlockResponse,
    TerminalContext,
)
from .notifications import NotificationService
from .service import (
    DepositConflict,
    DepositForbidden,
    DepositHardwareUnavailable,
    DepositService,
    ParcelNotFound,
    PickupCodeUnavailable,
)


class DepositController:
    """Build the UC3 router using shared app dependencies supplied at integration."""

    def __init__(
        self,
        get_deposit_service: Callable[..., DepositService],
        require_locker_terminal: Callable[..., TerminalContext],
        get_notification_service: Callable[..., NotificationService],
    ) -> None:
        self.router = APIRouter(
            prefix="/api/terminal/deposit", tags=["UC3 parcel deposit"]
        )

        @self.router.post(
            "/unlock",
            response_model=DepositUnlockResponse,
            status_code=status.HTTP_200_OK,
        )
        def request_unlock(
            payload: DepositUnlockRequest,
            deposit_service: DepositService = Depends(get_deposit_service),
            terminal: TerminalContext = Depends(require_locker_terminal),
        ) -> DepositUnlockResponse:
            try:
                return deposit_service.request_unlock(payload, terminal)
            except ParcelNotFound as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except DepositConflict as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            except DepositForbidden as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
            except DepositHardwareUnavailable as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc

        @self.router.post(
            "/confirm",
            response_model=DepositConfirmationResponse,
            status_code=status.HTTP_200_OK,
        )
        def confirm_deposit(
            payload: DepositConfirmationRequest,
            background_tasks: BackgroundTasks,
            deposit_service: DepositService = Depends(get_deposit_service),
            notification_service: NotificationService = Depends(
                get_notification_service
            ),
            terminal: TerminalContext = Depends(require_locker_terminal),
        ) -> DepositConfirmationResponse:
            try:
                outcome = deposit_service.confirm_deposit(payload, terminal)
            except ParcelNotFound as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except DepositConflict as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            except DepositForbidden as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
            except PickupCodeUnavailable as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc

            if outcome.event is not None:
                background_tasks.add_task(
                    notification_service.handle_parcel_deposited, outcome.event
                )
            return outcome.response
