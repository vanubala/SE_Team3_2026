"""Configuration for the standalone registration prototype."""
from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    parcel_id_secret: str
    database_path: str
    jwt_issuer: str = "smart-locker-auth"
    jwt_audience: str = "smart-locker-api"
    pickup_window_hours: int = 72
    demo_mode: bool = False

    def __post_init__(self) -> None:
        if len(self.jwt_secret.encode()) < 32 or len(self.parcel_id_secret.encode()) < 32:
            raise ValueError("JWT_SECRET and PARCEL_ID_SECRET must each be at least 32 bytes")
        if self.jwt_secret == self.parcel_id_secret:
            raise ValueError("Use different JWT and parcel-ID signing secrets")
        if self.pickup_window_hours < 1 or self.pickup_window_hours > 24 * 30:
            raise ValueError("PICKUP_WINDOW_HOURS must be between 1 and 720")


def from_env() -> Settings:
    jwt_secret = os.environ.get("JWT_SECRET", "")
    parcel_id_secret = os.environ.get("PARCEL_ID_SECRET", "")
    if not jwt_secret or not parcel_id_secret:
        raise RuntimeError("JWT_SECRET and PARCEL_ID_SECRET must be set. For a demo run: python run_demo.py")
    return Settings(
        jwt_secret=jwt_secret,
        parcel_id_secret=parcel_id_secret,
        database_path=os.environ.get("DATABASE_PATH", str(Path("data") / "parcels.sqlite3")),
        jwt_issuer=os.environ.get("JWT_ISSUER", "smart-locker-auth"),
        jwt_audience=os.environ.get("JWT_AUDIENCE", "smart-locker-api"),
        pickup_window_hours=int(os.environ.get("PICKUP_WINDOW_HOURS", "72")),
        demo_mode=os.environ.get("DEMO_MODE", "0") == "1",
    )
