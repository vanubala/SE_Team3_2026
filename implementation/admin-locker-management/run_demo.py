"""Local demo: in-memory SQLite data and a one-hour admin token. Not for production."""
from datetime import datetime, timedelta, timezone
import secrets

import jwt
import uvicorn
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from locker_management.app import create_app
from locker_management.auth import AUDIENCE, ISSUER
from locker_management.models import Base, Compartment, Locker, Parcel


def main() -> None:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        locker = Locker(name="Belval Plaza Station", address="Belval", gps_location="49.50,5.94",
                        opening_hours="24/7")
        statuses = ["AVAILABLE", "AVAILABLE", "RESERVED", "OCCUPIED", "MAINTENANCE", "AVAILABLE"]
        sizes = ["SMALL", "SMALL", "MEDIUM", "MEDIUM", "LARGE", "LARGE"]
        locker.compartments = [
            Compartment(compartment_number=n, size_category=size, status=status)
            for n, (size, status) in enumerate(zip(sizes, statuses), start=1)
        ]
        session.add(locker)
        session.flush()
        session.add_all([
            Parcel(status="ASSIGNED", compartment_id=locker.compartments[2].compartment_id),
            Parcel(status="READY_FOR_PICKUP", compartment_id=locker.compartments[3].compartment_id),
        ])
        session.commit()

    secret = secrets.token_urlsafe(48)
    token = jwt.encode({
        "sub": "demo-admin", "role": "ADMIN", "iss": ISSUER, "aud": AUDIENCE,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }, secret, algorithm="HS256")
    print("Open http://127.0.0.1:8000/docs, click Authorize and paste this token:\n")
    print(token, "\n", flush=True)
    uvicorn.run(create_app(engine, secret), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
