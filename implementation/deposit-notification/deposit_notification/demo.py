"""Local-only SQLite app used to try the UC3 endpoints before team integration."""
from pathlib import Path
import os
import secrets
from typing import Iterator

from fastapi import Depends, FastAPI, Header
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import Session, sessionmaker

from .controller import DepositController
from .contracts import TerminalContext
from .demo_models import Base, Compartment, Locker, Parcel, PickupCode
from .errors import register_error_handlers
from .hardware import ConsoleDoorGateway
from .notifications import NotificationService
from .providers import pickup_notification_gateway_from_env
from .repository import SQLAlchemyDepositRepository
from .security import PickupCodeIssuer
from .service import DepositService


class DemoLockerRepository:
    """Small local stand-in for the UC5 LockerRepository contract."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_compartment_for_update(self, compartment_id):
        return self.session.scalar(
            select(Compartment)
            .where(Compartment.compartment_id == compartment_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    def occupy_compartment(self, compartment_id) -> bool:
        result = self.session.execute(
            update(Compartment)
            .where(
                Compartment.compartment_id == compartment_id,
                Compartment.status == "RESERVED",
            )
            .values(status="OCCUPIED", version=Compartment.version + 1)
        )
        return result.rowcount == 1


def create_demo_app(database_path: str = "data/deposit-demo.sqlite3") -> FastAPI:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(engine, expire_on_commit=False)
    locker_id, compartment_id, parcel_id = _seed_demo_data(session_factory)
    code_secret = os.environ.get("PICKUP_CODE_SECRET") or secrets.token_hex(32)
    issuer = PickupCodeIssuer(code_secret)

    def get_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    def get_deposit_service(session: Session = Depends(get_session)) -> DepositService:
        locker_repository = DemoLockerRepository(session)
        repository = SQLAlchemyDepositRepository(
            locker_repository,
            parcel_model=Parcel,
            compartment_model=Compartment,
            locker_model=Locker,
            pickup_code_model=PickupCode,
        )
        return DepositService(repository, issuer, ConsoleDoorGateway())

    def require_locker_terminal(
        demo_locker_id: str = Header(alias="X-Demo-Locker-ID"),
    ) -> TerminalContext:
        # Local demo header only. Production must inject authenticated hardware identity.
        return TerminalContext(locker_id=demo_locker_id)

    def get_notification_service() -> NotificationService:
        return NotificationService(pickup_notification_gateway_from_env())

    app = FastAPI(title="Smart Parcel Locker — UC3 demo")
    register_error_handlers(app)
    app.include_router(
        DepositController(
            get_deposit_service,
            require_locker_terminal,
            get_notification_service,
        ).router
    )
    app.state.demo_locker_id = str(locker_id)
    app.state.demo_compartment_id = str(compartment_id)
    app.state.demo_parcel_id = str(parcel_id)
    app.state.database_engine = engine
    return app


def _seed_demo_data(session_factory):
    with session_factory() as session:
        assigned = session.scalar(
            select(Parcel).where(Parcel.status == "ASSIGNED").limit(1)
        )
        if assigned is not None and assigned.compartment_id is not None:
            compartment = session.get(Compartment, assigned.compartment_id)
            locker = session.get(Locker, compartment.locker_id) if compartment else None
            if compartment is not None and locker is not None:
                return locker.locker_id, compartment.compartment_id, assigned.parcel_id

        locker = Locker(
            name="UC3 demo locker",
            address="1 Demo Street",
            gps_location="49.5000, 5.9000",
            opening_hours="24/7",
            operational_status="ONLINE",
            instructions="Use the locker entrance beside the reception desk.",
        )
        session.add(locker)
        session.flush()
        compartment = Compartment(
            locker_id=locker.locker_id,
            compartment_number=1,
            size_category="MEDIUM",
            status="RESERVED",
            version=0,
        )
        session.add(compartment)
        session.flush()
        parcel = Parcel(
            status="ASSIGNED",
            compartment_id=compartment.compartment_id,
            recipient_contact="recipient@example.test",
        )
        session.add(parcel)
        session.commit()
        return locker.locker_id, compartment.compartment_id, parcel.parcel_id
