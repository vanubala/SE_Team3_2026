"""Authentication use cases. No HTTP code here; the API layer maps the errors."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hmac
import math
from typing import Callable

from . import security
from .config import Settings
from .identifiers import Identifier, IdentifierKind, InvalidIdentifier, parse_identifier
from .notifications import ConsoleGateway
from .repository import UserRepository


# Errors ---------------------------------------------------------------------

class AuthError(Exception):
    status = 400

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


class BadIdentifier(AuthError):
    status = 422


class WrongSignInMethod(AuthError):
    status = 400


class InvalidCredentials(AuthError):
    status = 401


class InvalidCode(AuthError):
    status = 401


class RegistrationNotAllowed(AuthError):
    status = 403


class AlreadyRegistered(AuthError):
    status = 409


class AccountLocked(AuthError):
    status = 429


class TooSoon(AuthError):
    status = 429


STAFF_USE_PASSWORD = "Couriers and administrators sign in with their company ID and password."
CUSTOMERS_USE_CODE = ("Senders and recipients sign in with a one-time code sent to their "
                      "email or phone, not with a password.")
STAFF_CANNOT_REGISTER = ("Courier and administrator accounts are provided by the company "
                         "and can't be registered here.")
BAD_CREDENTIALS = "Invalid company ID or password."
BAD_CODE = "The code is wrong or has expired. Check it or request a new one."


@dataclass
class CodeDispatch:
    channel: str          # "EMAIL" or "SMS"
    destination: str      # masked, safe to show
    expires_in_minutes: int
    dev_code: str | None  # only while no real gateway exists


def public_user(user: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    if user["locked_until"] and datetime.fromisoformat(user["locked_until"]) > now:
        status = "LOCKED"
    elif not user["verified"]:
        status = "PENDING_VERIFICATION"
    else:
        status = "ACTIVE"
    return {
        "userId": user["user_id"],
        "role": user["role"],
        "name": user["name"],
        "loginId": user["login_id"],
        "email": user["email"],
        "phone": user["phone"],
        "company": user["company"],
        "status": status,
        "createdAt": user["created_at"],
    }


class AuthService:
    def __init__(self, repository: UserRepository, settings: Settings,
                 gateway: ConsoleGateway | None = None,
                 clock: Callable[[], datetime] | None = None):
        self.repository = repository
        self.settings = settings
        self.gateway = gateway or ConsoleGateway()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    # Couriers and administrators ---------------------------------------------

    def sign_in_with_password(self, raw_identifier: str, password: str) -> dict:
        identifier = self._parse(raw_identifier)
        if not identifier.is_staff:
            raise WrongSignInMethod(CUSTOMERS_USE_CODE)
        user = self.repository.find_by_identifier(identifier)
        if user is None:
            security.verify_password(password, security.DUMMY_PASSWORD_HASH)
            raise InvalidCredentials(BAD_CREDENTIALS)
        self._ensure_not_locked(user)
        if not security.verify_password(password, user["password_hash"]):
            self._count_failure(user)
            raise InvalidCredentials(BAD_CREDENTIALS)
        self.repository.clear_failures(user["user_id"])
        return self._session(user)

    # Senders and recipients: sign in -----------------------------------------

    def request_sign_in_code(self, raw_identifier: str) -> CodeDispatch:
        identifier = self._parse(raw_identifier)
        if identifier.is_staff:
            raise WrongSignInMethod(STAFF_USE_PASSWORD)
        dispatch = self._dispatch(identifier, dev_code=None)
        user = self.repository.find_by_identifier(identifier)
        if user is None or not user["verified"]:
            # Same answer as for a real account, so the page doesn't reveal who is registered.
            return dispatch
        self._ensure_not_locked(user)
        dispatch.dev_code = self._send_code(user, identifier, "LOGIN")
        return dispatch

    def verify_sign_in_code(self, raw_identifier: str, code: str) -> dict:
        return self._verify_code(raw_identifier, code, "LOGIN")

    # Senders and recipients: registration ------------------------------------

    def register_customer(self, name: str, raw_identifier: str) -> CodeDispatch:
        identifier = self._parse(raw_identifier)
        if identifier.is_staff:
            raise RegistrationNotAllowed(STAFF_CANNOT_REGISTER)
        user = self.repository.find_by_identifier(identifier)
        if user is not None and user["verified"]:
            raise AlreadyRegistered("An account with this email or phone number already exists. "
                                    "Sign in instead.")
        if user is None:
            user = self.repository.create_customer(name=name, identifier=identifier, now=self.clock())
        else:
            # Registration was started earlier but never confirmed: start again.
            self._ensure_not_locked(user)
            self.repository.update_name(user["user_id"], name)
        dev_code = self._send_code(user, identifier, "REGISTER")
        return self._dispatch(identifier, dev_code)

    def verify_registration(self, raw_identifier: str, code: str) -> dict:
        return self._verify_code(raw_identifier, code, "REGISTER")

    # Session helpers -----------------------------------------------------------

    def get_user(self, user_id: str) -> dict | None:
        return self.repository.get(user_id)

    def list_accounts(self) -> list[dict]:
        now = self.clock()
        return [public_user(user, now) for user in self.repository.list_users()]

    # Internals -----------------------------------------------------------------

    def _parse(self, raw: str) -> Identifier:
        try:
            return parse_identifier(raw)
        except InvalidIdentifier as exc:
            raise BadIdentifier(str(exc)) from exc

    def _dispatch(self, identifier: Identifier, dev_code: str | None) -> CodeDispatch:
        return CodeDispatch(
            channel="SMS" if identifier.kind is IdentifierKind.PHONE else "EMAIL",
            destination=identifier.masked,
            expires_in_minutes=self.settings.code_ttl_minutes,
            dev_code=dev_code,
        )

    def _ensure_not_locked(self, user: dict) -> None:
        if not user["locked_until"]:
            return
        remaining = (datetime.fromisoformat(user["locked_until"]) - self.clock()).total_seconds()
        if remaining > 0:
            minutes = math.ceil(remaining / 60)
            raise AccountLocked(
                f"Too many failed attempts. Try again in {minutes} minute{'s' if minutes != 1 else ''}.",
                retry_after=math.ceil(remaining),
            )

    def _count_failure(self, user: dict) -> None:
        lock_until = self.clock() + timedelta(minutes=self.settings.lockout_minutes)
        locked = self.repository.register_failure(
            user["user_id"], max_attempts=self.settings.max_failed_attempts, lock_until=lock_until)
        if locked:
            raise AccountLocked(
                f"Too many failed attempts. The account is locked for "
                f"{self.settings.lockout_minutes} minutes.",
                retry_after=self.settings.lockout_minutes * 60,
            )

    def _send_code(self, user: dict, identifier: Identifier, purpose: str) -> str | None:
        now = self.clock()
        previous = self.repository.latest_code(user["user_id"], purpose)
        if previous is not None:
            age = (now - datetime.fromisoformat(previous["created_at"])).total_seconds()
            if age < self.settings.code_resend_seconds:
                wait = math.ceil(self.settings.code_resend_seconds - age)
                raise TooSoon(f"Please wait {wait} seconds before requesting a new code.",
                              retry_after=wait)
        code = security.generate_code()
        self.repository.add_code(
            user_id=user["user_id"], purpose=purpose,
            code_hash=security.hash_code(code, self.settings.code_secret),
            now=now, expires=now + timedelta(minutes=self.settings.code_ttl_minutes),
        )
        self.gateway.send_code(identifier, code, purpose)
        return code if self.settings.show_codes_on_screen else None

    def _verify_code(self, raw_identifier: str, code: str, purpose: str) -> dict:
        identifier = self._parse(raw_identifier)
        if identifier.is_staff:
            raise WrongSignInMethod(STAFF_USE_PASSWORD)
        user = self.repository.find_by_identifier(identifier)
        if user is None:
            raise InvalidCode(BAD_CODE)
        # Sign-in needs a confirmed account; registration needs an unconfirmed one.
        if bool(user["verified"]) != (purpose == "LOGIN"):
            raise InvalidCode(BAD_CODE)
        self._ensure_not_locked(user)

        record = self.repository.latest_code(user["user_id"], purpose)
        now = self.clock()
        if record is None or datetime.fromisoformat(record["expires_at"]) <= now:
            raise InvalidCode(BAD_CODE)
        if not hmac.compare_digest(record["code_hash"],
                                   security.hash_code(code, self.settings.code_secret)):
            self._count_failure(user)
            raise InvalidCode(BAD_CODE)

        self.repository.consume_code(record["code_id"], now)
        self.repository.clear_failures(user["user_id"])
        if purpose == "REGISTER":
            self.repository.mark_verified(user["user_id"])
        return self._session(self.repository.get(user["user_id"]))

    def _session(self, user: dict) -> dict:
        token, expires = security.issue_token(self.settings, user)
        return {
            "token": token,
            "expiresAt": expires.isoformat(timespec="seconds"),
            "user": public_user(user),
            "redirect": "/dashboard",
        }
