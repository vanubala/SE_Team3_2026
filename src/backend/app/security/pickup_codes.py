"""Pickup credential primitives (FR_01, NFR_02).

* Pickup codes are 6-digit PINs drawn from a CSPRNG. Only a keyed HMAC of the
  PIN is stored, so a database leak alone does not reveal live PINs, while the
  terminal can still look a PIN up in a single indexed query (NFR_03).
* A successful verify returns a short-lived signed pickup session token. The
  terminal must present it to confirm collection, so knowing a parcel ID is
  not enough to mark a parcel collected or free its compartment.
"""
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from app.config import Settings

PICKUP_CODE_DIGITS = 6
PICKUP_SESSION_TTL = timedelta(minutes=10)
_SESSION_AUDIENCE = 'smart-locker-terminal-pickup'


def generate_pickup_code() -> str:
    return f'{secrets.randbelow(10 ** PICKUP_CODE_DIGITS):0{PICKUP_CODE_DIGITS}d}'


class PickupCodeHasher:
    def __init__(self, settings: Settings):
        # Domain-separated key derived from the server secret; never stored.
        self._key = hmac.new(settings.jwt_secret.get_secret_value().encode(),
                             b'pickup-code-hmac-v1', hashlib.sha256).digest()

    def hash(self, code: str) -> str:
        return hmac.new(self._key, code.encode(), hashlib.sha256).hexdigest()


class InvalidPickupSession(Exception):
    """The pickup session token is missing, forged, expired or for another parcel."""


@dataclass(frozen=True)
class PickupSession:
    parcel_id: UUID
    compartment_id: UUID
    locker_id: UUID


class PickupSessionTokens:
    def __init__(self, settings: Settings):
        self._secret = settings.jwt_secret.get_secret_value()
        self._issuer = settings.jwt_issuer

    def issue(self, session: PickupSession, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        return jwt.encode({'sub': str(session.parcel_id), 'cmp': str(session.compartment_id),
                           'lkr': str(session.locker_id), 'iss': self._issuer,
                           'aud': _SESSION_AUDIENCE, 'iat': now, 'exp': now + PICKUP_SESSION_TTL},
                          self._secret, algorithm='HS256')

    def verify(self, token: str) -> PickupSession:
        try:
            claims = jwt.decode(token, self._secret, algorithms=['HS256'], issuer=self._issuer,
                                audience=_SESSION_AUDIENCE,
                                options={'require': ['sub', 'cmp', 'lkr', 'iss', 'aud', 'iat', 'exp']})
            return PickupSession(UUID(claims['sub']), UUID(claims['cmp']), UUID(claims['lkr']))
        except (jwt.InvalidTokenError, ValueError, TypeError, AttributeError) as exc:
            raise InvalidPickupSession() from exc
