from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

STAFF_PASSWORD = "Test-Staff-Password-1"


class Clock:
    """Controllable time, so expiry and lockout can be tested without waiting."""

    def __init__(self):
        self.now = datetime.now(timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **delta) -> None:
        self.now += timedelta(**delta)


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def settings(tmp_path):
    return Settings(database_path=str(tmp_path / "accounts.sqlite3"), staff_password=STAFF_PASSWORD)


@pytest.fixture
def client(settings, clock):
    with TestClient(create_app(settings, clock=clock)) as test_client:
        yield test_client


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def staff_login(client, login_id, password=STAFF_PASSWORD):
    return client.post("/api/auth/login", json={"identifier": login_id, "password": password})


def register(client, identifier, name="Ana Silva"):
    """Complete the registration flow and return the sign-in result."""
    started = client.post("/api/auth/register", json={"name": name, "identifier": identifier})
    assert started.status_code == 200, started.text
    verified = client.post("/api/auth/register/verify",
                           json={"identifier": identifier, "code": started.json()["devCode"]})
    assert verified.status_code == 201, verified.text
    return verified.json()


def wrong(code: str) -> str:
    return f"{(int(code) + 1) % 10**6:06d}"
