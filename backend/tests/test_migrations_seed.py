"""Exercises the actual revision, not just metadata.create_all()."""
from pathlib import Path
from uuid import uuid4
import os
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select, func, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.engine import make_url
from app.db.models import User, Locker, Compartment, Parcel, PickupCode
from app.db.seed import seed_demo, demo_id
from app.security.passwords import verify_password

ROOT=Path(__file__).resolve().parents[1]
TABLES={'users','lockers','compartments','parcels','pickup_codes','alembic_version'}


def migrate(connection, direction='up'):
    config=Config(str(ROOT/'alembic.ini')); config.attributes['connection']=connection
    if direction=='up': command.upgrade(config,'head')
    else: command.downgrade(config,'base')


def check_migration_and_seed(engine):
    with engine.begin() as conn:
        migrate(conn)
        assert set(inspect(conn).get_table_names())==TABLES
    with Session(engine) as db:
        seed_demo(db,'courier-first-password','admin-first-password'); db.commit()
        assert [db.scalar(select(func.count()).select_from(model)) for model in (User,Locker,Compartment,Parcel,PickupCode)]==[2,2,12,1,0]
        courier=db.get(User,demo_id('courier')); original=courier.password_hash
        assert verify_password('courier-first-password', original)
        c=db.get(Compartment,demo_id('belval:1')); c.status='MAINTENANCE'; db.commit()
        seed_demo(db,'courier-other-password','admin-other-password'); db.commit()
        assert db.get(User,demo_id('courier')).password_hash==original
        assert db.get(Compartment,demo_id('belval:1')).status=='MAINTENANCE'
        assert db.scalar(select(func.count()).select_from(Parcel))==1
        # Case-insensitive uniqueness is required by our normalized login lookup.
        db.add(User(name='Duplicate',email='COURIER@EXAMPLE.TEST',password_hash='hash',role='COURIER'))
        with pytest.raises(IntegrityError): db.commit()
        db.rollback()
    with engine.begin() as conn:
        migrate(conn,'down')
        assert set(inspect(conn).get_table_names())=={'alembic_version'}
        migrate(conn)
        assert set(inspect(conn).get_table_names())==TABLES


def test_migration_and_seed_sqlite():
    engine=create_engine('sqlite+pysqlite://')
    try: check_migration_and_seed(engine)
    finally: engine.dispose()


def test_seed_rejects_unsafe_passwords():
    with pytest.raises(ValueError): seed_demo(None,'same-password','same-password')
    with pytest.raises(ValueError): seed_demo(None,'short','different-password')


@pytest.fixture
def postgres_engine():
    url=os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL for real PostgreSQL verification')
    if make_url(url).get_backend_name()!='postgresql':
        pytest.fail('TEST_DATABASE_URL must be PostgreSQL')
    # Isolated randomly named schema; do not modify existing application tables.
    schema='mvp_test_'+uuid4().hex
    admin=create_engine(url)
    engine=None
    try:
        with admin.begin() as conn: conn.execute(text(f'CREATE SCHEMA {schema}'))
        engine=create_engine(url,connect_args={'options':f'-csearch_path={schema}'})
        yield engine
    finally:
        if engine is not None: engine.dispose()
        with admin.begin() as conn: conn.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE'))
        admin.dispose()


@pytest.mark.postgres
def test_real_postgres_migration_seed(postgres_engine):
    check_migration_and_seed(postgres_engine)


@pytest.mark.postgres
def test_real_postgres_auth_and_constraints(postgres_engine):
    from app.config import Settings
    from app.main import create_app
    from app.security.dependencies import require_courier, require_admin
    from fastapi import Depends
    from fastapi.testclient import TestClient
    with postgres_engine.begin() as conn: migrate(conn)
    with Session(postgres_engine) as db:
        seed_demo(db,'courier-first-password','admin-first-password'); db.commit()
        assert db.get(User,demo_id('courier')).created_at.tzinfo is not None
        p=db.get(Parcel,demo_id('sample-parcel')); p.status='ASSIGNED'; p.compartment_id=demo_id('belval:1'); db.commit()
        db.add(Parcel(parcel_id=uuid4(),tracking_number='other-demo',size_category='SMALL',status='ASSIGNED',compartment_id=p.compartment_id,registered_by_courier_id=p.registered_by_courier_id,recipient_contact='guest@example.test'))
        with pytest.raises(IntegrityError): db.commit()
        db.rollback()
        db.add(Compartment(locker_id=uuid4(),compartment_number=99,size_category='SMALL'))
        with pytest.raises(IntegrityError): db.commit()
        db.rollback()
        compartment = db.get(Compartment, demo_id('belval:2'))
        compartment.status = 'INVALID'
        with pytest.raises(IntegrityError) as error:
            db.commit()
        assert error.value.orig.diag.constraint_name == 'ck_compartments_status'
        db.rollback()
    app=create_app(Settings(database_url=os.environ['TEST_DATABASE_URL'],jwt_secret='test-only-'+'a'*40),engine=postgres_engine)
    @app.get('/test/courier')
    def courier(user=Depends(require_courier)): return {'userId':str(user.user_id)}
    @app.get('/test/admin')
    def admin(user=Depends(require_admin)): return {'userId':str(user.user_id)}
    with TestClient(app) as client:
        for role in ('courier','admin'):
            result=client.post('/api/auth/login',json={'email':f'{role}@example.test','password':f'{role}-first-password'})
            assert result.status_code==200 and result.json()['user']['role']==role.upper()
            headers={'Authorization':'Bearer '+result.json()['token']}
            assert client.get('/test/'+role,headers=headers).status_code==200
            assert client.get('/test/'+('admin' if role=='courier' else 'courier'),headers=headers).status_code==403


@pytest.mark.postgres
def test_real_postgres_concurrent_allocations_cannot_double_book(postgres_engine):
    with postgres_engine.begin() as conn:
        migrate(conn)
    with Session(postgres_engine) as db, db.begin():
        seed_demo(db, 'courier-first-password', 'admin-first-password')

    def allocation(tracking_number):
        return Parcel(
            parcel_id=uuid4(), tracking_number=tracking_number, size_category='SMALL',
            status='ASSIGNED', compartment_id=demo_id('belval:1'),
            registered_by_courier_id=demo_id('courier'), recipient_contact='guest@example.test',
        )

    with Session(postgres_engine) as first, Session(postgres_engine) as second:
        first.add(allocation('CONCURRENT-1'))
        first.flush()
        second.execute(text("SET LOCAL lock_timeout = '500ms'"))
        second.add(allocation('CONCURRENT-2'))
        with pytest.raises(OperationalError) as timeout:
            second.flush()
        assert timeout.value.orig.sqlstate == '55P03'  # lock_not_available
        second.rollback()

        first.commit()
        second.add(allocation('CONCURRENT-2'))
        with pytest.raises(IntegrityError) as duplicate:
            second.flush()
        assert duplicate.value.orig.diag.constraint_name == 'uq_parcels_active_compartment'
        second.rollback()

        active = select(Parcel.tracking_number).where(Parcel.compartment_id == demo_id('belval:1'))
        assert second.scalars(active).all() == ['CONCURRENT-1']
