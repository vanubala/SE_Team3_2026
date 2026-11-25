"""Converts errors to HTTP responses with the error body of Schemas-Endpoints.md section 3."""
import logging
from collections.abc import Mapping
from datetime import UTC, datetime
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .. import errors
from .schemas import iso_utc

logger = logging.getLogger(__name__)

STATUS_CODES = {
    errors.InvalidParcelData: 400,
    errors.NotAuthenticated: 401,
    errors.NotCourier: 403,
    errors.ParcelNotFound: 404,
    errors.LockerNotFound: 404,
    errors.CompartmentNotFound: 404,
    errors.DuplicateTrackingNumber: 409,
    errors.ParcelNotRegistered: 409,
    errors.LockerUnavailable: 409,
    errors.NoCompartmentAvailable: 409,
    errors.CompartmentTooSmall: 409,
    errors.CompartmentTaken: 409,
    errors.StorageError: 500,
}


def error_response(status: int, message: str, headers: Mapping[str, str] | None = None) -> JSONResponse:
    body = {
        "timestamp": iso_utc(datetime.now(UTC)),
        "status": status,
        "error": HTTPStatus(status).name,
        "message": message,
    }
    if status == 401:
        headers = {**(headers or {}), "WWW-Authenticate": "Bearer"}
    return JSONResponse(status_code=status, content=body, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(errors.ModuleError)
    def module_error(request: Request, exc: errors.ModuleError) -> JSONResponse:
        status = STATUS_CODES[type(exc)]
        if status == 500:
            logger.error("%s %s failed", request.method, request.url.path, exc_info=exc)
        return error_response(status, exc.message)

    @app.exception_handler(RequestValidationError)
    def invalid_request(request: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0]
        # loc is e.g. ("body", "trackingNumber"). Numbers in loc (the position of a JSON syntax error) are left out.
        field = ".".join(part for part in first["loc"][1:] if isinstance(part, str)) or "request"
        return error_response(400, f"{field}: {first['msg']}")

    @app.exception_handler(StarletteHTTPException)
    def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Errors from FastAPI itself, e.g. unknown route (404) or wrong method (405).
        message = exc.detail if isinstance(exc.detail, str) else HTTPStatus(exc.status_code).phrase
        return error_response(exc.status_code, message, exc.headers)

    @app.exception_handler(Exception)
    def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Any other error: the client gets a plain 500, the server logs the details.
        return error_response(500, "Internal server error")
