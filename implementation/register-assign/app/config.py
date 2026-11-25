"""Settings read from the environment."""
import os
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str
    parcel_id_namespace: uuid.UUID
    jwt_issuer: str = "smart-locker-auth"
    jwt_audience: str = "smart-locker-api"


def from_env() -> Settings:
    """Reads the settings from environment variables.
    Raises RuntimeError if JWT_SECRET or PARCEL_ID_NAMESPACE is missing or invalid."""
    jwt_secret = os.environ.get("JWT_SECRET", "")
    if len(jwt_secret.encode()) < 32:
        # HS256 needs a key of at least 32 bytes (RFC 7518, section 3.2).
        raise RuntimeError("Set JWT_SECRET to a secret of at least 32 bytes.")
    try:
        namespace = uuid.UUID(os.environ.get("PARCEL_ID_NAMESPACE", ""))
    except ValueError:
        raise RuntimeError("Set PARCEL_ID_NAMESPACE to a UUID, for example one made with uuid.uuid4().") from None
    return Settings(
        database_url=os.environ.get("DATABASE_URL", "postgresql+psycopg://localhost/smart_locker"),
        jwt_secret=jwt_secret,
        parcel_id_namespace=namespace,
        jwt_issuer=os.environ.get("JWT_ISSUER", Settings.jwt_issuer),
        jwt_audience=os.environ.get("JWT_AUDIENCE", Settings.jwt_audience),
    )
