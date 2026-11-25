from datetime import datetime, timezone
from http import HTTPStatus
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


def envelope(status: int, message: str) -> dict:
    try:
        error = HTTPStatus(status).name
    except ValueError:
        error = 'ERROR'
    return {'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
            'status': status, 'error': error, 'message': message}


def register_error_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse(envelope(exc.status_code, exc.detail if isinstance(exc.detail,str) else 'Request failed'),
                            status_code=exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        # Never echo the rejected body: it can contain credentials.
        return JSONResponse(envelope(400, 'Invalid request'), status_code=400)

    @app.exception_handler(SQLAlchemyError)
    async def storage_error(request: Request, exc: SQLAlchemyError):
        # Do not log SQL parameters or expose database details.
        logger.error('Database operation failed (%s)', type(exc).__name__)
        return JSONResponse(envelope(503, 'Database unavailable'), status_code=503)
