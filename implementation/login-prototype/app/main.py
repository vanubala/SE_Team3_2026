"""Assembles the application: storage, seeded accounts, API and pages."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import build_router
from .config import Settings
from .repository import UserRepository
from .seed import seed_staff_accounts
from .services import AuthError, AuthService

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def create_app(settings: Settings, clock: Callable[[], datetime] | None = None) -> FastAPI:
    clock = clock or (lambda: datetime.now(timezone.utc))
    repository = UserRepository(settings.database_path)
    service = AuthService(repository, settings, clock=clock)
    staff_credentials = seed_staff_accounts(repository, settings.staff_password, clock())

    app = FastAPI(title="Smart Parcel Locker - Shared Sign-in Prototype", version="0.1.0")
    app.state.service = service
    app.state.staff_credentials = staff_credentials

    @app.exception_handler(AuthError)
    def auth_error(_: Request, exc: AuthError):
        headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
        return JSONResponse(status_code=exc.status, content={"detail": exc.message}, headers=headers)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if not (path.startswith("/docs") or path == "/openapi.json"):
            response.headers.update(SECURITY_HEADERS)
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    app.include_router(build_router(service, settings))
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def sign_in_page():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/register", include_in_schema=False)
    def register_page():
        return FileResponse(STATIC_DIR / "register.html")

    @app.get("/dashboard", include_in_schema=False)
    def dashboard_page():
        return FileResponse(STATIC_DIR / "dashboard.html")

    @app.get("/health", include_in_schema=False)
    def health():
        return {"status": "ok"}

    return app
