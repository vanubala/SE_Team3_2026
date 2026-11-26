"""Pickup credential primitives (FR_01, NFR_02).

* Pickup codes are 6-digit PINs created by the deposit flow (UC3). Only
  HMAC-SHA256(PICKUP_CODE_SECRET, pin) as hex is stored, so a database leak
  alone does not reveal live PINs, while the terminal can still look a PIN up
  in a single indexed query (NFR_03). This must stay byte-for-byte identical
  to UC3's ``PickupCodeIssuer.hash_code``.
* A successful verify returns a short-lived signed pickup session token. The
  terminal must present it to confirm collection, so knowing a parcel ID is
  not enough to mark a parcel collected or free its compartment.
"""
import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from pydantic import SecretStr
from app.config import Settings

PICKUP_SESSION_TTL = timedelta(minutes=10)
_SESSION_AUDIENCE = 'smart-locker-terminal-pickup'


class PickupCodeHasher:
    def __init__(self, secret: SecretStr):
        self._key = secret.get_secret_value().encode('utf-8')

    def hash(self, code: str) -> str:
        return hmac.new(self._key, code.encode('ascii'), hashlib.sha256).hexdigest()


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
