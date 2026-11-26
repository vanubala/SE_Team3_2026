"""Locker terminal (kiosk) credentials.

Each physical terminal holds a long-lived signed token bound to its locker
station and sends it as ``Authorization: Bearer <token>``. The token uses its
own audience, so it is never accepted as a staff JWT, and a staff JWT is never
accepted here. ``require_locker_terminal`` is the dependency the deposit (UC3)
and pickup (UC4) routers share; it returns an object with ``locker_id: str``,
matching UC3's ``TerminalContext``.

Issue a token for a station (development):
    python -m app.security.terminal_auth <locker_id>
"""
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.config import Settings

_TERMINAL_AUDIENCE = 'smart-locker-terminal'
_bearer = HTTPBearer(auto_error=False)


class InvalidTerminalToken(Exception):
    pass


@dataclass(frozen=True)
class TerminalPrincipal:
    locker_id: str


class TerminalTokenService:
    def __init__(self, settings: Settings):
        self._secret = settings.jwt_secret.get_secret_value()
        self._issuer = settings.jwt_issuer
        self._ttl = timedelta(days=settings.terminal_token_ttl_days)

    def issue(self, locker_id: UUID, now: datetime | None = None) -> str:
        now = now or datetime.now(timezone.utc)
        return jwt.encode({'sub': str(locker_id), 'typ': 'terminal', 'iss': self._issuer,
                           'aud': _TERMINAL_AUDIENCE, 'iat': now, 'exp': now + self._ttl},
                          self._secret, algorithm='HS256')

    def verify(self, token: str) -> TerminalPrincipal:
        try:
            claims = jwt.decode(token, self._secret, algorithms=['HS256'], issuer=self._issuer,
                                audience=_TERMINAL_AUDIENCE,
                                options={'require': ['sub', 'typ', 'iss', 'aud', 'iat', 'exp']})
            if claims['typ'] != 'terminal':
                raise InvalidTerminalToken()
            return TerminalPrincipal(str(UUID(claims['sub'])))
        except (jwt.InvalidTokenError, ValueError, TypeError, AttributeError, KeyError) as exc:
            raise InvalidTerminalToken() from exc


def require_locker_terminal(request: Request,
                            credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)
                            ) -> TerminalPrincipal:
    headers = {'WWW-Authenticate': 'Bearer', 'Cache-Control': 'no-store'}
    if credentials is None:
        raise HTTPException(401, 'Missing or invalid terminal credential', headers=headers)
    try:
        return request.app.state.terminal_tokens.verify(credentials.credentials)
    except InvalidTerminalToken as exc:
        raise HTTPException(401, 'Missing or invalid terminal credential', headers=headers) from exc


def main():
    parser = argparse.ArgumentParser(description='Print a terminal credential for one locker station.')
    parser.add_argument('locker_id', type=UUID)
    args = parser.parse_args()
    from dotenv import load_dotenv
    load_dotenv()
    print(TerminalTokenService(Settings()).issue(args.locker_id))


if __name__ == '__main__':
    main()
