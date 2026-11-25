"""Standard error envelope (Schemas-Endpoints.md section 3)."""
from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from .service import (
    ConflictError, InvalidStatusError, LockerManagementError, NotFoundError, StorageError,
)

_STATUS = {
    NotFoundError: 404,
    ConflictError: 409,
    InvalidStatusError: 400,
    StorageError: 503,
}


def _envelope(status: int, message: str, headers=None) -> JSONResponse:
    return JSONResponse(status_code=status, headers=headers, content={
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "status": status,
        "error": HTTPStatus(status).name,
        "message": message,
    })


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(LockerManagementError)
    def domain_error(_, exc: LockerManagementError):
        return _envelope(_STATUS.get(type(exc), 500), str(exc))

    @app.exception_handler(HTTPException)
    def http_error(_, exc: HTTPException):
        return _envelope(exc.status_code, str(exc.detail), exc.headers)

    @app.exception_handler(RequestValidationError)
    def validation_error(_, exc: RequestValidationError):
        message = "; ".join(
            f"{'.'.join(str(part) for part in e['loc'])}: {e['msg']}" for e in exc.errors()
        )
        return _envelope(400, message)
