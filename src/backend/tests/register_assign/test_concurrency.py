"""Concurrency tests for NFR_04. They need PostgreSQL (TEST_DATABASE_URL), because SQLite allows only one writer."""
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.db.models import Compartment, Locker, Parcel
from app.repositories.locker_repository import LockerRepository
from app.repositories.unit_of_work import UnitOfWork
from app.services.assignment_service import AssignmentService
from app.services.parcel_errors import CompartmentTaken, DuplicateTrackingNumber, ParcelNotRegistered
from app.services.registration_service import ParcelForm, RegistrationService
from register_assign.support import NAMESPACE, NOW, TOMORROW, uid

COURIER = uid("courier-1")


@pytest.fixture
def pg_engine(engine):
    if engine.dialect.name != "postgresql":
        pytest.skip("needs PostgreSQL: SQLite does not run two writers at once")
    return engine


def new_uow(engine) -> UnitOfWork:
    return UnitOfWork(Session(engine, expire_on_commit=False))


def register(engine, tracking_number: str) -> uuid.UUID:
    uow = new_uow(engine)
    try:
        form = ParcelForm(tracking_number, "MEDIUM", "recipient@example.lu", TOMORROW)
        return RegistrationService(uow, NAMESPACE, now=lambda: NOW).register_parcel(COURIER, form).parcel_id
    finally:
        uow.session.close()


def wait_until_blocked_on_a_lock(engine, timeout=5.0) -> None:
    """Waits until some other session of this database waits for a row lock."""
    query = text(
        "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND wait_event_type = 'Lock'"
    )
    deadline = time.monotonic() + timeout
    # Autocommit, because inside one transaction pg_stat_activity does not change.
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        while connection.execute(query).scalar() == 0:
            assert time.monotonic() < deadline, "the second request never waited for the lock"
            time.sleep(0.01)


def run_at_once(jobs):
    """Runs all jobs at the same time in threads. Returns each result or exception."""
    start = threading.Barrier(len(jobs))

    def run(job):
        start.wait()
        try:
            return job()
        except Exception as exc:  # the test inspects which exception each request got
            return exc

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        return list(pool.map(run, jobs))


def slow_commit(monkeypatch, seconds=0.3):
    """Delays each commit a little, so the other requests reach their UPDATE while the lock is held."""
    real_commit = UnitOfWork.commit

    def commit(self):
        time.sleep(seconds)
        real_commit(self)

    monkeypatch.setattr(UnitOfWork, "commit", commit)


def test_second_reservation_waits_for_the_first_and_then_changes_nothing(pg_engine, belval):
    first = Session(pg_engine)
    second = Session(pg_engine)
    try:
        assert LockerRepository(first).reserve_compartment(belval, uid("comp-04")) is True  # row locked, commit pending
        outcome = {}
        waiting = threading.Thread(
            target=lambda: outcome.update(second=LockerRepository(second).reserve_compartment(belval, uid("comp-04")))
        )
        waiting.start()
        wait_until_blocked_on_a_lock(pg_engine)

        first.commit()
        waiting.join(timeout=5)
        second.commit()
    finally:
        first.close()
        second.close()

    assert outcome == {"second": False}
    with Session(pg_engine) as check:
        compartment = check.get(Compartment, uid("comp-04"))
        assert (compartment.status, compartment.version) == ("RESERVED", 1)


def test_reservation_waits_for_a_station_being_taken_out_of_service_and_then_refuses(pg_engine, belval):
    administrator = Session(pg_engine)
    courier = Session(pg_engine)
    try:
        # Like the admin module: lock the locker row and set it OFFLINE, not committed yet.
        administrator.execute(select(Locker).where(Locker.locker_id == belval).with_for_update())
        administrator.execute(update(Locker).where(Locker.locker_id == belval).values(operational_status="OFFLINE"))
        outcome = {}
        reserve = LockerRepository(courier).reserve_compartment
        waiting = threading.Thread(target=lambda: outcome.update(reserved=reserve(belval, uid("comp-04"))))
        waiting.start()
        wait_until_blocked_on_a_lock(pg_engine)

        administrator.commit()
        waiting.join(timeout=5)
        courier.commit()
    finally:
        administrator.close()
        courier.close()

    assert outcome == {"reserved": False}
    with Session(pg_engine) as check:
        compartment = check.get(Compartment, uid("comp-04"))
        assert (compartment.status, compartment.version) == ("AVAILABLE", 0)


def test_many_couriers_assigning_the_same_compartment_at_once_one_wins(pg_engine, belval, monkeypatch):
    parcels = [register(pg_engine, f"LU-{n}") for n in range(8)]
    slow_commit(monkeypatch)

    def assign(parcel_id):
        uow = new_uow(pg_engine)
        try:
            return AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, uid("comp-04"))
        finally:
            uow.session.close()

    results = run_at_once([lambda p=p: assign(p) for p in parcels])

    winners = [r for r in results if not isinstance(r, Exception)]
    assert len(winners) == 1
    assert all(isinstance(r, CompartmentTaken) for r in results if r not in winners)
    with Session(pg_engine) as check:
        assert check.get(Compartment, uid("comp-04")).version == 1
        assigned = check.scalars(select(Parcel).where(Parcel.status == "ASSIGNED")).all()
        assert [(p.parcel_id, p.compartment_id) for p in assigned] == [(winners[0][0].parcel_id, uid("comp-04"))]


def test_one_parcel_assigned_to_two_compartments_at_once_gets_only_one(pg_engine, belval, monkeypatch):
    parcel_id = register(pg_engine, "LU-1")
    slow_commit(monkeypatch)

    def assign(compartment_id):
        uow = new_uow(pg_engine)
        try:
            return AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, compartment_id)
        finally:
            uow.session.close()

    results = run_at_once([lambda: assign(uid("comp-04")), lambda: assign(uid("comp-09"))])

    winners = [r for r in results if not isinstance(r, Exception)]
    losers = [r for r in results if isinstance(r, Exception)]
    assert len(winners) == 1
    assert len(losers) == 1 and isinstance(losers[0], ParcelNotRegistered)
    won = winners[0][1].compartment_id
    lost = ({uid("comp-04"), uid("comp-09")} - {won}).pop()
    with Session(pg_engine) as check:
        assert check.get(Compartment, won).status == "RESERVED"
        assert check.get(Compartment, lost).status == "AVAILABLE"  # the losing reservation was undone
        assert check.get(Parcel, parcel_id).compartment_id == won


def test_same_tracking_number_registered_twice_at_once_gives_one_duplicate(pg_engine, monkeypatch):
    slow_commit(monkeypatch)

    def attempt():
        return register(pg_engine, "LU-987654321")

    results = run_at_once([attempt, attempt])

    assert sum(isinstance(r, uuid.UUID) for r in results) == 1
    assert sum(isinstance(r, DuplicateTrackingNumber) for r in results) == 1
