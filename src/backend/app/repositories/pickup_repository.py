"""Data access for guest pickup (UC4). The service decides when to commit."""
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session
from app.db.models import (Compartment, Locker, Parcel, ParcelStatus, PickupCode,
                           TerminalLockout)


class PickupRepository:
    def __init__(self, db: Session):
        self.db = db

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def find_locker(self, locker_id: UUID) -> Locker | None:
        return self.db.get(Locker, locker_id)

    def lock_terminal_state(self, locker_id: UUID) -> TerminalLockout:
        """Return the locker's lockout row, holding a row lock until commit.

        The lock serialises PIN attempts at one terminal, so parallel guesses
        cannot all slip in under the 5-attempt limit.
        """
        insert = postgresql.insert if self.db.get_bind().dialect.name == 'postgresql' else sqlite.insert
        self.db.execute(insert(TerminalLockout).values(locker_id=locker_id, failed_attempts=0)
                        .on_conflict_do_nothing(index_elements=['locker_id']))
        return self.db.scalars(select(TerminalLockout).where(TerminalLockout.locker_id == locker_id)
                               .with_for_update()
                               .execution_options(populate_existing=True)).one()

    def find_active_code(self, locker_id: UUID, code_hash: str, now: datetime
                         ) -> tuple[PickupCode, Parcel, Compartment] | None:
        row = self.db.execute(
            select(PickupCode, Parcel, Compartment)
            .join(Parcel, Parcel.parcel_id == PickupCode.parcel_id)
            .join(Compartment, Compartment.compartment_id == Parcel.compartment_id)
            .where(Compartment.locker_id == locker_id,
                   PickupCode.code_hash == code_hash,
                   PickupCode.used_at.is_(None),
                   PickupCode.expires_at > now,
                   Parcel.status == ParcelStatus.READY_FOR_PICKUP)
        ).first()
        return None if row is None else (row[0], row[1], row[2])

    def lock_parcel(self, parcel_id: UUID) -> Parcel | None:
        return self.db.scalars(select(Parcel).where(Parcel.parcel_id == parcel_id)
                               .with_for_update().execution_options(populate_existing=True)).first()

    def lock_code_for_parcel(self, parcel_id: UUID) -> PickupCode | None:
        return self.db.scalars(select(PickupCode).where(PickupCode.parcel_id == parcel_id)
                               .with_for_update().execution_options(populate_existing=True)).first()

    def lock_compartment(self, compartment_id: UUID) -> Compartment | None:
        return self.db.scalars(select(Compartment).where(Compartment.compartment_id == compartment_id)
                               .with_for_update().execution_options(populate_existing=True)).first()
