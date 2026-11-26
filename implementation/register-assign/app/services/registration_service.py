"""Parcel registration (UC1, FR_02, FR_03)."""
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from ..database import UnitOfWork
from ..errors import DuplicateTrackingNumber, InvalidParcelData
from ..models import Parcel, ParcelStatus
from .sizes import parse_size

TRACKING_NUMBER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{2,63}")
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
# International format (E.164): "+", then the country code and number. The SMS sender of the deposit module
# only accepts this format.
PHONE = re.compile(r"\+[1-9][0-9]{7,14}")
CONTACT_MAX_LENGTH = 254  # longest email address that can be delivered (RFC 5321); the column holds 255
NOTES_MAX_LENGTH = 500


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class ParcelForm:
    tracking_number: str
    size_category: str
    recipient_contact: str
    expected_delivery: datetime
    preferred_locker_id: uuid.UUID | None = None
    notes: str | None = None


class RegistrationService:
    def __init__(self, uow: UnitOfWork, parcel_id_namespace: uuid.UUID, now: Callable[[], datetime] = utc_now):
        self.uow = uow
        self.parcel_id_namespace = parcel_id_namespace
        self.now = now

    def register_parcel(self, courier_id: uuid.UUID, form: ParcelForm) -> Parcel:
        """Validates the form and saves the parcel with status REGISTERED. The pickup deadline is left empty;
        the deposit module sets it. Returns the parcel.
        Raises InvalidParcelData, DuplicateTrackingNumber or StorageError. Nothing is saved when an error is raised."""
        form = self.sanitize_and_validate(form)
        if self.uow.parcels.exists_by_tracking_number(form.tracking_number):
            raise DuplicateTrackingNumber("A parcel with this tracking number is already registered")
        parcel = Parcel(
            parcel_id=self.generate_hashed_parcel_id(form.tracking_number),
            tracking_number=form.tracking_number,
            size_category=form.size_category,
            status=ParcelStatus.REGISTERED,
            preferred_locker_id=form.preferred_locker_id,
            registered_by_courier_id=courier_id,
            recipient_contact=form.recipient_contact,
            notes=form.notes,
            expected_delivery=form.expected_delivery,
            registered_at=self.now(),
        )
        try:
            self.uow.parcels.save(parcel)
            self.uow.commit()
        except Exception:
            self.uow.rollback()
            raise
        return parcel

    def list_parcels(self, courier_id: uuid.UUID, status: str | None = None) -> list[Parcel]:
        """Returns the parcels registered by this courier, oldest first, optionally filtered by status.
        Raises InvalidParcelData for an unknown status."""
        if status is not None and status not in tuple(ParcelStatus):
            raise InvalidParcelData(f"Status must be one of {', '.join(ParcelStatus)}")
        return self.uow.parcels.find_by_courier(courier_id, status)

    def sanitize_and_validate(self, form: ParcelForm) -> ParcelForm:
        """Checks the form and returns it with trimmed values. Raises InvalidParcelData."""
        tracking_number = form.tracking_number.strip()
        if not TRACKING_NUMBER.fullmatch(tracking_number):
            raise InvalidParcelData("Tracking number must have 3 to 64 letters, digits, '-' or '_'")

        size = parse_size(form.size_category)

        contact = form.recipient_contact.strip()
        if len(contact) > CONTACT_MAX_LENGTH:
            raise InvalidParcelData(f"Recipient contact must have at most {CONTACT_MAX_LENGTH} characters")
        if "@" in contact:
            if not EMAIL.fullmatch(contact):
                raise InvalidParcelData("Recipient contact is not a valid email address")
        else:
            contact = contact.replace(" ", "")
            if not PHONE.fullmatch(contact):
                raise InvalidParcelData(
                    "Recipient contact must be an email address or a phone number with country code, "
                    "such as +352621123456"
                )

        if form.expected_delivery.tzinfo is None:
            raise InvalidParcelData("Expected delivery must include a time zone")
        if form.expected_delivery <= self.now():
            raise InvalidParcelData("Expected delivery must be in the future")

        locker_id = form.preferred_locker_id
        if locker_id is not None and self.uow.lockers.find_locker(locker_id) is None:
            raise InvalidParcelData("Preferred locker does not exist")

        notes = None
        if form.notes is not None:
            notes = "".join(ch for ch in form.notes if ch in "\t\n" or ord(ch) >= 32).strip() or None
        if notes is not None and len(notes) > NOTES_MAX_LENGTH:
            raise InvalidParcelData(f"Notes must have at most {NOTES_MAX_LENGTH} characters")

        return ParcelForm(
            tracking_number=tracking_number,
            size_category=size,
            recipient_contact=contact,
            expected_delivery=form.expected_delivery.astimezone(UTC),
            preferred_locker_id=locker_id,
            notes=notes,
        )

    def generate_hashed_parcel_id(self, tracking_number: str) -> uuid.UUID:
        # uuid5 with a secret namespace: the same tracking number gives the same ID, but the ID cannot be guessed.
        return uuid.uuid5(self.parcel_id_namespace, tracking_number)
