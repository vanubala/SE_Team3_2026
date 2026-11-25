"""Tables used by this module, following Schemas-Endpoints.md sections 1.2 to 1.4.

The shared schema and its migrations belong to the database module. At
integration, replace these classes with the shared ones. `Parcel` maps only the
columns needed here: this module reads parcels and never writes them.
"""
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class LockerStatus(StrEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


class CompartmentStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"


class SizeCategory(StrEnum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


# Parcels that hold a compartment. An EXPIRED parcel stays inside its
# compartment until a courier retrieves it.
ACTIVE_PARCEL_STATUSES = ("ASSIGNED", "READY_FOR_PICKUP", "EXPIRED")


class Base(DeclarativeBase):
    pass


class Locker(Base):
    __tablename__ = "lockers"

    locker_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))
    address: Mapped[str] = mapped_column(String(255))
    gps_location: Mapped[str] = mapped_column(String(100))
    opening_hours: Mapped[str] = mapped_column(String(100))
    operational_status: Mapped[str] = mapped_column(String(20), default=LockerStatus.ONLINE.value)
    instructions: Mapped[str | None] = mapped_column(Text)

    compartments: Mapped[list["Compartment"]] = relationship(
        order_by="Compartment.compartment_number"
    )


class Compartment(Base):
    __tablename__ = "compartments"
    __table_args__ = (UniqueConstraint("locker_id", "compartment_number"),)

    compartment_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    locker_id: Mapped[UUID] = mapped_column(ForeignKey("lockers.locker_id"), index=True)
    compartment_number: Mapped[int]
    size_category: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default=CompartmentStatus.AVAILABLE.value)
    version: Mapped[int] = mapped_column(default=0)


class Parcel(Base):
    __tablename__ = "parcels"

    parcel_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(String(30))
    compartment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("compartments.compartment_id"), index=True
    )
