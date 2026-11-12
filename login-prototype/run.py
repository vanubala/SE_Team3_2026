"""Start the shared sign-in prototype on this computer only.

    python run.py                          new random staff passwords on each start
    python run.py --staff-password S3cret!pass   one password for all staff accounts
    python run.py --reset                  delete registered senders/recipients first
"""
import argparse
import os
from pathlib import Path

import uvicorn

from app.config import Settings
from app.main import create_app

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "data" / "accounts.sqlite3"
ROLE_LABELS = {"ADMINISTRATOR": "Administrator", "COURIER": "Courier"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Parcel Locker shared sign-in prototype")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--staff-password", default=os.environ.get("DEMO_STAFF_PASSWORD"),
                        help="one password for every courier and administrator account (min. 8 characters)")
    parser.add_argument("--reset", action="store_true",
                        help="delete the local database before starting")
    args = parser.parse_args()

    if args.reset and DATABASE.exists():
        DATABASE.unlink()
        print("Local database deleted.")

    settings = Settings(database_path=str(DATABASE), staff_password=args.staff_password)
    app = create_app(settings)
    url = f"http://127.0.0.1:{args.port}"

    print()
    print("Smart Parcel Locker - shared sign-in prototype")
    print(f"Open {url} in your browser. Press Ctrl+C to stop.")
    print()
    if args.staff_password:
        print("Company accounts (password set with --staff-password):")
    else:
        print("Company accounts (new passwords on every start):")
    print(f"  {'ID':<9} {'Role':<14} {'Name':<16} Password")
    for account in app.state.staff_credentials:
        print(f"  {account['loginId']:<9} {ROLE_LABELS[account['role']]:<14} "
              f"{account['name']:<16} {account['password']}")
    print()
    print("Senders and recipients: create an account on the page with an email or phone number.")
    print("There is no SMS/email gateway, so one-time codes appear on screen and below.")
    print()

    # Bound to localhost only: this is a local prototype, not a public server.
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
