"""Stand-in for the shared JWT/RBAC middleware. Replace at integration."""
from typing import Callable

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ISSUER = "smart-locker-auth"
AUDIENCE = "smart-locker-api"


def make_require_admin(secret: str) -> Callable:
    if len(secret.encode()) < 32:
        raise ValueError("The JWT secret must be at least 32 bytes")
    bearer = HTTPBearer(auto_error=False)

    def require_admin(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ) -> str:
        headers = {"WWW-Authenticate": "Bearer"}
        if credentials is None:
            raise HTTPException(401, "Authentication is required.", headers=headers)
        try:
            claims = jwt.decode(
                credentials.credentials, secret, algorithms=["HS256"],
                issuer=ISSUER, audience=AUDIENCE,
                options={"require": ["sub", "exp", "iss", "aud"]},
            )
        except jwt.PyJWTError:
            raise HTTPException(401, "Invalid or expired token.", headers=headers) from None
        if claims.get("role") != "ADMIN":
            raise HTTPException(403, "Administrator role required.")
        return claims["sub"]

    return require_admin
