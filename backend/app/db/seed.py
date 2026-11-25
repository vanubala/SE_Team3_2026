"""Explicitly opt in to inserting synthetic demo data; safe to rerun."""
import argparse
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid5
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.db.models import User, Locker, Compartment, Parcel, Role, SizeCategory
from app.security.passwords import hash_password

NAMESPACE = UUID('84a16ee9-4133-4b14-b5ee-8d9e2256d6aa')


def demo_id(label: str) -> UUID:
    return uuid5(NAMESPACE, label)


COURIER_EMAIL = 'courier@example.test'
ADMIN_EMAIL = 'admin@example.test'


def seed_demo(db: Session, courier_password: str, admin_password: str) -> None:
    if min(len(courier_password), len(admin_password)) < 12 or courier_password == admin_password:
        raise ValueError('Provide two different demo passwords, at least 12 characters each')
    for key, name, email, password, role, company in (
        ('courier','Demo Courier',COURIER_EMAIL,courier_password,Role.COURIER,'Demo Carrier'),
        ('admin','Demo Administrator',ADMIN_EMAIL,admin_password,Role.ADMIN,None),
    ):
        uid = demo_id(key)
        existing = db.get(User, uid)
        if existing is None:
            if db.scalar(select(User).where(func.lower(User.email) == email)) is not None:
                raise ValueError(f'Demo account collision: {email}; no existing account overwritten')
            db.add(User(user_id=uid, name=name, email=email, password_hash=hash_password(password),
                        role=role.value, company_name=company))
    db.flush()
    for label, name in [('belval','Demo Belval Station'), ('kirchberg','Demo Kirchberg Station')]:
        lid = demo_id(label)
        if db.get(Locker,lid) is None:
            db.add(Locker(locker_id=lid,name=name,address='Synthetic demo address',
                          gps_location='49.60,6.10',opening_hours='24/7',instructions='Simulation only'))
        db.flush()
        for number,size in enumerate([SizeCategory.SMALL,SizeCategory.SMALL,SizeCategory.MEDIUM,
                                      SizeCategory.MEDIUM,SizeCategory.LARGE,SizeCategory.LARGE],1):
            cid=demo_id(f'{label}:{number}')
            if db.get(Compartment,cid) is None:
                db.add(Compartment(compartment_id=cid,locker_id=lid,compartment_number=number,size_category=size.value))
    db.flush()
    pid=demo_id('sample-parcel')
    if db.get(Parcel,pid) is None:
        db.add(Parcel(parcel_id=pid,tracking_number='DEMO-0001',size_category='MEDIUM',status='REGISTERED',
                      preferred_locker_id=demo_id('belval'),registered_by_courier_id=demo_id('courier'),
                      recipient_contact='recipient@example.test',notes='Synthetic demonstration parcel',
                      expected_delivery=datetime.now(timezone.utc)+timedelta(days=1)))
    db.flush()
    # No PickupCode seed: deposit generates one; never insert a live PIN or reset state.


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo',action='store_true',required=True,help='Confirm synthetic development data only')
    parser.parse_args()
    load_dotenv()
    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url
    url=os.getenv('DATABASE_URL')
    if not url or make_url(url).get_backend_name() != 'postgresql':
        parser.error('Set DATABASE_URL to your development PostgreSQL database')
    passwords=[os.getenv('DEMO_COURIER_PASSWORD',''),os.getenv('DEMO_ADMIN_PASSWORD','')]
    if any('replace-with' in p for p in passwords):
        parser.error('Replace demo password placeholders')
    engine=create_engine(url,pool_pre_ping=True)
    try:
        with Session(engine) as db, db.begin():
            seed_demo(db,*passwords)
        print('Demo records present. Accounts: courier@example.test, admin@example.test. Existing accounts and states were not reset.')
    finally:
        engine.dispose()


if __name__=='__main__':
    main()
