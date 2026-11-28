"""Saving and loading parcels."""
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Parcel, ParcelStatus


class ParcelRepository:
    def __init__(self, session: Session):
        self.session = session

    def exists_by_tracking_number(self, tracking_number: str) -> bool:
        query = select(Parcel.parcel_id).where(Parcel.tracking_number == tracking_number)
        return self.session.scalar(query) is not None

    def save(self, parcel: Parcel) -> bool:
        """Adds the parcel to the session. Returns False if a parcel with the same tracking number already exists.
        Raises the database error for any other failure."""
        self.session.add(parcel)
        try:
            self.session.flush()
        except IntegrityError:
            # After a failed INSERT, PostgreSQL rejects further queries until the transaction is rolled back.
            self.session.rollback()
            if self.exists_by_tracking_number(parcel.tracking_number):
                return False
            raise
        return True

    def find_by_id(self, parcel_id: UUID) -> Parcel | None:
        return self.session.get(Parcel, parcel_id)

    def find_by_courier(self, courier_id: UUID, status: str | None = None) -> list[Parcel]:
        from app.db.models import Compartment, Locker

        query = (
            select(Parcel, Compartment.compartment_number, Locker.locker_id, Locker.name)
            .outerjoin(Compartment, Parcel.compartment_id == Compartment.compartment_id)
            .outerjoin(
                Locker,
                Locker.locker_id == func.coalesce(Compartment.locker_id, Parcel.preferred_locker_id),
            )
            .where(Parcel.registered_by_courier_id == courier_id)
        )
        if status is not None:
            query = query.where(Parcel.status == status)

        rows = self.session.execute(
            query.order_by(Parcel.registered_at, Parcel.tracking_number)
        ).all()

        parcels: list[Parcel] = []
        for parcel, comp_num, resolved_locker_id, resolved_locker_name in rows:
            parcel.compartment_number = comp_num
            parcel.locker_name = resolved_locker_name
            if resolved_locker_id is not None:
                parcel.preferred_locker_id = resolved_locker_id
            parcels.append(parcel)
        return parcels

    def update_assignment(self, parcel_id: UUID, compartment_id: UUID) -> bool:
        # Only updates the parcel if it is still REGISTERED.
        result = self.session.execute(
            update(Parcel)
            .where(Parcel.parcel_id == parcel_id, Parcel.status == ParcelStatus.REGISTERED)
            .values(status=ParcelStatus.ASSIGNED, compartment_id=compartment_id)
            .execution_options(synchronize_session="fetch")
        )
        return result.rowcount == 1