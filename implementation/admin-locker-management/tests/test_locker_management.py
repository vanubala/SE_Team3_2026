from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from locker_management.app import create_app
from locker_management.auth import AUDIENCE, ISSUER
from locker_management.models import Base, Compartment, CompartmentStatus, Locker, Parcel
from locker_management.repository import LockerRepository
from locker_management.service import ConflictError, InvalidStatusError, LockerManagementService

SECRET = "test-secret-that-is-longer-than-32-bytes"


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.sqlite3').as_posix()}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def client(engine):
    with TestClient(create_app(engine, SECRET)) as client:
        client.headers["Authorization"] = f"Bearer {token()}"
        yield client


def token(role="ADMIN", secret=SECRET, minutes=5, **overrides):
    claims = {"sub": "admin-1", "role": role, "iss": ISSUER, "aud": AUDIENCE,
              "exp": datetime.now(timezone.utc) + timedelta(minutes=minutes)} | overrides
    return jwt.encode(claims, secret, algorithm="HS256")


def add_locker(engine, *statuses, name="Belval", sizes=None, locker_status="ONLINE"):
    """Returns (locker id, [compartment ids])."""
    sizes = sizes or ["SMALL"] * len(statuses)
    with Session(engine) as session:
        locker = Locker(name=name, address="a", gps_location="0,0", opening_hours="24/7",
                        operational_status=locker_status)
        locker.compartments = [
            Compartment(compartment_number=n, size_category=size, status=status)
            for n, (status, size) in enumerate(zip(statuses, sizes), start=1)
        ]
        session.add(locker)
        session.commit()
        return locker.locker_id, [c.compartment_id for c in locker.compartments]


def add_parcel(engine, compartment_id, status):
    with Session(engine) as session:
        session.add(Parcel(status=status, compartment_id=compartment_id))
        session.commit()


def stored(engine, compartment_id):
    with Session(engine) as session:
        return session.get(Compartment, compartment_id)


def patch(client, compartment_id, status):
    return client.patch(f"/api/admin/compartments/{compartment_id}/status", json={"status": status})


def assert_envelope(response, status, error):
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"timestamp", "status", "error", "message"}
    assert (body["status"], body["error"]) == (status, error)


# Access (FR_05, NFR_01)

ROUTES = [
    ("GET", "/api/admin/lockers", None),
    ("PATCH", f"/api/admin/compartments/{uuid4()}/status", {"status": "MAINTENANCE"}),
    ("PATCH", f"/api/admin/lockers/{uuid4()}", {"operationalStatus": "OFFLINE"}),
]


@pytest.mark.parametrize("method,path,body", ROUTES, ids=["overview", "compartment", "locker"])
def test_every_route_needs_an_admin(client, method, path, body):
    del client.headers["Authorization"]
    assert_envelope(client.request(method, path, json=body), 401, "UNAUTHORIZED")
    headers = {"Authorization": f"Bearer {token('COURIER')}"}
    assert_envelope(client.request(method, path, json=body, headers=headers), 403, "FORBIDDEN")


@pytest.mark.parametrize("bad", [
    {"minutes": -5}, {"secret": "another-secret-longer-than-32-bytes!"},
    {"iss": "other"}, {"aud": "other"},
])
def test_bad_tokens_are_refused(client, bad):
    response = client.get("/api/admin/lockers", headers={"Authorization": f"Bearer {token(**bad)}"})
    assert_envelope(response, 401, "UNAUTHORIZED")


# Monitoring (FR_09)

def test_overview(client, engine):
    locker_id, ids = add_locker(
        engine, "AVAILABLE", "RESERVED", "OCCUPIED", "MAINTENANCE", "AVAILABLE",
        sizes=["SMALL", "MEDIUM", "LARGE", "SMALL", "LARGE"],
    )
    add_locker(engine, name="Empty", locker_status="OFFLINE")
    response = client.get("/api/admin/lockers")
    assert response.status_code == 200
    belval, empty = response.json()
    assert belval["lockerId"] == str(locker_id)
    assert belval["occupancy"] == {
        "total": 5, "available": 2, "reserved": 1, "occupied": 1, "maintenance": 1,
        "occupancyRate": 40.0, "availableBySize": {"SMALL": 1, "MEDIUM": 0, "LARGE": 1},
    }
    assert belval["compartments"][0] == {
        "compartmentId": str(ids[0]), "number": 1, "size": "SMALL", "status": "AVAILABLE"}
    assert [c["number"] for c in belval["compartments"]] == [1, 2, 3, 4, 5]
    assert empty["operationalStatus"] == "OFFLINE"
    assert empty["occupancy"]["occupancyRate"] == 0


def test_overview_without_lockers(client):
    assert client.get("/api/admin/lockers").json() == []


def test_overview_query_count_does_not_grow_with_lockers(client, engine):
    for n in range(5):
        add_locker(engine, "AVAILABLE", name=str(n))
    queries = []
    event.listen(engine, "before_cursor_execute", lambda *args: queries.append(args[2]))
    client.get("/api/admin/lockers")
    assert len(queries) == 2


# Compartment status (FR_10)

def test_block_and_restore(client, engine):
    _, [cid] = add_locker(engine, "AVAILABLE")
    for version, status in enumerate(["MAINTENANCE", "AVAILABLE"], start=1):
        response = patch(client, cid, status)
        assert response.status_code == 200
        assert response.json() == {"compartmentId": str(cid), "status": status}
        assert (stored(engine, cid).status, stored(engine, cid).version) == (status, version)


def test_repeating_a_status_changes_nothing(client, engine):
    _, [cid] = add_locker(engine, "MAINTENANCE")
    assert patch(client, cid, "MAINTENANCE").status_code == 200
    assert stored(engine, cid).version == 0


@pytest.mark.parametrize("current,parcel", [
    ("RESERVED", "ASSIGNED"), ("OCCUPIED", "READY_FOR_PICKUP"), ("OCCUPIED", "EXPIRED"),
    ("MAINTENANCE", "READY_FOR_PICKUP"),
])
def test_cannot_free_a_compartment_with_an_active_parcel(client, engine, current, parcel):
    _, [cid] = add_locker(engine, current)
    add_parcel(engine, cid, parcel)
    assert_envelope(patch(client, cid, "AVAILABLE"), 409, "CONFLICT")
    assert stored(engine, cid).status == current


def test_can_free_a_compartment_once_the_parcel_is_collected(client, engine):
    _, [cid] = add_locker(engine, "OCCUPIED")
    add_parcel(engine, cid, "COLLECTED")
    assert patch(client, cid, "AVAILABLE").status_code == 200


def test_maintenance_with_a_parcel_inside_warns_but_succeeds(client, engine):
    _, [cid] = add_locker(engine, "OCCUPIED")
    add_parcel(engine, cid, "READY_FOR_PICKUP")
    response = patch(client, cid, "MAINTENANCE")
    assert response.status_code == 200
    assert "active parcel" in response.json()["warning"]
    assert stored(engine, cid).status == "MAINTENANCE"


@pytest.mark.parametrize("status", ["OCCUPIED", "RESERVED", "BROKEN", None])
def test_invalid_compartment_status(client, engine, status):
    _, [cid] = add_locker(engine, "AVAILABLE")
    assert_envelope(patch(client, cid, status), 400, "BAD_REQUEST")


def test_unknown_or_malformed_compartment(client):
    assert_envelope(patch(client, uuid4(), "MAINTENANCE"), 404, "NOT_FOUND")
    assert_envelope(patch(client, "not-a-uuid", "MAINTENANCE"), 400, "BAD_REQUEST")


def test_service_itself_rejects_parcel_driven_statuses(engine):
    with Session(engine) as session, pytest.raises(InvalidStatusError):
        LockerManagementService(LockerRepository(session)).change_compartment_status(
            uuid4(), CompartmentStatus.OCCUPIED)


# Station status (FR_10)

@pytest.mark.parametrize("status", ["OFFLINE", "MAINTENANCE", "ONLINE"])
def test_change_locker_status(client, engine, status):
    locker_id, [cid] = add_locker(engine, "MAINTENANCE")
    response = client.patch(f"/api/admin/lockers/{locker_id}", json={"operationalStatus": status})
    assert response.status_code == 200
    assert response.json() == {"lockerId": str(locker_id), "operationalStatus": status}
    with Session(engine) as session:
        assert session.get(Locker, locker_id).operational_status == status
    assert stored(engine, cid).status == "MAINTENANCE"


def test_locker_with_parcels_warns(client, engine):
    locker_id, [cid] = add_locker(engine, "OCCUPIED")
    add_parcel(engine, cid, "READY_FOR_PICKUP")
    response = client.patch(f"/api/admin/lockers/{locker_id}", json={"operationalStatus": "OFFLINE"})
    assert "1 active parcel" in response.json()["warning"]


def test_unknown_locker_and_invalid_status(client):
    path = f"/api/admin/lockers/{uuid4()}"
    assert_envelope(client.patch(path, json={"operationalStatus": "OFFLINE"}), 404, "NOT_FOUND")
    assert_envelope(client.patch(path, json={"operationalStatus": "BROKEN"}), 400, "BAD_REQUEST")


# Concurrency and failures (NFR_04)

def test_lost_update_is_refused(engine):
    _, [cid] = add_locker(engine, "AVAILABLE")

    class RacingRepository(LockerRepository):
        def has_active_parcel(self, compartment_id):
            # A courier reserves the compartment between our read and our write.
            self.session.rollback()
            with Session(engine) as other:
                compartment = other.get(Compartment, compartment_id)
                compartment.status = "RESERVED"
                compartment.version += 1
                other.commit()
            return False

    with Session(engine) as session, pytest.raises(ConflictError):
        LockerManagementService(RacingRepository(session)).change_compartment_status(
            cid, CompartmentStatus.MAINTENANCE)
    assert stored(engine, cid).status == "RESERVED"


def test_postgresql_rows_are_locked():
    class CapturingSession:
        def scalar(self, statement):
            self.sql = str(statement.compile(dialect=postgresql.dialect()))

    session = CapturingSession()
    repository = LockerRepository(session)
    repository.get_compartment_for_update(uuid4())
    assert "FOR UPDATE" in session.sql
    repository.get_locker_for_update(uuid4())
    assert "FOR UPDATE" in session.sql
    repository.reserve_compartment(uuid4(), uuid4())
    assert "FOR SHARE" in session.sql


def test_database_failure_is_reported_without_details(client, monkeypatch):
    def fail(self):
        raise OperationalError("SELECT secret", {}, Exception("password"))

    monkeypatch.setattr(LockerRepository, "find_all_with_compartments", fail)
    response = client.get("/api/admin/lockers")
    assert_envelope(response, 503, "SERVICE_UNAVAILABLE")
    assert "secret" not in response.text and "password" not in response.text


# Operations offered to the other services

def test_compartment_can_only_be_reserved_once(engine):
    locker_id, [cid] = add_locker(engine, "AVAILABLE")
    for expected in (True, False):
        with Session(engine) as session:
            assert LockerRepository(session).reserve_compartment(locker_id, cid) is expected
            session.commit()


@pytest.mark.parametrize("locker_status,status", [
    ("OFFLINE", "AVAILABLE"), ("MAINTENANCE", "AVAILABLE"), ("ONLINE", "MAINTENANCE"),
])
def test_blocked_compartments_cannot_be_reserved(engine, locker_status, status):
    locker_id, [cid] = add_locker(engine, status, locker_status=locker_status)
    with Session(engine) as session:
        assert not LockerRepository(session).reserve_compartment(locker_id, cid)


def test_cannot_reserve_through_another_station(engine):
    _, [cid] = add_locker(engine, "AVAILABLE")
    other, _ = add_locker(engine, name="Other")
    with Session(engine) as session:
        assert not LockerRepository(session).reserve_compartment(other, cid)


def test_deposit_then_pickup(engine):
    _, [cid] = add_locker(engine, "RESERVED")
    with Session(engine) as session:
        repository = LockerRepository(session)
        assert repository.occupy_compartment(cid)
        assert repository.release_compartment(cid)
        session.commit()
    assert stored(engine, cid).status == "AVAILABLE"


def test_pickup_does_not_end_maintenance(engine):
    _, [cid] = add_locker(engine, "MAINTENANCE")
    with Session(engine) as session:
        assert not LockerRepository(session).release_compartment(cid)


def test_repository_leaves_the_commit_to_the_caller(engine):
    locker_id, [cid] = add_locker(engine, "AVAILABLE")
    with Session(engine) as session:
        assert LockerRepository(session).reserve_compartment(locker_id, cid)
        session.rollback()
    assert stored(engine, cid).status == "AVAILABLE"
