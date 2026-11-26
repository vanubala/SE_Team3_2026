"""Guest pickup at the locker terminal (UC4, Schemas-Endpoints §2.5)."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.errors import envelope
from app.repositories.pickup_repository import PickupRepository
from app.schemas.pickup import (PickupConfirmRequest, PickupConfirmResponse,
                                PickupVerifyRequest, PickupVerifyResponse)
from app.services.pickup_service import (CollectionConflict, InvalidPickupCode, LockerNotFound,
                                         ParcelNotFound, PickupService, PickupSessionRejected,
                                         TerminalLocked)

router = APIRouter(prefix='/api/terminal/pickup', tags=['Guest pickup'])

NO_STORE = {'Cache-Control': 'no-store'}


def get_pickup_service(request: Request, db: Session = Depends(get_db)) -> PickupService:
    return PickupService(PickupRepository(db), request.app.state.pickup_codes,
                         request.app.state.pickup_sessions)


def _error(status: int, message: str, headers: dict | None = None, **extra) -> JSONResponse:
    return JSONResponse(envelope(status, message) | extra, status_code=status,
                        headers=NO_STORE | (headers or {}))


@router.post('/verify', response_model=PickupVerifyResponse,
             responses={400: {'description': 'Invalid request'}, 401: {'description': 'Invalid or expired pickup code'},
                        404: {'description': 'Unknown locker'}, 423: {'description': 'Terminal locked'}})
def verify(payload: PickupVerifyRequest, response: Response,
           service: PickupService = Depends(get_pickup_service)):
    try:
        result = service.verify_and_unlock(payload.lockerId, payload.pickupCode)
    except LockerNotFound:
        return _error(404, 'Locker not found')
    except TerminalLocked as exc:
        return _error(423, 'Terminal locked after 5 failed attempts. Try again later.',
                      {'Retry-After': str(exc.retry_after_seconds)},
                      retryAfterSeconds=exc.retry_after_seconds)
    except InvalidPickupCode as exc:
        return _error(401, 'Invalid or expired pickup code', remainingAttempts=exc.remaining_attempts)
    response.headers.update(NO_STORE)
    return PickupVerifyResponse(parcelId=result.parcel_id, compartmentId=result.compartment_id,
                                compartmentNumber=result.compartment_number,
                                pickupSessionToken=result.session_token)


@router.post('/confirm', response_model=PickupConfirmResponse,
             responses={400: {'description': 'Invalid request'}, 401: {'description': 'Invalid pickup session'},
                        404: {'description': 'Unknown parcel'}, 409: {'description': 'Collection not possible'}})
def confirm(payload: PickupConfirmRequest, response: Response,
            service: PickupService = Depends(get_pickup_service)):
    try:
        result = service.confirm_collection(payload.parcelId, payload.compartmentId,
                                            payload.pickupSessionToken, payload.doorClosed,
                                            payload.parcelDetected)
    except PickupSessionRejected as exc:
        raise HTTPException(401, 'Invalid or expired pickup session', headers=NO_STORE) from exc
    except ParcelNotFound as exc:
        raise HTTPException(404, 'Parcel not found', headers=NO_STORE) from exc
    except CollectionConflict as exc:
        raise HTTPException(409, str(exc), headers=NO_STORE) from exc
    response.headers.update(NO_STORE)
    return PickupConfirmResponse(parcelId=result.parcel_id, status=result.status,
                                 compartmentStatus=result.compartment_status)
