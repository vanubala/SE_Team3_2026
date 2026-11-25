"""Tables from Schemas-Endpoints.md section 1."""
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SizeCategory(StrEnum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class ParcelStatus(StrEnum):
    REGISTERED = "REGISTERED"
    ASSIGNED = "ASSIGNED"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    COLLECTED = "COLLECTED"
    EXPIRED = "EXPIRED"


class CompartmentStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"


class LockerStatus(StrEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


class Base(DeclarativeBase):
    pass


class Locker(Base):
    __tablename__ = "lockers"

    locker_id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    gps_location: Mapped[str] = mapped_column(String(100))
    opening_hours: Mapped[str] = mapped_column(String(100))
    operational_status: Mapped[str] = mapped_column(String(20), default=LockerStatus.ONLINE)
    instructions: Mapped[str | None] = mapped_column(Text)


class Compartment(Base):
    __tablename__ = "compartments"
    __table_args__ = (UniqueConstraint("locker_id", "compartment_number"),)

    compartment_id: Mapped[UUID] = mapped_column(primary_key=True)
    locker_id: Mapped[UUID] = mapped_column(ForeignKey("lockers.locker_id"))
    compartment_number: Mapped[int] = mapped_column(Integer)
    size_category: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default=CompartmentStatus.AVAILABLE)
    version: Mapped[int] = mapped_column(Integer, default=0)


class Parcel(Base):
    __tablename__ = "parcels"

    parcel_id: Mapped[UUID] = mapped_column(primary_key=True)
    tracking_number: Mapped[str] = mapped_column(String(100), unique=True)
    size_category: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30))
    preferred_locker_id: Mapped[UUID | None] = mapped_column(ForeignKey("lockers.locker_id"))
    compartment_id: Mapped[UUID | None] = mapped_column(ForeignKey("compartments.compartment_id"))
    registered_by_courier_id: Mapped[UUID] = mapped_column(index=True)
    recipient_contact: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    expected_delivery: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deposited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
