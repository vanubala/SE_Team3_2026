"""Development adapter for the compartment-door command port."""
import logging

logger = logging.getLogger(__name__)


class ConsoleDoorGateway:
    """Log a simulated unlock; replace with the locker hardware adapter."""

    def unlock_compartment(self, *, locker_id: str, compartment_id: str) -> None:
        logger.info(
            "[hardware-demo] UNLOCK locker=%s compartment=%s",
            locker_id,
            compartment_id,
        )
