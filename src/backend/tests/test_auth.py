"""Requirement-first oracles: FR_05, NFR_01, C0, A0; Schemas-Endpoints §2.1."""
from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import create_app
from app.db.session import get_db
from app.db.models import Role, User
from app.security.passwords import hash_password
from app.security.dependencies import require_role
from app.security.tokens import TokenService
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.db.models import Base

SECRET = 'test-only-' + 'a' * 40
PASSWORD = 'unit-test-password'
COURIER_ID = UUID('11111111-1111-4111-8111-111111111111')
ADMIN_ID = UUID('22222222-2222-4222-8222-222222222222')

@pytest.fixture(scope='module')
def encoded_password():
    return hash_password(PASSWORD)

@pytest.fixture
def settings():
    return Settings(database_url='sqlite+pysqlite://', jwt_secret=SECRET)

@pytest.fixture
def client(settings, encoded_password):
    engine = create_engine('sqlite+pysqlite://', poolclass=StaticPool,
                           connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([User(user_id=COURIER_ID, name='Courier', email='courier@example.test', password_hash=encoded_password, role='COURIER'),
                    User(user_id=ADMIN_ID, name='Admin', email='admin@example.test', password_hash=encoded_password, role='ADMIN')]); db.commit()
    app = create_app(settings, engine=engine)
    # Probe routes exist only inside the test application, not in the MVP API.
    @app.get('/test/courier')
    def courier(user=Depends(require_role(Role.COURIER))):
        return {'userId': str(user.user_id)}
    @app.get('/test/admin')
    def admin(user=Depends(require_role(Role.ADMIN))):
        return {'userId': str(user.user_id)}
    with TestClient(app) as c:
        yield c
    engine.dispose()


def login(client, email='courier@example.test', password=PASSWORD):
    return client.post('/api/auth/login', json={'email': email, 'password': password})

@pytest.mark.parametrize('email,role,uid', [('courier@example.test','COURIER',COURIER_ID), ('admin@example.test','ADMIN',ADMIN_ID)])
def test_login_contract(client, settings, email, role, uid):
    r=login(client,email)
    assert r.status_code==200
    b=r.json()
    assert set(b)=={'token','user'}
    assert set(b['user'])=={'userId','name','role'}
    assert b['user']['userId']==str(uid) and b['user']['role']==role
    claims=jwt.decode(b['token'],SECRET,algorithms=['HS256'],issuer=settings.jwt_issuer,audience=settings.jwt_audience)
    assert claims['sub']==str(uid) and claims['role']==role
    assert 0 < claims['exp']-claims['iat'] <= 1800
    assert r.headers['cache-control']=='no-store'

@pytest.mark.parametrize('email,password',[('courier@example.test','wrong'),('unknown@example.test',PASSWORD)])
def test_bad_credentials(client,email,password):
    r=login(client,email,password)
    assert r.status_code==401
    assert set(r.json())=={'timestamp','status','error','message'}
    assert r.json()['error']=='UNAUTHORIZED'
    assert r.json()['message']=='Invalid credentials'
    assert r.headers['www-authenticate']=='Bearer'

@pytest.mark.parametrize('payload',[{}, {'email':'x','password':PASSWORD},{'email':'courier@example.test','password':''},{'email':'courier@example.test','password':PASSWORD,'role':'ADMIN'},{'email':'a'*256+'@x.test','password':PASSWORD}])
def test_malformed_payload(client,payload):
    r=client.post('/api/auth/login',json=payload)
    assert r.status_code==400
    assert set(r.json())=={'timestamp','status','error','message'}
    assert PASSWORD not in r.text

@pytest.mark.parametrize('email,own,other',[('courier@example.test','courier','admin'),('admin@example.test','admin','courier')])
def test_rbac_matrix(client,email,own,other):
    token=login(client,email).json()['token']; headers={'Authorization':f'Bearer {token}'}
    assert client.get(f'/test/{own}',headers=headers).status_code==200
    r=client.get(f'/test/{other}',headers=headers)
    assert r.status_code==403 and r.json()['error']=='FORBIDDEN'

@pytest.mark.parametrize('header',[None,'Basic abc','Bearer garbage','Bearer'])
def test_missing_or_bad_token(client,header):
    r=client.get('/test/courier',headers={'Authorization':header} if header else {})
    assert r.status_code==401 and r.headers['www-authenticate']=='Bearer'

@pytest.mark.parametrize('mutation',['expired','signature','role','issuer','audience','missing_exp','future_iat','bad_sub','none'])
def test_invalid_claims(client,settings,mutation):
    now=datetime.now(timezone.utc)
    claims={'sub':str(COURIER_ID),'role':'COURIER','iss':settings.jwt_issuer,'aud':settings.jwt_audience,'iat':now,'exp':now+timedelta(minutes=5)}
    secret=SECRET; algorithm='HS256'
    if mutation=='expired': claims['exp']=now-timedelta(seconds=1)
    elif mutation=='signature': secret='z'*48
    elif mutation=='role': claims['role']='RECIPIENT'
    elif mutation=='issuer': claims['iss']='other'
    elif mutation=='audience': claims['aud']='other'
    elif mutation=='missing_exp': del claims['exp']
    elif mutation=='future_iat': claims['iat']=now+timedelta(minutes=1)
    elif mutation=='bad_sub': claims['sub']='not-a-uuid'
    elif mutation=='none': algorithm='none'; secret=''
    token=jwt.encode(claims,secret,algorithm=algorithm)
    assert client.get('/test/courier',headers={'Authorization':f'Bearer {token}'}).status_code==401


def test_changed_role_claim_invalidates_token(client, settings):
    courier_token = login(client).json()['token']
    header, _, signature = courier_token.split('.')
    admin_payload = TokenService(settings).issue(COURIER_ID, Role.ADMIN).split('.')[1]
    changed_token = '.'.join((header, admin_payload, signature))

    response = client.get('/test/admin', headers={'Authorization': f'Bearer {changed_token}'})

    assert response.status_code == 401
    assert response.json()['error'] == 'UNAUTHORIZED'


def test_email_normalization(client):
    assert login(client,' COURIER@EXAMPLE.TEST ').status_code==200


def test_password_hash_is_salted():
    from app.security.passwords import verify_password
    a,b=hash_password(PASSWORD),hash_password(PASSWORD)
    assert a!=b and a.startswith('$argon2id$')
    assert verify_password(PASSWORD,a)
    assert not verify_password('wrong',a)
    assert not verify_password(PASSWORD,'invalid hash')
