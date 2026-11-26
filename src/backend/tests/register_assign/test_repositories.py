"""Repository tests on the database."""
from app.db.models import Parcel
from register_assign.support import NOW, add_locker, uid


def add_parcel(session, parcel="p-1", status="REGISTERED", courier="courier-1", tracking_number="LU-1"):
    session.add(Parcel(
        parcel_id=uid(parcel), tracking_number=tracking_number, size_category="SMALL", status=status,
        registered_by_courier_id=uid(courier), recipient_contact="recipient@example.lu", registered_at=NOW,
    ))
    session.commit()


def test_reserve_changes_an_available_compartment_once(uow, belval):
    assert uow.lockers.reserve_compartment(belval, uid("comp-04")) is True
    assert uow.lockers.reserve_compartment(belval, uid("comp-04")) is False
    assert uow.lockers.reserve_compartment(belval, uid("comp-03")) is False  # already RESERVED in the fixture
    assert uow.lockers.reserve_compartment(belval, uid("no-such-compartment")) is False


def test_reserve_refuses_a_station_out_of_service_or_a_compartment_of_another_station(uow, session):
    add_locker(session, locker="loc-offline", status="OFFLINE", compartments=[("comp-off", 1, "SMALL", "AVAILABLE")])
    add_locker(session, locker="loc-online", compartments=[("comp-on", 1, "SMALL", "AVAILABLE")])

    assert uow.lockers.reserve_compartment(uid("loc-offline"), uid("comp-off")) is False
    assert uow.lockers.reserve_compartment(uid("loc-online"), uid("comp-off")) is False
    assert uow.lockers.reserve_compartment(uid("loc-nowhere"), uid("comp-on")) is False
    assert uow.lockers.find_compartment(uid("comp-off")).status == "AVAILABLE"
    assert uow.lockers.find_compartment(uid("comp-on")).status == "AVAILABLE"


def test_update_assignment_only_moves_a_registered_parcel(uow, belval, session):
    add_parcel(session, "p-1", status="REGISTERED", tracking_number="LU-1")
    add_parcel(session, "p-2", status="ASSIGNED", tracking_number="LU-2")

    assert uow.parcels.update_assignment(uid("p-1"), uid("comp-04")) is True
    assert uow.parcels.update_assignment(uid("p-1"), uid("comp-09")) is False  # now ASSIGNED
    assert uow.parcels.update_assignment(uid("p-2"), uid("comp-09")) is False
    assert uow.parcels.update_assignment(uid("no-such-parcel"), uid("comp-09")) is False
    assert uow.parcels.find_by_id(uid("p-1")).compartment_id == uid("comp-04")


def test_find_available_compartments_keeps_only_available_ones_of_the_sizes_asked(uow, belval):
    found = uow.lockers.find_available_compartments(belval, ["MEDIUM", "LARGE"])

    assert {c.compartment_id for c in found} == {uid("comp-04"), uid("comp-09")}


def test_find_by_courier_filters_by_courier_and_status(uow, session):
    add_parcel(session, "p-1", courier="courier-1", tracking_number="LU-1")
    add_parcel(session, "p-2", courier="courier-2", tracking_number="LU-2")
    add_parcel(session, "p-3", courier="courier-1", status="ASSIGNED", tracking_number="LU-3")

    assert [p.parcel_id for p in uow.parcels.find_by_courier(uid("courier-1"))] == [uid("p-1"), uid("p-3")]
    assert [p.parcel_id for p in uow.parcels.find_by_courier(uid("courier-1"), "ASSIGNED")] == [uid("p-3")]
