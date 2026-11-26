"""SQLite demo stand-ins; replace these with the team's shared ORM models."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Locker(Base):
    __tablename__ = "lockers"

    locker_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    gps_location: Mapped[str] = mapped_column(String(100), nullable=False)
    opening_hours: Mapped[str] = mapped_column(String(100), nullable=False)
    operational_status: Mapped[str] = mapped_column(String(20), nullable=False)
    instructions: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Compartment(Base):
    __tablename__ = "compartments"

    compartment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    locker_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("lockers.locker_id"), nullable=False
    )
    compartment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    size_category: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Parcel(Base):
    __tablename__ = "parcels"

    parcel_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    compartment_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("compartments.compartment_id"), nullable=True
    )
    recipient_contact: Mapped[str] = mapped_column(String(255), nullable=False)
    deposited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pickup_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PickupCode(Base):
    __tablename__ = "pickup_codes"
    __table_args__ = (
        UniqueConstraint("code_hash", name="uq_pickup_codes_code_hash"),
    )

    code_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    parcel_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("parcels.parcel_id"), unique=True, nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
