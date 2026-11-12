from datetime import datetime, timedelta, timezone
from pathlib import Path
import jwt
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.factory import create_app

@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        jwt_secret="jwt-test-secret-only-this-is-very-long-123",
        parcel_id_secret="id-test-secret-only-this-is-very-long-456",
        database_path=str(tmp_path / "parcels.sqlite3"),
        demo_mode=False,
        pickup_window_hours=72,
    )

@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as test_client:
        yield test_client

def make_token(settings, role="COURIER", subject="courier-alice", ttl_seconds=3600, **overrides):
    now = datetime.now(timezone.utc)
    claims = {"sub": subject, "role": role, "iss": settings.jwt_issuer,
              "aud": settings.jwt_audience, "iat": now,
              "exp": now + timedelta(seconds=ttl_seconds)}
    claims.update(overrides)
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")

@pytest.fixture
def auth(settings):
    def create(role="COURIER", subject="courier-alice", ttl_seconds=3600):
        return {"Authorization": "Bearer " + make_token(settings, role, subject, ttl_seconds)}
    return create

@pytest.fixture
def request_payload():
    return {"barcode": "EXT-2026-0001", "size": "MEDIUM",
            "expectedDeliveryAt": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "notes": "Fragile - handle with care"}
