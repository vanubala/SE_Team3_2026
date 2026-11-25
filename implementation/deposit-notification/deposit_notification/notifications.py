"""Asynchronous notification handler and replaceable provider adapter."""
import asyncio
import logging

from .contracts import ParcelDeposited, PickupNotificationGateway

logger = logging.getLogger(__name__)


class ConsolePickupGateway:
    """Safe local stand-in; it never writes the pickup PIN to logs."""

    async def send_pickup_notification(
        self, *, destination: str, message: str, idempotency_key: str
    ) -> None:
        channel = "EMAIL" if "@" in destination else "SMS"
        # This adapter simulates delivery without persisting/logging message contents.
        logger.info(
            "[outbox-demo] simulated %s notification; recipient and message redacted",
            channel,
        )


class NotificationService:
    def __init__(
        self,
        gateway: PickupNotificationGateway,
        *,
        max_attempts: int = 3,
        retry_delay_seconds: float = 0.25,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        self._gateway = gateway
        self._max_attempts = max_attempts
        self._retry_delay_seconds = retry_delay_seconds

    async def handle_parcel_deposited(self, event: ParcelDeposited) -> None:
        message_parts = [
            "Your parcel is ready for pickup. "
            f"Pickup PIN: {event.pickup_code}. "
            f"Locker address: {event.locker_address}. "
            f"GPS location: {event.locker_gps_location}. "
            f"Compartment: {event.compartment_number}. "
            f"Opening hours: {event.opening_hours}. "
            f"Collect by: {event.pickup_deadline.isoformat()}."
        ]
        instructions = event.locker_instructions or "Follow the instructions shown at the locker."
        message_parts.append(f"Instructions: {instructions}")
        message = " ".join(message_parts)
        for attempt in range(1, self._max_attempts + 1):
            try:
                await self._gateway.send_pickup_notification(
                    destination=event.recipient_contact,
                    message=message,
                    idempotency_key=str(event.event_id),
                )
                return
            except Exception:
                logger.warning(
                    "Pickup notification delivery failed for event %s, attempt %d/%d",
                    event.event_id,
                    attempt,
                    self._max_attempts,
                )
                if attempt < self._max_attempts:
                    await asyncio.sleep(self._retry_delay_seconds * (2 ** (attempt - 1)))
        logger.error(
            "Pickup notification exhausted retries for event %s", event.event_id
        )
