"""Builds the web application for parcel registration and compartment assignment."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from .config import Settings, from_env
from .controllers.assignment_controller import router as assignment_router
from .controllers.http_errors import register_error_handlers
from .controllers.registration_controller import router as registration_router
from .database import make_engine
from .models import Base


def create_app(settings: Settings | None = None, engine: Engine | None = None) -> FastAPI:
    """Creates the app. Tests pass settings and engine; otherwise they come from the environment."""
    settings = settings or from_env()
    owns_engine = engine is None
    engine = engine or make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if engine.dialect.name == "sqlite":
            # SQLite only (local runs and tests). On PostgreSQL the tables must already exist.
            Base.metadata.create_all(engine)
        yield
        if owns_engine:
            engine.dispose()  # close the database connections on shutdown

    app = FastAPI(title="Smart Parcel Locker: registration and assignment", lifespan=lifespan)
    app.state.settings = settings
    app.state.sessions = sessionmaker(engine, expire_on_commit=False)
    register_error_handlers(app)
    app.include_router(registration_router)
    app.include_router(assignment_router)
    return app
