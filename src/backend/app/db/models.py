"""Shared SQLAlchemy mappings for Schemas-Endpoints.md §§1.1–1.5."""
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4
from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Index, Integer,
                        String, Text, UniqueConstraint, Uuid, func, text)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Role(StrEnum):
    COURIER = 'COURIER'
    ADMIN = 'ADMIN'


class SizeCategory(StrEnum):
    SMALL = 'SMALL'
    MEDIUM = 'MEDIUM'
    LARGE = 'LARGE'


class LockerStatus(StrEnum):
    ONLINE = 'ONLINE'
    OFFLINE = 'OFFLINE'
    MAINTENANCE = 'MAINTENANCE'


class CompartmentStatus(StrEnum):
    AVAILABLE = 'AVAILABLE'
    RESERVED = 'RESERVED'
    OCCUPIED = 'OCCUPIED'
    MAINTENANCE = 'MAINTENANCE'


class ParcelStatus(StrEnum):
    REGISTERED = 'REGISTERED'
    ASSIGNED = 'ASSIGNED'
    READY_FOR_PICKUP = 'READY_FOR_PICKUP'
    COLLECTED = 'COLLECTED'
    EXPIRED = 'EXPIRED'


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (CheckConstraint("role IN ('COURIER','ADMIN')", name='ck_users_role'),
                      Index('uq_users_email_lower', func.lower(text('email')), unique=True),)
    user_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    company_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Locker(Base):
    __tablename__ = 'lockers'
    __table_args__ = (CheckConstraint("operational_status IN ('ONLINE','OFFLINE','MAINTENANCE')", name='ck_lockers_status'),)
    locker_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    gps_location: Mapped[str] = mapped_column(String(100))
    opening_hours: Mapped[str] = mapped_column(String(100))
    operational_status: Mapped[str] = mapped_column(String(20), server_default='ONLINE')
    instructions: Mapped[str | None] = mapped_column(Text)
    compartments: Mapped[list["Compartment"]] = relationship(order_by='Compartment.compartment_number')


class Compartment(Base):
    __tablename__ = 'compartments'
    __table_args__ = (
        UniqueConstraint('locker_id', 'compartment_number', name='uq_compartments_locker_number'),
        CheckConstraint('compartment_number > 0', name='ck_compartments_number'),
        CheckConstraint("size_category IN ('SMALL','MEDIUM','LARGE')", name='ck_compartments_size'),
        CheckConstraint("status IN ('AVAILABLE','RESERVED','OCCUPIED','MAINTENANCE')", name='ck_compartments_status'),
        CheckConstraint('version >= 0', name='ck_compartments_version'),
        Index('ix_compartments_locker_status_size', 'locker_id', 'status', 'size_category'),
    )
    compartment_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    locker_id: Mapped[UUID] = mapped_column(ForeignKey('lockers.locker_id'))
    compartment_number: Mapped[int] = mapped_column(Integer)
    size_category: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), server_default='AVAILABLE')
    version: Mapped[int] = mapped_column(Integer, server_default=text('0'))


# A second active allocation for the same physical box must fail even if an
# application bug bypasses the row lock. Historical parcels may retain the ID.
ACTIVE_ALLOCATION = "compartment_id IS NOT NULL AND status IN ('ASSIGNED','READY_FOR_PICKUP')"


class Parcel(Base):
    __tablename__ = 'parcels'
    __table_args__ = (
        CheckConstraint("size_category IN ('SMALL','MEDIUM','LARGE')", name='ck_parcels_size'),
        CheckConstraint("status IN ('REGISTERED','ASSIGNED','READY_FOR_PICKUP','COLLECTED','EXPIRED')", name='ck_parcels_status'),
        Index('ix_parcels_courier_status', 'registered_by_courier_id', 'status'),
        Index('ix_parcels_preferred_locker_id', 'preferred_locker_id'),
        Index('ix_parcels_compartment_id', 'compartment_id'),
        Index('uq_parcels_active_compartment', 'compartment_id', unique=True,
              postgresql_where=text(ACTIVE_ALLOCATION), sqlite_where=text(ACTIVE_ALLOCATION)),
    )
    # RegistrationService owns the barcode-derived ID; intentionally no random default.
    parcel_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    tracking_number: Mapped[str] = mapped_column(String(100), unique=True)
    size_category: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30))
    preferred_locker_id: Mapped[UUID | None] = mapped_column(ForeignKey('lockers.locker_id'))
    compartment_id: Mapped[UUID | None] = mapped_column(ForeignKey('compartments.compartment_id'))
    registered_by_courier_id: Mapped[UUID] = mapped_column(ForeignKey('users.user_id'))
    recipient_contact: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    expected_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deposited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PickupCode(Base):
    __tablename__ = 'pickup_codes'
    __table_args__ = (CheckConstraint('failed_attempts >= 0', name='ck_pickup_codes_attempts'),)
    code_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    parcel_id: Mapped[UUID] = mapped_column(ForeignKey('parcels.parcel_id'), unique=True)
    code_hash: Mapped[str] = mapped_column(String(255))
    failed_attempts: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
