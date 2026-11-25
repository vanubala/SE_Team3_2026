"""Standalone assembly for development and tests."""
from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from .auth import make_require_admin
from .controller import AdminLockerController
from .errors import register_error_handlers


def create_app(engine: Engine, jwt_secret: str) -> FastAPI:
    def get_session():
        with Session(engine) as session:
            yield session

    app = FastAPI(title="Smart Parcel Locker - Admin Lockers")
    register_error_handlers(app)
    app.include_router(AdminLockerController(make_require_admin(jwt_secret), get_session).router)
    return app
