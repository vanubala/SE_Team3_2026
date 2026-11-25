from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from app.config import Settings
from app.db.models import Role


class InvalidToken(Exception):
    """A bearer credential is absent, invalid or expired."""


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    role: Role


class TokenService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def issue(self, user_id: UUID, role: Role) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode({'sub': str(user_id), 'role': role.value,
                           'iss': self.settings.jwt_issuer, 'aud': self.settings.jwt_audience,
                           'iat': now, 'exp': now + timedelta(minutes=self.settings.jwt_ttl_minutes)},
                          self.settings.jwt_secret.get_secret_value(), algorithm='HS256')

    def verify(self, token: str) -> Principal:
        try:
            claims = jwt.decode(token, self.settings.jwt_secret.get_secret_value(),
                                algorithms=['HS256'], issuer=self.settings.jwt_issuer,
                                audience=self.settings.jwt_audience,
                                options={'require': ['sub', 'role', 'iss', 'aud', 'iat', 'exp']})
            return Principal(UUID(claims['sub']), Role(claims['role']))
        except (jwt.InvalidTokenError, ValueError, TypeError, AttributeError) as exc:
            raise InvalidToken() from exc
