"""Executable acceptance tests for Modular-Design.md (C1)."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import sqlite3
from app.factory import create_app
from fastapi.testclient import TestClient


def test_register_success_full_pipeline(client, auth, request_payload, settings):
    response = client.post('/api/parcels', headers=auth(), json=request_payload)
    assert response.status_code == 201, response.text
    result = response.json()
    assert result['status'] == 'SUCCESS'
    assert result['parcelId'] == result['parcel']['parcelId']
    assert result['parcel']['trackingNumber'] == request_payload['barcode']
    assert result['parcel']['size'] == 'MEDIUM'
    assert result['parcel']['status'] == 'REGISTERED'
    assert result['parcel']['notes'] == 'Fragile - handle with care'
    assert len(result['parcelId']) == 64
    delivery = datetime.fromisoformat(result['parcel']['expectedDeliveryAt'].replace('Z','+00:00'))
    deadline = datetime.fromisoformat(result['parcel']['pickupDeadline'].replace('Z','+00:00'))
    assert deadline - delivery == timedelta(hours=72)
    with sqlite3.connect(settings.database_path) as db:
        assert db.execute('SELECT COUNT(*) FROM parcels').fetchone()[0] == 1


def test_missing_auth_rejected(client, request_payload):
    assert client.post('/api/parcels', json=request_payload).status_code == 401
    assert client.get('/api/parcels').status_code == 401


def test_bad_signature_rejected(client, auth, request_payload):
    token = auth()['Authorization'].split(' ',1)[1]
    header = {'Authorization': 'Bearer ' + token[:-2] + ('aa' if token[-2:] != 'aa' else 'bb')}
    assert client.post('/api/parcels', json=request_payload, headers=header).status_code == 401


def test_expired_token_rejected(client, auth, request_payload):
    assert client.post('/api/parcels', json=request_payload, headers=auth(ttl_seconds=-60)).status_code == 401


def test_wrong_role_rejected(client, auth, request_payload):
    assert client.post('/api/parcels', json=request_payload, headers=auth(role='RECIPIENT')).status_code == 403


def test_duplicate_rejected_with_conflict(client, auth, request_payload):
    assert client.post('/api/parcels', json=request_payload, headers=auth()).status_code == 201
    response = client.post('/api/parcels', json=request_payload, headers=auth())
    assert response.status_code == 409
    assert 'already registered' in response.json()['detail']
    assert len(client.get('/api/parcels', headers=auth()).json()) == 1


def test_invalid_package_size_rejected(client, auth, request_payload):
    payload={**request_payload, 'size':'HUGE'}
    assert client.post('/api/parcels', json=payload, headers=auth()).status_code == 422


def test_invalid_barcode_rejected(client, auth, request_payload):
    payload={**request_payload, 'barcode':'x!'}
    assert client.post('/api/parcels', json=payload, headers=auth()).status_code == 422


def test_past_delivery_rejected(client, auth, request_payload):
    payload={**request_payload, 'expectedDeliveryAt':(datetime.now(timezone.utc)-timedelta(days=1)).isoformat()}
    assert client.post('/api/parcels', json=payload, headers=auth()).status_code == 422


def test_naive_delivery_datetime_rejected(client, auth, request_payload):
    payload={**request_payload, 'expectedDeliveryAt':'2030-01-01T12:00:00'}
    assert client.post('/api/parcels', json=payload, headers=auth()).status_code == 422


def test_notes_controls_removed(client, auth, request_payload):
    payload={**request_payload, 'notes':'  fragile\x00\x07\nhandle with care  '}
    response=client.post('/api/parcels', json=payload, headers=auth())
    assert response.status_code == 201
    assert response.json()['parcel']['notes'] == 'fragile\nhandle with care'


def test_courier_data_is_isolated(client, auth, request_payload):
    assert client.post('/api/parcels', json=request_payload, headers=auth(subject='alice')).status_code == 201
    assert len(client.get('/api/parcels', headers=auth(subject='alice')).json()) == 1
    assert len(client.get('/api/parcels', headers=auth(subject='bob')).json()) == 0


def test_data_persists_app_restart(settings, auth, request_payload):
    with TestClient(create_app(settings)) as client1:
        response=client1.post('/api/parcels', json=request_payload, headers=auth())
        assert response.status_code == 201
        first_id=response.json()['parcelId']
    with TestClient(create_app(settings)) as client2:
        parcels=client2.get('/api/parcels', headers=auth()).json()
        assert parcels[0]['parcelId'] == first_id


def test_hash_id_is_deterministic_and_secret_keyed(client, auth, request_payload, settings):
    response=client.post('/api/parcels', json=request_payload, headers=auth())
    expected=hmac.new(settings.parcel_id_secret.encode(),request_payload['barcode'].encode(),hashlib.sha256).hexdigest()
    assert response.json()['parcelId'] == expected
    assert response.json()['parcelId'] != hashlib.sha256(request_payload['barcode'].encode()).hexdigest()


def test_demo_endpoint_disabled_by_default(client):
    assert client.get('/api/demo-session').status_code == 404


def test_invalid_payload_extraneous_fields_rejected(client, auth, request_payload):
    assert client.post('/api/parcels', headers=auth(), json={**request_payload,'courierId':'admin'}).status_code == 422


def test_public_dto_does_not_leak_courier_identity(client, auth, request_payload):
    result=client.post('/api/parcels', headers=auth(), json=request_payload).json()
    assert 'courier_id' not in result['parcel'] and 'courierId' not in result['parcel']


def test_api_health_and_frontend(client):
    assert client.get('/health').json() == {'status':'ok'}
    response=client.get('/')
    assert response.status_code == 200
    assert 'Register a parcel' in response.text
    assert client.get('/static/app.js').status_code == 200
