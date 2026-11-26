"""Requirement oracles for UC4 guest pickup: FR_01, FR_08, NFR_02, NFR_03; Schemas-Endpoints §2.5."""
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.config import Settings
from app.db.models import Base, Compartment, Locker, Parcel, PickupCode, TerminalLockout, User
from app.main import create_app
from app.repositories.pickup_repository import PickupRepository
from app.security.pickup_codes import PickupCodeHasher, PickupSession, PickupSessionTokens
from app.services import pickup_service
from app.services.pickup_service import PickupCodeIssuer

SECRET = 'test-only-' + 'p' * 40
CODE = '482910'
OTHER_CODE = '111111'


@pytest.fixture
def settings():
    return Settings(database_url='sqlite+pysqlite://', jwt_secret=SECRET)


@pytest.fixture
def engine():
    engine = create_engine('sqlite+pysqlite://', poolclass=StaticPool,
                           connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def world(engine, settings):
    """One locker with a parcel READY_FOR_PICKUP in compartment #4, plus a second locker."""
    hasher = PickupCodeHasher(settings)
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        courier = User(name='Courier', email='c@example.test', password_hash='x', role='COURIER')
        locker = Locker(name='Belval', address='a', gps_location='49,6', opening_hours='24/7')
        other_locker = Locker(name='Kirchberg', address='b', gps_location='49,6', opening_hours='24/7')
        db.add_all([courier, locker, other_locker]); db.flush()
        comp = Compartment(locker_id=locker.locker_id, compartment_number=4, size_category='MEDIUM', status='OCCUPIED')
        db.add(comp); db.flush()
        parcel = Parcel(parcel_id=uuid4(), tracking_number='LU-1', size_category='MEDIUM', status='READY_FOR_PICKUP',
                        preferred_locker_id=locker.locker_id, compartment_id=comp.compartment_id,
                        registered_by_courier_id=courier.user_id, recipient_contact='r@example.test',
                        deposited_at=now, pickup_deadline=now + timedelta(days=7))
        db.add(parcel); db.flush()
        db.add(PickupCode(parcel_id=parcel.parcel_id, code_hash=hasher.hash(CODE), failed_attempts=0,
                          expires_at=now + timedelta(days=7)))
        db.commit()
        return {'locker': locker.locker_id, 'other_locker': other_locker.locker_id,
                'compartment': comp.compartment_id, 'parcel': parcel.parcel_id}


@pytest.fixture
def client(engine, settings, world):
    with TestClient(create_app(settings, engine=engine)) as c:
        yield c


def verify(client, locker, code=CODE):
    return client.post('/api/terminal/pickup/verify', json={'lockerId': str(locker), 'pickupCode': code})


def confirm(client, body):
    return client.post('/api/terminal/pickup/confirm', json=body)


def confirm_body(world, token, **kw):
    return {'parcelId': str(world['parcel']), 'compartmentId': str(world['compartment']),
            'doorClosed': True, 'pickupSessionToken': token} | kw


def load(engine, model, key):
    with Session(engine) as db:
        return db.get(model, key)


def test_full_pickup_flow(client, engine, world):
    r = verify(client, world['locker'])
    assert r.status_code == 200 and r.headers['cache-control'] == 'no-store'
    body = r.json()
    assert body['parcelId'] == str(world['parcel']) and body['compartmentId'] == str(world['compartment'])
    assert body['compartmentNumber'] == 4 and body['doorCommand'] == 'UNLOCK' and body['pickupSessionToken']

    r = confirm(client, confirm_body(world, body['pickupSessionToken']))
    assert r.status_code == 200
    assert r.json() == {'parcelId': str(world['parcel']), 'status': 'COLLECTED', 'compartmentStatus': 'AVAILABLE'}
    parcel = load(engine, Parcel, world['parcel'])
    assert parcel.status == 'COLLECTED' and parcel.collected_at is not None
    comp = load(engine, Compartment, world['compartment'])
    assert comp.status == 'AVAILABLE' and comp.version == 1
    with Session(engine) as db:
        assert db.scalar(select(PickupCode)).used_at is not None

    # Single-use: the same PIN no longer opens anything.
    assert verify(client, world['locker']).status_code == 401


def test_code_is_valid_only_at_its_own_station(client, world):
    r = verify(client, world['other_locker'])
    assert r.status_code == 401 and r.json()['remainingAttempts'] == 4


def test_wrong_code_reports_remaining_attempts_in_error_envelope(client, world):
    r = verify(client, world['locker'], OTHER_CODE)
    assert r.status_code == 401
    b = r.json()
    assert {'timestamp', 'status', 'error', 'message', 'remainingAttempts'} <= set(b)
    assert b['status'] == 401 and b['remainingAttempts'] == 4


def test_five_failures_lock_terminal_even_for_correct_code(client, world):
    remaining = [verify(client, world['locker'], OTHER_CODE).json().get('remainingAttempts') for _ in range(4)]
    assert remaining == [4, 3, 2, 1]
    r = verify(client, world['locker'], OTHER_CODE)
    assert r.status_code == 423 and r.json()['retryAfterSeconds'] == 900 and r.headers['retry-after'] == '900'
    r = verify(client, world['locker'], CODE)
    assert r.status_code == 423 and 0 < r.json()['retryAfterSeconds'] <= 900
    # Lockout is per terminal: other stations keep working (NFR_07).
    assert verify(client, world['other_locker'], OTHER_CODE).json()['remainingAttempts'] == 4


def test_success_resets_failure_counter(client, engine, world):
    for _ in range(4):
        verify(client, world['locker'], OTHER_CODE)
    assert verify(client, world['locker']).status_code == 200
    assert load(engine, TerminalLockout, world['locker']).failed_attempts == 0
    assert verify(client, world['locker'], OTHER_CODE).json()['remainingAttempts'] == 4


def use_clock(client, clock):
    from fastapi import Request, Depends
    from app.db.session import get_db
    from app.controllers.pickup_controller import get_pickup_service

    def service(request: Request, db: Session = Depends(get_db)):
        return pickup_service.PickupService(PickupRepository(db), request.app.state.pickup_codes,
                                            request.app.state.pickup_sessions, clock=clock)
    client.app.dependency_overrides[get_pickup_service] = service


def test_lockout_expires_after_15_minutes(client, world):
    start = datetime.now(timezone.utc)
    now = {'t': start}
    use_clock(client, lambda: now['t'])
    for _ in range(5):
        verify(client, world['locker'], OTHER_CODE)
    now['t'] = start + timedelta(minutes=14)
    assert verify(client, world['locker']).status_code == 423
    now['t'] = start + timedelta(minutes=15, seconds=1)
    assert verify(client, world['locker']).status_code == 200


def test_failures_far_apart_are_not_consecutive(client, world):
    start = datetime.now(timezone.utc)
    now = {'t': start}
    use_clock(client, lambda: now['t'])
    for _ in range(4):
        verify(client, world['locker'], OTHER_CODE)
    now['t'] = start + timedelta(minutes=20)
    assert verify(client, world['locker'], OTHER_CODE).json()['remainingAttempts'] == 4


def test_expired_code_is_rejected(client, engine, world):
    with Session(engine) as db:
        code = db.scalar(select(PickupCode))
        code.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    assert verify(client, world['locker']).status_code == 401


@pytest.mark.parametrize('body', [
    {'lockerId': 'not-a-uuid', 'pickupCode': CODE},
    {'lockerId': str(uuid4()), 'pickupCode': '12345'},
    {'lockerId': str(uuid4()), 'pickupCode': 'abcdef'},
    {'lockerId': str(uuid4()), 'pickupCode': CODE, 'extra': 1},
])
def test_malformed_verify_is_400(client, body):
    assert client.post('/api/terminal/pickup/verify', json=body).status_code == 400


def test_unknown_locker_is_404(client):
    assert verify(client, uuid4()).status_code == 404


def test_confirm_requires_valid_session(client, world, settings):
    assert confirm(client, confirm_body(world, 'forged')).status_code == 401
    other = PickupSessionTokens(Settings(database_url='sqlite+pysqlite://', jwt_secret='other-secret-' + 'z' * 40))
    forged = other.issue(PickupSession(world['parcel'], world['compartment'], world['locker']))
    assert confirm(client, confirm_body(world, forged)).status_code == 401
    expired = PickupSessionTokens(settings).issue(
        PickupSession(world['parcel'], world['compartment'], world['locker']),
        now=datetime.now(timezone.utc) - timedelta(hours=1))
    assert confirm(client, confirm_body(world, expired)).status_code == 401


def test_staff_jwt_is_not_a_pickup_session(client, world, settings):
    from app.security.tokens import TokenService
    from app.db.models import Role
    staff = TokenService(settings).issue(uuid4(), Role.ADMIN)
    assert confirm(client, confirm_body(world, staff)).status_code == 401


def test_session_is_bound_to_parcel_and_compartment(client, world):
    token = verify(client, world['locker']).json()['pickupSessionToken']
    assert confirm(client, confirm_body(world, token, parcelId=str(uuid4()))).status_code == 401
    assert confirm(client, confirm_body(world, token, compartmentId=str(uuid4()))).status_code == 401


@pytest.mark.parametrize('override,message', [({'doorClosed': False}, 'door is still open'),
                                              ({'parcelDetected': True}, 'still detected')])
def test_confirm_rejects_open_door_or_parcel_left(client, engine, world, override, message):
    token = verify(client, world['locker']).json()['pickupSessionToken']
    r = confirm(client, confirm_body(world, token, **override))
    assert r.status_code == 409 and message in r.json()['message']
    assert load(engine, Parcel, world['parcel']).status == 'READY_FOR_PICKUP'


def test_confirm_is_idempotent_on_retry(client, engine, world):
    token = verify(client, world['locker']).json()['pickupSessionToken']
    first = confirm(client, confirm_body(world, token))
    second = confirm(client, confirm_body(world, token))
    assert first.status_code == second.status_code == 200 and first.json() == second.json()
    assert load(engine, Compartment, world['compartment']).version == 1


def test_maintenance_compartment_is_not_released(client, engine, world):
    token = verify(client, world['locker']).json()['pickupSessionToken']
    with Session(engine) as db:
        db.get(Compartment, world['compartment']).status = 'MAINTENANCE'; db.commit()
    r = confirm(client, confirm_body(world, token))
    assert r.status_code == 200 and r.json()['compartmentStatus'] == 'MAINTENANCE'


def test_code_is_stored_only_as_hash(engine, world):
    with Session(engine) as db:
        assert CODE not in db.scalar(select(PickupCode)).code_hash


def test_issuer_creates_unique_six_digit_code(engine, world, settings):
    hasher = PickupCodeHasher(settings)
    with Session(engine) as db:
        db.get(PickupCode, db.scalar(select(PickupCode.code_id))).used_at = datetime.now(timezone.utc)
        db.commit()
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        code = PickupCodeIssuer(PickupRepository(db), hasher).issue(world['parcel'], world['locker'], expires)
        db.commit()
        assert len(code) == 6 and code.isdigit()
        stored = db.scalar(select(PickupCode))
        assert stored.code_hash == hasher.hash(code) and stored.used_at is None


def test_issuer_skips_codes_already_active_at_station(engine, world, settings, monkeypatch):
    hasher = PickupCodeHasher(settings)
    candidates = iter([CODE, '000777'])
    monkeypatch.setattr(pickup_service, 'generate_pickup_code', lambda: next(candidates))
    with Session(engine) as db:
        courier_id = db.scalar(select(User.user_id))
        new_parcel = Parcel(parcel_id=uuid4(), tracking_number='LU-2', size_category='SMALL', status='ASSIGNED',
                            registered_by_courier_id=courier_id, recipient_contact='r2@example.test')
        db.add(new_parcel); db.commit()
        code = PickupCodeIssuer(PickupRepository(db), hasher).issue(
            new_parcel.parcel_id, world['locker'], datetime.now(timezone.utc) + timedelta(days=7))
        assert code == '000777'


def test_pickup_code_is_never_echoed_in_validation_errors(client):
    r = client.post('/api/terminal/pickup/verify', json={'lockerId': 'bad', 'pickupCode': '999999'})
    assert '999999' not in r.text
