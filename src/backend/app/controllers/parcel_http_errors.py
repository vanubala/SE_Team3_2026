"""Maps the errors of parcel registration and assignment to the shared error body (app/errors.py)."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import envelope
from app.services import parcel_errors as errors

STATUS_CODES = {
    errors.InvalidParcelData: 400,
    errors.ParcelNotFound: 404,
    errors.LockerNotFound: 404,
    errors.CompartmentNotFound: 404,
    errors.DuplicateTrackingNumber: 409,
    errors.ParcelNotRegistered: 409,
    errors.LockerUnavailable: 409,
    errors.NoCompartmentAvailable: 409,
    errors.CompartmentTooSmall: 409,
    errors.CompartmentTaken: 409,
}


async def parcel_error_handler(request: Request, exc: errors.ParcelError) -> JSONResponse:
    status = STATUS_CODES[type(exc)]
    return JSONResponse(envelope(status, exc.message), status_code=status)


def register_parcel_error_handler(app: FastAPI) -> None:
    app.add_exception_handler(errors.ParcelError, parcel_error_handler)
