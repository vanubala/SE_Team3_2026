"""Twilio SMS and SendGrid email adapter for pickup notifications."""
import os
import re
from urllib.parse import quote

import httpx

from .notifications import ConsolePickupGateway


class NotificationProviderError(RuntimeError):
    """A configured provider rejected a notification request."""


class TwilioSendGridGateway:
    """Send phone contacts through Twilio and email contacts through SendGrid."""

    def __init__(
        self,
        *,
        twilio_account_sid: str,
        twilio_api_key_sid: str,
        twilio_api_key_secret: str,
        sendgrid_api_key: str,
        sendgrid_from_email: str,
        twilio_from_number: str | None = None,
        twilio_messaging_service_sid: str | None = None,
        sendgrid_api_base_url: str = "https://api.sendgrid.com",
        timeout_seconds: float = 10.0,
    ) -> None:
        self._account_sid = twilio_account_sid.strip()
        self._twilio_api_key_sid = twilio_api_key_sid.strip()
        self._twilio_api_key_secret = twilio_api_key_secret.strip()
        self._sendgrid_api_key = sendgrid_api_key.strip()
        self._sendgrid_from_email = sendgrid_from_email.strip()
        self._twilio_from_number = (twilio_from_number or "").strip()
        self._twilio_messaging_service_sid = (
            twilio_messaging_service_sid or ""
        ).strip()
        self._sendgrid_api_base_url = sendgrid_api_base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

        required = {
            "TWILIO_ACCOUNT_SID": self._account_sid,
            "TWILIO_API_KEY_SID": self._twilio_api_key_sid,
            "TWILIO_API_KEY_SECRET": self._twilio_api_key_secret,
            "SENDGRID_API_KEY": self._sendgrid_api_key,
            "SENDGRID_FROM_EMAIL": self._sendgrid_from_email,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError("Missing notification settings: " + ", ".join(missing))
        if not (self._twilio_from_number or self._twilio_messaging_service_sid):
            raise ValueError(
                "Set TWILIO_FROM_NUMBER or TWILIO_MESSAGING_SERVICE_SID"
            )
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @classmethod
    def from_environment(cls) -> "TwilioSendGridGateway":
        return cls(
            twilio_account_sid=os.environ.get("TWILIO_ACCOUNT_SID", ""),
            twilio_api_key_sid=os.environ.get("TWILIO_API_KEY_SID", ""),
            twilio_api_key_secret=os.environ.get("TWILIO_API_KEY_SECRET", ""),
            twilio_from_number=os.environ.get("TWILIO_FROM_NUMBER"),
            twilio_messaging_service_sid=os.environ.get(
                "TWILIO_MESSAGING_SERVICE_SID"
            ),
            sendgrid_api_key=os.environ.get("SENDGRID_API_KEY", ""),
            sendgrid_from_email=os.environ.get("SENDGRID_FROM_EMAIL", ""),
            sendgrid_api_base_url=os.environ.get(
                "SENDGRID_API_BASE_URL", "https://api.sendgrid.com"
            ),
        )

    async def send_pickup_notification(
        self, *, destination: str, message: str, idempotency_key: str
    ) -> None:
        if "@" in destination:
            await self._send_email(destination, message, idempotency_key)
        else:
            await self._send_sms(destination, message)

    async def _send_sms(self, destination: str, message: str) -> None:
        if not re.fullmatch(r"\+[1-9][0-9]{7,14}", destination):
            raise ValueError("SMS recipient must be an E.164 phone number")

        url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{quote(self._account_sid, safe='')}/Messages.json"
        )
        form = {"To": destination, "Body": message}
        if self._twilio_messaging_service_sid:
            form["MessagingServiceSid"] = self._twilio_messaging_service_sid
        else:
            form["From"] = self._twilio_from_number

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                url,
                data=form,
                auth=(self._twilio_api_key_sid, self._twilio_api_key_secret),
            )
        if not response.is_success:
            raise NotificationProviderError(
                f"Twilio rejected the SMS request (HTTP {response.status_code})"
            )

    async def _send_email(
        self, destination: str, message: str, idempotency_key: str
    ) -> None:
        payload = {
            "personalizations": [
                {
                    "to": [{"email": destination}],
                    "custom_args": {"parcel_event_id": idempotency_key},
                }
            ],
            "from": {"email": self._sendgrid_from_email},
            "subject": "Your parcel is ready for pickup",
            "content": [{"type": "text/plain", "value": message}],
        }
        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                f"{self._sendgrid_api_base_url}/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self._sendgrid_api_key}",
                    "Content-Type": "application/json",
                },
            )
        if not response.is_success:
            raise NotificationProviderError(
                f"SendGrid rejected the email request (HTTP {response.status_code})"
            )


def pickup_notification_gateway_from_env():
    """Keep the local demo on console unless real provider use is explicitly enabled."""
    provider = os.environ.get("PICKUP_NOTIFICATION_PROVIDER", "console").strip().lower()
    if provider == "console":
        return ConsolePickupGateway()
    if provider in {"twilio-sendgrid", "twilio_sendgrid"}:
        return TwilioSendGridGateway.from_environment()
    raise ValueError(
        "PICKUP_NOTIFICATION_PROVIDER must be 'console' or 'twilio-sendgrid'"
    )
