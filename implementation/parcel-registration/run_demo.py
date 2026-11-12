"""Start a localhost-only, self-configuring development demonstration.

Never expose this demo mode on a public network or use it as a production login.
"""
import os
from pathlib import Path
import secrets
import uvicorn
from app.config import Settings
from app.factory import create_app


def main() -> None:
    workdir = Path(__file__).resolve().parent
    os.chdir(workdir)
    settings = Settings(
        jwt_secret=secrets.token_urlsafe(48),
        parcel_id_secret=secrets.token_urlsafe(48),
        database_path=str(workdir / "data" / "demo-parcels.sqlite3"),
        demo_mode=True,
    )
    app = create_app(settings)
    print("\nCourier Parcel Registration prototype: http://127.0.0.1:8000")
    print("DEMO MODE: local development only. No real courier accounts are created.\n")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
