import uuid

import pytest

from app.config import from_env

NAMESPACE = "6f1c2d4e-9a7b-4c3d-8e2f-1a2b3c4d5e6f"


@pytest.fixture
def env(monkeypatch):
    for name in ("JWT_SECRET", "PARCEL_ID_NAMESPACE", "DATABASE_URL", "JWT_ISSUER", "JWT_AUDIENCE"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_reads_the_settings_from_the_environment(env):
    env.setenv("JWT_SECRET", "s" * 32)
    env.setenv("PARCEL_ID_NAMESPACE", NAMESPACE)
    env.setenv("DATABASE_URL", "sqlite://")

    settings = from_env()

    assert settings.parcel_id_namespace == uuid.UUID(NAMESPACE)
    assert settings.database_url == "sqlite://"
    assert (settings.jwt_issuer, settings.jwt_audience) == ("smart-locker-auth", "smart-locker-api")


@pytest.mark.parametrize("secret, namespace", [
    pytest.param(None, NAMESPACE, id="no-secret"),
    pytest.param("s" * 31, NAMESPACE, id="secret-31-bytes"),
    pytest.param("s" * 32, None, id="no-namespace"),
    pytest.param("s" * 32, "not-a-uuid", id="namespace-not-a-uuid"),
])
def test_refuses_to_start_without_proper_secrets(env, secret, namespace):
    if secret is not None:
        env.setenv("JWT_SECRET", secret)
    if namespace is not None:
        env.setenv("PARCEL_ID_NAMESPACE", namespace)

    with pytest.raises(RuntimeError):
        from_env()
