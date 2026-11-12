"""App assembly: FastAPI + SQLite repository + controller + static dashboard."""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .auth import issue_demo_token
from .config import Settings, from_env
from .controller import make_registration_router
from .repository import ParcelRepository
from .service import RegistrationService

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or from_env()
    repository = ParcelRepository(settings.database_path)
    service = RegistrationService(repository, settings)
    app = FastAPI(title="Smart Parcel Locker - Courier Registration", version="0.1.0")
    app.include_router(make_registration_router(service, settings))
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/api/config")
    def get_config():
        return {"demoMode": settings.demo_mode, "pickupWindowHours": settings.pickup_window_hours}

    @app.get("/api/demo-session")
    def demo_session(request: Request):
        # Strictly local-only educational endpoint; never enable in production.
        if not settings.demo_mode or (request.client and request.client.host not in {"127.0.0.1", "::1", "testclient"}):
            raise HTTPException(status_code=404, detail="Not found")
        return {"token": issue_demo_token(settings)}

    @app.get("/")
    def dashboard():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
