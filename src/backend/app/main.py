from contextlib import asynccontextmanager
from secrets import token_urlsafe
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from app.config import Settings, get_settings
from app.controllers.auth_controller import router as auth_router
from app.controllers.pickup_controller import router as pickup_router
from app.db.session import make_engine
from app.errors import register_error_handlers
from app.security.passwords import hash_password
from app.security.pickup_codes import PickupCodeHasher, PickupSessionTokens
from app.security.tokens import TokenService


def create_app(settings: Settings | None = None, *, engine: Engine | None = None) -> FastAPI:
    settings = settings or get_settings()
    owns_engine = engine is None
    engine = engine if engine is not None else make_engine(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if owns_engine:
            engine.dispose()

    app = FastAPI(title='Smart Parcel Locker MVP', lifespan=lifespan)
    app.state.session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.state.tokens = TokenService(settings)
    app.state.dummy_hash = hash_password(token_urlsafe(32))
    app.state.pickup_codes = PickupCodeHasher(settings)
    app.state.pickup_sessions = PickupSessionTokens(settings)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=['GET','POST','PATCH','DELETE','OPTIONS'],
                       allow_headers=['Authorization','Content-Type'], allow_credentials=False)
    register_error_handlers(app)
    app.include_router(auth_router)
    app.include_router(pickup_router)
    # Integration lead registers the remaining APIRouters here.
    return app
