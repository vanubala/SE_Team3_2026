"""Standard HTTP error envelope for the standalone UC3 demo app."""
from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


def _envelope(status_code: int, message: str, headers=None) -> JSONResponse:
    timestamp = (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )
    return JSONResponse(
        status_code=status_code,
        headers=headers,
        content={
            "timestamp": timestamp,
            "status": status_code,
            "error": HTTPStatus(status_code).name,
            "message": message,
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    def http_error(_, exc: HTTPException) -> JSONResponse:
        return _envelope(exc.status_code, str(exc.detail), exc.headers)

    @app.exception_handler(RequestValidationError)
    def validation_error(_, exc: RequestValidationError) -> JSONResponse:
        message = "; ".join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors()
        )
        return _envelope(400, message)
