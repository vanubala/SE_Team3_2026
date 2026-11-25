"""Schema contracts: §§1.1–1.5; independent relational constraint tests."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable, CreateIndex
from app.db.models import Base, User, Locker, Compartment, Parcel, PickupCode

EXPECTED={
 'users': 'user_id name email password_hash role company_name created_at',
 'lockers': 'locker_id name address gps_location opening_hours operational_status instructions',
 'compartments': 'compartment_id locker_id compartment_number size_category status version',
 'parcels': 'parcel_id tracking_number size_category status preferred_locker_id compartment_id registered_by_courier_id recipient_contact notes expected_delivery registered_at deposited_at pickup_deadline collected_at',
 'pickup_codes': 'code_id parcel_id code_hash failed_attempts locked_until issued_at expires_at used_at',
}

@pytest.fixture
def db():
    engine=create_engine('sqlite+pysqlite://')
    @event.listens_for(engine,'connect')
    def fk(conn,_): conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def user(**kw):
    return User(**({'name':'Test Courier','email':'courier@example.test','password_hash':'test-hash','role':'COURIER'}|kw))


def locker(**kw):
    return Locker(**({'name':'Station','address':'Demo address','gps_location':'49,6','opening_hours':'24/7'}|kw))


def setup_parcel(db):
    u,l=user(),locker(); db.add_all([u,l]); db.flush()
    c=Compartment(locker_id=l.locker_id,compartment_number=1,size_category='SMALL');db.add(c);db.flush()
    p=Parcel(parcel_id=uuid4(),tracking_number='TEST-1',size_category='SMALL',status='ASSIGNED',preferred_locker_id=l.locker_id,compartment_id=c.compartment_id,registered_by_courier_id=u.user_id,recipient_contact='guest@example.test');db.add(p);db.commit()
    return u,l,c,p


def test_exact_columns():
    assert set(Base.metadata.tables)==set(EXPECTED)
    for name,cols in EXPECTED.items():
        assert set(Base.metadata.tables[name].columns.keys())==set(cols.split())


def test_postgresql_ddl_compiles():
    dialect=postgresql.dialect()
    for t in Base.metadata.sorted_tables:
        ddl=str(CreateTable(t).compile(dialect=dialect))
        assert 'UUID' in ddl and 'PRIMARY KEY' in ddl
        for index in t.indexes: assert 'CREATE' in str(CreateIndex(index).compile(dialect=dialect))


def test_defaults(db):
    u,l,c,p=setup_parcel(db)
    assert u.created_at and l.operational_status=='ONLINE'
    assert c.status=='AVAILABLE' and c.version==0
    assert p.registered_at and p.pickup_deadline is None


def test_admin_can_load_compartments_in_physical_order(db):
    station = locker()
    db.add(station)
    db.flush()
    db.add_all([
        Compartment(locker_id=station.locker_id, compartment_number=number, size_category='SMALL')
        for number in (3, 1, 2)
    ])
    db.commit()
    db.expunge_all()

    overview = db.scalar(select(Locker).options(selectinload(Locker.compartments)))

    assert [box.compartment_number for box in overview.compartments] == [1, 2, 3]

@pytest.mark.parametrize('case',['duplicate_email','unknown_role','foreign_key','invalid_size','invalid_compartment_status','negative_version','duplicate_box_number','duplicate_tracking','invalid_parcel_status','active_compartment_collision','duplicate_code','negative_attempts'])
def test_invalid_records_rejected(db,case):
    u,l,c,p=setup_parcel(db)
    if case=='duplicate_email': db.add(user(email=u.email))
    elif case=='unknown_role': db.add(user(email='x@example.test',role='RECIPIENT'))
    elif case=='foreign_key': db.add(Compartment(locker_id=uuid4(),compartment_number=2,size_category='SMALL'))
    elif case=='invalid_size': c.size_category='HUGE'
    elif case=='invalid_compartment_status': c.status='WRONG'
    elif case=='negative_version': c.version=-1
    elif case=='duplicate_box_number': db.add(Compartment(locker_id=l.locker_id,compartment_number=1,size_category='LARGE'))
    elif case=='duplicate_tracking': db.add(Parcel(parcel_id=uuid4(),tracking_number=p.tracking_number,size_category='SMALL',status='REGISTERED',registered_by_courier_id=u.user_id,recipient_contact='a@example.test'))
    elif case=='invalid_parcel_status': p.status='WRONG'
    elif case=='active_compartment_collision': db.add(Parcel(parcel_id=uuid4(),tracking_number='TEST-2',size_category='SMALL',status='ASSIGNED',compartment_id=c.compartment_id,registered_by_courier_id=u.user_id,recipient_contact='a@example.test'))
    else:
        expires=datetime.now(timezone.utc)+timedelta(days=7)
        db.add(PickupCode(parcel_id=p.parcel_id,code_hash='hash',expires_at=expires,failed_attempts=-1 if case=='negative_attempts' else 0))
        if case=='duplicate_code': db.add(PickupCode(parcel_id=p.parcel_id,code_hash='hash2',expires_at=expires))
    with pytest.raises(IntegrityError): db.commit()
    db.rollback()


def test_compartment_can_be_reused_after_collection(db):
    u,l,c,p=setup_parcel(db); p.status='COLLECTED'; db.commit()
    db.add(Parcel(parcel_id=uuid4(),tracking_number='TEST-2',size_category='SMALL',status='ASSIGNED',compartment_id=c.compartment_id,registered_by_courier_id=u.user_id,recipient_contact='a@example.test'));db.commit()
    assert len(db.scalars(select(Parcel)).all())==2
