from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from deposit_notification.demo import DemoLockerRepository
from deposit_notification.demo_models import Base, Compartment, Locker, Parcel, PickupCode
from deposit_notification.repository import SQLAlchemyDepositRepository


def setup_database(compartment_status="RESERVED"):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    locker = Locker(
        name="Test locker",
        address="1 Test Street",
        gps_location="49.5, 5.9",
        opening_hours="24/7",
        operational_status="ONLINE",
        instructions="Use the side entrance.",
    )
    session.add(locker)
    session.flush()
    compartment = Compartment(
        locker_id=locker.locker_id,
        compartment_number=7,
        size_category="MEDIUM",
        status=compartment_status,
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
    repository = SQLAlchemyDepositRepository(
        DemoLockerRepository(session),
        parcel_model=Parcel,
        compartment_model=Compartment,
        locker_model=Locker,
        pickup_code_model=PickupCode,
    )
    return session, locker, compartment, parcel, repository


def test_reserved_deposit_uses_locker_repository_transition():
    session, _, compartment, parcel, repository = setup_database()
    deposited_at = datetime.now(timezone.utc)

    repository.confirm_assigned_deposit(
        parcel_id=str(parcel.parcel_id),
        locker_id=str(compartment.locker_id),
        compartment_id=str(compartment.compartment_id),
        code_id=uuid4(),
        code_hash="hash-for-test",
        deposited_at=deposited_at,
        pickup_deadline=deposited_at + timedelta(days=7),
    )
    repository.commit()

    session.refresh(parcel)
    session.refresh(compartment)
    assert parcel.status == "READY_FOR_PICKUP"
    assert compartment.status == "OCCUPIED"
    assert compartment.version == 1
    assert session.scalar(select(PickupCode).where(PickupCode.parcel_id == parcel.parcel_id))
    session.close()


def test_maintenance_after_unlock_records_physical_deposit_without_clearing_maintenance():
    session, _, compartment, parcel, repository = setup_database("MAINTENANCE")
    deposited_at = datetime.now(timezone.utc)

    repository.confirm_assigned_deposit(
        parcel_id=str(parcel.parcel_id),
        locker_id=str(compartment.locker_id),
        compartment_id=str(compartment.compartment_id),
        code_id=uuid4(),
        code_hash="maintenance-case-hash",
        deposited_at=deposited_at,
        pickup_deadline=deposited_at + timedelta(days=7),
    )
    repository.commit()

    session.refresh(parcel)
    session.refresh(compartment)
    assert parcel.status == "READY_FOR_PICKUP"
    assert compartment.status == "MAINTENANCE"
    assert session.scalar(select(PickupCode).where(PickupCode.parcel_id == parcel.parcel_id))
    session.close()
