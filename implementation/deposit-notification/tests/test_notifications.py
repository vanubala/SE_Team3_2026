import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from deposit_notification.contracts import ParcelDeposited
from deposit_notification.notifications import NotificationService


def event():
    return ParcelDeposited(
        event_id=uuid4(),
        parcel_id="parcel-1",
        recipient_contact="recipient@example.test",
        pickup_code="012345",
        locker_address="1 Demo Street",
        locker_gps_location="49.5, 5.9",
        opening_hours="24/7",
        locker_instructions="Use the side entrance.",
        compartment_number=7,
        pickup_deadline=datetime(2030, 1, 1, tzinfo=timezone.utc),
    )


class RecordingGateway:
    def __init__(self, failures=0):
        self.failures = failures
        self.calls = []

    async def send_pickup_notification(self, **kwargs):
        self.calls.append(kwargs)
        if self.failures:
            self.failures -= 1
            raise RuntimeError("temporary provider failure")


def test_notification_contains_pickup_and_locker_details():
    gateway = RecordingGateway()

    asyncio.run(NotificationService(gateway).handle_parcel_deposited(event()))

    assert len(gateway.calls) == 1
    message = gateway.calls[0]["message"]
    for expected in (
        "012345",
        "1 Demo Street",
        "49.5, 5.9",
        "Compartment: 7",
        "24/7",
        "Use the side entrance.",
    ):
        assert expected in message


def test_notification_retries_transient_provider_failures():
    gateway = RecordingGateway(failures=2)

    asyncio.run(
        NotificationService(gateway, max_attempts=3, retry_delay_seconds=0)
        .handle_parcel_deposited(event())
    )

    assert len(gateway.calls) == 3
