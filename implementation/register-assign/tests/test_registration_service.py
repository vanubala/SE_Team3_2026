from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from app.errors import DuplicateTrackingNumber, InvalidParcelData, StorageError
from app.services.registration_service import ParcelForm, RegistrationService
from tests.conftest import NAMESPACE, NOW, TOMORROW, add_locker, uid

COURIER_1 = uid("courier-1")
COURIER_2 = uid("courier-2")


def service(uow) -> RegistrationService:
    return RegistrationService(uow, NAMESPACE, now=lambda: NOW)


def form(**changes) -> ParcelForm:
    values = dict(
        tracking_number="LU-987654321",
        size_category="MEDIUM",
        recipient_contact="recipient@example.lu",
        expected_delivery=TOMORROW,
        preferred_locker_id=None,
        notes=None,
    )
    values.update(changes)
    return ParcelForm(**values)


def test_registers_a_valid_parcel_as_registered_without_pickup_deadline(uow):
    parcel = service(uow).register_parcel(COURIER_1, form())

    saved = uow.parcels.find_by_id(parcel.parcel_id)
    assert saved.status == "REGISTERED"
    assert saved.tracking_number == "LU-987654321"
    assert saved.registered_by_courier_id == COURIER_1
    assert saved.registered_at.replace(tzinfo=NOW.tzinfo) == NOW
    assert saved.pickup_deadline is None


def test_rejects_a_tracking_number_that_is_already_registered(uow):
    service(uow).register_parcel(COURIER_1, form())

    with pytest.raises(DuplicateTrackingNumber):
        service(uow).register_parcel(COURIER_2, form(size_category="SMALL"))


@pytest.mark.parametrize("tracking_number, accepted", [
    ("ab", False),          # 2 characters: just below the minimum
    ("abc", True),          # 3: the minimum
    ("a" * 64, True),       # 64: the maximum
    ("a" * 65, False),      # 65: just above the maximum
    ("-abc", False),        # must start with a letter or digit
    ("LU 123", False),      # no spaces inside
])
def test_tracking_number_length_and_characters(uow, tracking_number, accepted):
    if accepted:
        assert service(uow).register_parcel(COURIER_1, form(tracking_number=tracking_number))
    else:
        with pytest.raises(InvalidParcelData):
            service(uow).register_parcel(COURIER_1, form(tracking_number=tracking_number))


@pytest.mark.parametrize("size, saved", [("small", "SMALL"), (" MEDIUM ", "MEDIUM"), ("LARGE", "LARGE")])
def test_accepts_the_three_sizes_in_any_case(uow, size, saved):
    parcel = service(uow).register_parcel(COURIER_1, form(size_category=size))

    assert parcel.size_category == saved


def test_rejects_an_unknown_size(uow):
    with pytest.raises(InvalidParcelData):
        service(uow).register_parcel(COURIER_1, form(size_category="XL"))


@pytest.mark.parametrize("contact, stored", [
    ("recipient@example.lu", "recipient@example.lu"),
    ("+352 621 123 456", "+352621123456"),
    ("+33612345678", "+33612345678"),
])
def test_accepts_an_email_address_or_a_phone_number(uow, contact, stored):
    parcel = service(uow).register_parcel(COURIER_1, form(recipient_contact=contact))

    assert parcel.recipient_contact == stored


@pytest.mark.parametrize("contact", [
    "", "recipient@", "@example.lu", "call me",
    "621123456", "00352621123456", "+0352621123456", "+12345",  # no "+" and country code, or too short
])
def test_rejects_a_contact_that_is_neither(uow, contact):
    with pytest.raises(InvalidParcelData):
        service(uow).register_parcel(COURIER_1, form(recipient_contact=contact))


@pytest.mark.parametrize("length, accepted", [
    (254, True),    # the longest email address that can be delivered
    (255, False),   # one more
])
def test_recipient_contact_length(uow, length, accepted):
    domain = "@example.lu"
    contact = "r" * (length - len(domain)) + domain
    if accepted:
        assert service(uow).register_parcel(COURIER_1, form(recipient_contact=contact))
    else:
        with pytest.raises(InvalidParcelData):
            service(uow).register_parcel(COURIER_1, form(recipient_contact=contact))


@pytest.mark.parametrize("delivery, accepted", [
    (NOW - timedelta(seconds=1), False),
    (NOW, False),
    (NOW + timedelta(seconds=1), True),
])
def test_expected_delivery_must_be_after_now(uow, delivery, accepted):
    if accepted:
        assert service(uow).register_parcel(COURIER_1, form(expected_delivery=delivery))
    else:
        with pytest.raises(InvalidParcelData):
            service(uow).register_parcel(COURIER_1, form(expected_delivery=delivery))


def test_rejects_an_expected_delivery_without_time_zone(uow):
    with pytest.raises(InvalidParcelData):
        service(uow).register_parcel(COURIER_1, form(expected_delivery=datetime(2026, 12, 1, 14, 0)))


def test_keeps_an_existing_preferred_locker(uow, session):
    add_locker(session, locker="loc-belval-01")

    parcel = service(uow).register_parcel(COURIER_1, form(preferred_locker_id=uid("loc-belval-01")))

    assert parcel.preferred_locker_id == uid("loc-belval-01")


def test_rejects_a_preferred_locker_that_does_not_exist(uow):
    with pytest.raises(InvalidParcelData):
        service(uow).register_parcel(COURIER_1, form(preferred_locker_id=uid("loc-nowhere")))


def test_cleans_notes_and_limits_their_length(uow):
    cleaned = service(uow).register_parcel(COURIER_1, form(tracking_number="LU-1", notes="  Fragile\x00 \n"))
    at_limit = service(uow).register_parcel(COURIER_1, form(tracking_number="LU-2", notes="x" * 500))

    assert cleaned.notes == "Fragile"
    assert len(at_limit.notes) == 500
    with pytest.raises(InvalidParcelData):
        service(uow).register_parcel(COURIER_1, form(tracking_number="LU-3", notes="x" * 501))


def test_lists_only_the_couriers_own_parcels_and_filters_by_status(uow):
    service(uow).register_parcel(COURIER_1, form(tracking_number="LU-1"))
    service(uow).register_parcel(COURIER_1, form(tracking_number="LU-2"))
    service(uow).register_parcel(COURIER_2, form(tracking_number="LU-3"))

    mine = service(uow).list_parcels(COURIER_1, "REGISTERED")
    assigned = service(uow).list_parcels(COURIER_1, "ASSIGNED")

    assert [p.tracking_number for p in mine] == ["LU-1", "LU-2"]
    assert assigned == []
    with pytest.raises(InvalidParcelData):
        service(uow).list_parcels(COURIER_1, "LOST")


def test_two_requests_saving_the_same_tracking_number_give_one_duplicate(uow, monkeypatch):
    service(uow).register_parcel(COURIER_1, form())
    answers = iter([False, True])  # the second request checked before the first one had saved
    monkeypatch.setattr(uow.parcels, "exists_by_tracking_number", lambda tracking_number: next(answers))

    with pytest.raises(DuplicateTrackingNumber):
        service(uow).register_parcel(COURIER_2, form())


@pytest.mark.parametrize("failure", [
    pytest.param(IntegrityError("INSERT INTO parcels", {}, Exception("foreign key")), id="other-constraint"),
    pytest.param(OperationalError("INSERT INTO parcels", {}, Exception("connection lost")), id="database-down"),
])
def test_a_database_failure_while_saving_is_a_storage_error(uow, monkeypatch, failure):
    real_flush = uow.session.flush
    failures = [failure]

    def flush_failing_once(*args, **kwargs):
        if uow.session.new and failures:  # only the flush that inserts the new parcel fails
            raise failures.pop()
        return real_flush(*args, **kwargs)

    monkeypatch.setattr(uow.session, "flush", flush_failing_once)

    with pytest.raises(StorageError):
        service(uow).register_parcel(COURIER_1, form())

    assert not uow.parcels.exists_by_tracking_number("LU-987654321")
