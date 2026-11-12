"""JWT adapter for the C0 authentication module; no password/login implementation."""
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from .config import Settings

_bearer = HTTPBearer(auto_error=False)


def require_courier(settings: Settings):
    def verify(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]) -> str:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Valid courier authentication is required", headers={"WWW-Authenticate": "Bearer"})
        try:
            claims = jwt.decode(
                credentials.credentials,
                settings.jwt_secret,
                algorithms=["HS256"],
                issuer=settings.jwt_issuer,
                audience=settings.jwt_audience,
                options={"require": ["sub", "exp", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid or expired authentication token", headers={"WWW-Authenticate": "Bearer"}) from exc
        if not isinstance(claims.get("sub"), str) or not claims["sub"].strip():
            raise HTTPException(status_code=401, detail="Missing authenticated user")
        if claims.get("role") != "COURIER":
            raise HTTPException(status_code=403, detail="Courier role required")
        return claims["sub"]
    return verify


def issue_demo_token(settings: Settings, subject: str = "demo-courier") -> str:
    """DEVELOPMENT ONLY. Demo sessions are never exposed unless explicitly enabled."""
    now = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": subject, "role": "COURIER", "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience, "iat": now,
        "exp": now + timedelta(hours=1),
    }, settings.jwt_secret, algorithm="HS256")
