from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.db.models import Compartment, Locker, Parcel
from app.services.assignment_service import AssignmentService
from app.services.parcel_errors import (
    CompartmentNotFound,
    CompartmentTaken,
    CompartmentTooSmall,
    InvalidParcelData,
    LockerNotFound,
    LockerUnavailable,
    NoCompartmentAvailable,
    ParcelNotFound,
    ParcelNotRegistered,
)
from app.services.registration_service import ParcelForm, RegistrationService
from register_assign.support import NAMESPACE, NOW, TOMORROW, add_locker, uid

COURIER = uid("courier-1")


def register(uow, tracking_number="LU-1", size="MEDIUM", courier_id=COURIER) -> UUID:
    form = ParcelForm(tracking_number, size, "recipient@example.lu", TOMORROW)
    return RegistrationService(uow, NAMESPACE, now=lambda: NOW).register_parcel(courier_id, form).parcel_id


@pytest.mark.parametrize("size, recommended, offered", [
    ("SMALL", "comp-01", ["comp-01", "comp-02", "comp-04", "comp-09"]),
    ("MEDIUM", "comp-04", ["comp-04", "comp-09"]),
    ("LARGE", "comp-09", ["comp-09"]),
])
def test_recommends_the_smallest_compartment_the_parcel_fits_in(uow, belval, size, recommended, offered):
    best, compartments = AssignmentService(uow).get_available_and_recommended_compartments(belval, size)

    assert best.compartment_id == uid(recommended)
    assert [c.compartment_id for c in compartments] == [uid(name) for name in offered]


def test_never_offers_reserved_occupied_or_maintenance_compartments(uow, session):
    add_locker(session, compartments=[
        ("comp-01", 1, "SMALL", "RESERVED"),
        ("comp-02", 2, "SMALL", "OCCUPIED"),
        ("comp-03", 3, "SMALL", "MAINTENANCE"),
    ])

    with pytest.raises(NoCompartmentAvailable):
        AssignmentService(uow).get_available_and_recommended_compartments(uid("loc-belval-01"), "SMALL")


def test_offers_nothing_at_a_locker_out_of_service(uow, session):
    add_locker(session, status="MAINTENANCE", compartments=[("comp-01", 1, "SMALL", "AVAILABLE")])

    with pytest.raises(LockerUnavailable):
        AssignmentService(uow).get_available_and_recommended_compartments(uid("loc-belval-01"), "SMALL")


def test_unknown_locker_and_unknown_size(uow, belval):
    with pytest.raises(LockerNotFound):
        AssignmentService(uow).get_available_and_recommended_compartments(uid("loc-nowhere"), "SMALL")
    with pytest.raises(InvalidParcelData):
        AssignmentService(uow).get_available_and_recommended_compartments(belval, "HUGE")


def test_assigns_the_parcel_and_reserves_the_compartment(uow, belval):
    parcel_id = register(uow)

    parcel, compartment = AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, uid("comp-04"))

    assert parcel.status == "ASSIGNED"
    assert parcel.compartment_id == uid("comp-04")
    saved = uow.lockers.find_compartment(uid("comp-04"))
    assert saved.status == "RESERVED"
    assert saved.version == 1


def test_a_larger_compartment_is_allowed(uow, belval):
    parcel_id = register(uow, size="SMALL")

    parcel, _ = AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, uid("comp-09"))

    assert parcel.status == "ASSIGNED"


def test_refuses_a_compartment_that_is_too_small_and_changes_nothing(uow, belval):
    parcel_id = register(uow, size="LARGE")

    with pytest.raises(CompartmentTooSmall):
        AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, uid("comp-04"))

    assert uow.parcels.find_by_id(parcel_id).status == "REGISTERED"
    assert uow.lockers.find_compartment(uid("comp-04")).status == "AVAILABLE"


def test_refuses_a_compartment_of_another_locker(uow, belval, session):
    add_locker(session, locker="loc-esch-02", compartments=[("comp-esch-1", 1, "MEDIUM", "AVAILABLE")])
    parcel_id = register(uow)

    with pytest.raises(CompartmentNotFound):
        AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, uid("comp-esch-1"))


def test_refuses_an_unknown_parcel_or_one_already_assigned(uow, belval):
    parcel_id = register(uow)
    AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, uid("comp-04"))

    with pytest.raises(ParcelNotFound):
        AssignmentService(uow).assign_compartment(COURIER, uid("no-such-parcel"), belval, uid("comp-09"))
    with pytest.raises(ParcelNotRegistered):
        AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, uid("comp-09"))


def test_a_courier_cannot_assign_a_parcel_registered_by_another_courier(uow, belval):
    parcel_id = register(uow, courier_id=uid("courier-2"))

    with pytest.raises(ParcelNotFound):
        AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, uid("comp-04"))

    assert uow.parcels.find_by_id(parcel_id).status == "REGISTERED"
    assert uow.lockers.find_compartment(uid("comp-04")).status == "AVAILABLE"


def test_two_parcels_cannot_get_the_same_compartment(uow, belval):
    first = register(uow, tracking_number="LU-1")
    second = register(uow, tracking_number="LU-2")
    AssignmentService(uow).assign_compartment(COURIER, first, belval, uid("comp-04"))

    with pytest.raises(CompartmentTaken):
        AssignmentService(uow).assign_compartment(COURIER, second, belval, uid("comp-04"))

    assert uow.parcels.find_by_id(second).status == "REGISTERED"


def test_compartment_taken_between_check_and_reservation():
    # Mocked storage: the compartment is taken after the check.
    parcel_id, locker_id, compartment_id = uid("p-1"), uid("loc-1"), uid("comp-1")
    uow = MagicMock()
    uow.parcels.find_by_id.return_value = Parcel(
        parcel_id=parcel_id, status="REGISTERED", size_category="SMALL", registered_by_courier_id=COURIER
    )
    uow.lockers.find_locker.return_value = Locker(locker_id=locker_id, operational_status="ONLINE")
    uow.lockers.find_compartment.return_value = Compartment(
        compartment_id=compartment_id, locker_id=locker_id, compartment_number=1, size_category="SMALL",
        status="AVAILABLE",
    )
    uow.lockers.reserve_compartment.return_value = False

    with pytest.raises(CompartmentTaken):
        AssignmentService(uow).assign_compartment(COURIER, parcel_id, locker_id, compartment_id)

    uow.lockers.reserve_compartment.assert_called_once_with(locker_id, compartment_id)
    uow.parcels.update_assignment.assert_not_called()
    uow.commit.assert_not_called()
    uow.rollback.assert_called_once()


def test_station_taken_out_of_service_between_check_and_reservation():
    parcel_id, locker_id, compartment_id = uid("p-1"), uid("loc-1"), uid("comp-1")
    uow = MagicMock()
    uow.parcels.find_by_id.return_value = Parcel(
        parcel_id=parcel_id, status="REGISTERED", size_category="SMALL", registered_by_courier_id=COURIER
    )
    uow.lockers.find_locker.side_effect = [
        Locker(locker_id=locker_id, operational_status="ONLINE"),
        Locker(locker_id=locker_id, operational_status="OFFLINE"),
    ]
    uow.lockers.find_compartment.return_value = Compartment(
        compartment_id=compartment_id, locker_id=locker_id, compartment_number=1, size_category="SMALL",
        status="AVAILABLE",
    )
    uow.lockers.reserve_compartment.return_value = False

    with pytest.raises(LockerUnavailable):
        AssignmentService(uow).assign_compartment(COURIER, parcel_id, locker_id, compartment_id)

    uow.commit.assert_not_called()
    uow.rollback.assert_called_once()


def test_parcel_assigned_elsewhere_in_the_meantime_undoes_the_reservation(uow, belval, monkeypatch):
    parcel_id = register(uow)
    monkeypatch.setattr(uow.parcels, "update_assignment", lambda parcel_id, compartment_id: False)

    with pytest.raises(ParcelNotRegistered):
        AssignmentService(uow).assign_compartment(COURIER, parcel_id, belval, uid("comp-04"))

    assert uow.lockers.find_compartment(uid("comp-04")).status == "AVAILABLE"
