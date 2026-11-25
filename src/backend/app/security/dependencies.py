"""Reusable FastAPI bearer/RBAC guards. Attach to every protected route."""
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.db.models import Role
from app.security.tokens import InvalidToken, Principal

bearer = HTTPBearer(auto_error=False)


def current_user(request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> Principal:
    if credentials is None:
        raise HTTPException(401, 'Missing or invalid bearer token', headers={'WWW-Authenticate':'Bearer'})
    try:
        return request.app.state.tokens.verify(credentials.credentials)
    except InvalidToken as exc:
        raise HTTPException(401, 'Missing or invalid bearer token', headers={'WWW-Authenticate':'Bearer'}) from exc


def require_role(*roles: Role):
    """Return a route dependency that denies roles not explicitly allowed."""
    allowed = frozenset(Role(role) for role in roles)
    if not allowed:
        raise ValueError('At least one allowed role is required')

    def check(principal: Principal = Depends(current_user)) -> Principal:
        if principal.role not in allowed:
            raise HTTPException(403, 'Insufficient role permissions')
        return principal

    return check


require_courier = require_role(Role.COURIER)
require_admin = require_role(Role.ADMIN)
