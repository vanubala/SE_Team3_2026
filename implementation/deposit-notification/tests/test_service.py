from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from deposit_notification.contracts import (
    AssignedCompartment,
    DepositCommitResult,
    DepositConfirmationRequest,
    DepositUnlockRequest,
    IssuedPickupCode,
    TerminalContext,
)
from deposit_notification.service import (
    DepositConflict,
    DepositForbidden,
    DepositHardwareUnavailable,
    DepositService,
    PickupCodeCollision,
    PickupCodeUnavailable,
)


def result(*, already_processed=False):
    now = datetime.now(timezone.utc)
    return DepositCommitResult(
        already_processed=already_processed,
        parcel_id="parcel-1",
        locker_id="locker-1",
        compartment_id="compartment-1",
        compartment_number=7,
        recipient_contact="recipient@example.test",
        locker_address="1 Demo Street",
        locker_gps_location="49.5, 5.9",
        opening_hours="24/7",
        locker_instructions="Use the side entrance.",
        deposited_at=now,
        pickup_deadline=now + timedelta(days=7),
    )


class FakeRepository:
    def __init__(self, *, already_processed=False, collisions=0, error=None):
        self.already_processed = already_processed
        self.collisions = collisions
        self.error = error
        self.commit_count = 0
        self.rollback_count = 0
        self.confirm_calls = []

    def get_assigned_compartment(self, parcel_id, locker_id):
        return AssignedCompartment(parcel_id, locker_id, "compartment-1", 7)

    def confirm_assigned_deposit(self, **kwargs):
        self.confirm_calls.append(kwargs)
        if self.collisions:
            self.collisions -= 1
            raise PickupCodeCollision
        if self.error:
            raise self.error
        return result(already_processed=self.already_processed)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


class FakeIssuer:
    def __init__(self, count=5):
        self.issued = []
        for index in range(count):
            code = f"{index + 1:06d}"
            self.issued.append(IssuedPickupCode(uuid4(), code, f"hash-{index + 1}"))

    def issue(self):
        if not self.issued:
            raise AssertionError("The service requested more PINs than expected")
        return self.issued.pop(0)


class FakeDoor:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def unlock_compartment(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error


def service(repository=None, issuer=None, door=None):
    return DepositService(
        repository or FakeRepository(),
        issuer or FakeIssuer(),
        door or FakeDoor(),
    )


def confirmation(*, door_closed=True, parcel_detected=True):
    return DepositConfirmationRequest(
        parcelId="parcel-1",
        compartmentId="compartment-1",
        doorClosed=door_closed,
        parcelDetected=parcel_detected,
    )


def test_unlock_uses_assigned_compartment():
    repository, door = FakeRepository(), FakeDoor()

    response = service(repository, door=door).request_unlock(
        DepositUnlockRequest(lockerId="locker-1", parcelId="parcel-1"),
        TerminalContext(locker_id="locker-1"),
    )

    assert response.compartment_id == "compartment-1"
    assert door.calls == [{"locker_id": "locker-1", "compartment_id": "compartment-1"}]


def test_unlock_rejects_another_locker_before_opening_door():
    door = FakeDoor()

    with pytest.raises(DepositForbidden):
        service(door=door).request_unlock(
            DepositUnlockRequest(lockerId="other-locker", parcelId="parcel-1"),
            TerminalContext(locker_id="locker-1"),
        )

    assert door.calls == []


def test_unlock_reports_hardware_failure():
    with pytest.raises(DepositHardwareUnavailable):
        service(door=FakeDoor(error=OSError("device unavailable"))).request_unlock(
            DepositUnlockRequest(lockerId="locker-1", parcelId="parcel-1"),
            TerminalContext(locker_id="locker-1"),
        )


@pytest.mark.parametrize(
    "payload",
    [confirmation(door_closed=False), confirmation(parcel_detected=False)],
)
def test_confirmation_requires_closed_door_and_detected_parcel(payload):
    repository = FakeRepository()

    with pytest.raises(DepositConflict):
        service(repository).confirm_deposit(payload, TerminalContext("locker-1"))

    assert repository.confirm_calls == []
    assert repository.commit_count == 0


def test_successful_confirmation_commits_and_emits_pin_event():
    repository, issuer = FakeRepository(), FakeIssuer()

    outcome = service(repository, issuer).confirm_deposit(
        confirmation(), TerminalContext("locker-1")
    )

    assert outcome.response.status == "READY_FOR_PICKUP"
    assert outcome.response.notification_triggered is True
    assert outcome.event is not None
    assert outcome.event.pickup_code == "000001"
    assert repository.confirm_calls[0]["code_hash"] == "hash-1"
    assert repository.commit_count == 1
    assert repository.rollback_count == 0


def test_pin_collision_rolls_back_and_retries_with_a_new_code():
    repository, issuer = FakeRepository(collisions=1), FakeIssuer()

    outcome = service(repository, issuer).confirm_deposit(
        confirmation(), TerminalContext("locker-1")
    )

    assert len(repository.confirm_calls) == 2
    assert repository.confirm_calls[0]["code_hash"] == "hash-1"
    assert repository.confirm_calls[1]["code_hash"] == "hash-2"
    assert repository.rollback_count == 1
    assert repository.commit_count == 1
    assert outcome.event.pickup_code == "000002"


def test_exhausted_pin_collisions_return_unavailable_and_rollback():
    repository = FakeRepository(collisions=5)

    with pytest.raises(PickupCodeUnavailable):
        service(repository).confirm_deposit(
            confirmation(), TerminalContext("locker-1")
        )

    assert len(repository.confirm_calls) == 5
    assert repository.rollback_count == 5
    assert repository.commit_count == 0


def test_repository_failure_rolls_back_and_propagates():
    repository = FakeRepository(error=RuntimeError("database unavailable"))

    with pytest.raises(RuntimeError, match="database unavailable"):
        service(repository).confirm_deposit(
            confirmation(), TerminalContext("locker-1")
        )

    assert repository.rollback_count == 1
    assert repository.commit_count == 0


def test_repeated_confirmation_does_not_emit_another_notification():
    repository = FakeRepository(already_processed=True)

    outcome = service(repository).confirm_deposit(
        confirmation(), TerminalContext("locker-1")
    )

    assert outcome.event is None
    assert outcome.response.notification_triggered is False
    assert repository.commit_count == 1
