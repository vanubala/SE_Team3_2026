"""HTTP endpoints. Each one validates input and delegates to AuthService."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import security
from .config import Settings
from .services import AuthService, CodeDispatch, public_user


class _Body(BaseModel):
    # Unknown fields (for example a "role") are rejected, not ignored.
    model_config = ConfigDict(extra="forbid")


class PasswordSignIn(_Body):
    identifier: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class CodeRequest(_Body):
    identifier: str = Field(min_length=1, max_length=254)


class CodeCheck(_Body):
    identifier: str = Field(min_length=1, max_length=254)
    code: str = Field(pattern=r"^\d{6}$")


class Registration(_Body):
    name: str = Field(min_length=1, max_length=80)
    identifier: str = Field(min_length=1, max_length=254)

    @field_validator("name")
    @classmethod
    def clean_name(cls, name: str) -> str:
        name = " ".join("".join(ch for ch in name if ch.isprintable()).split())
        if not name:
            raise ValueError("Enter your name")
        return name


def _code_sent(dispatch: CodeDispatch, message: str) -> dict:
    body = {
        "message": message,
        "channel": dispatch.channel,
        "destination": dispatch.destination,
        "expiresInMinutes": dispatch.expires_in_minutes,
    }
    if dispatch.dev_code is not None:
        body["devCode"] = dispatch.dev_code
    return body


def build_router(service: AuthService, settings: Settings) -> APIRouter:
    router = APIRouter(prefix="/api")
    bearer = HTTPBearer(auto_error=False)

    def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
        unauthorized = {"WWW-Authenticate": "Bearer"}
        if credentials is None:
            raise HTTPException(401, "Please sign in.", headers=unauthorized)
        try:
            claims = security.decode_token(settings, credentials.credentials)
        except jwt.PyJWTError:
            raise HTTPException(401, "Your session is invalid or has expired. Please sign in again.",
                                headers=unauthorized) from None
        user = service.get_user(claims["sub"])
        if user is None or user["role"] != claims["role"]:
            raise HTTPException(401, "Please sign in again.", headers=unauthorized)
        return user

    def require_role(*roles: str):
        def check(user: dict = Depends(current_user)) -> dict:
            if user["role"] not in roles:
                raise HTTPException(403, "Your account type doesn't have access to this area.")
            return user
        return check

    # Sign in: couriers and administrators -------------------------------------

    @router.post("/auth/login", tags=["Sign in"])
    def sign_in_with_password(body: PasswordSignIn):
        return service.sign_in_with_password(body.identifier, body.password)

    # Sign in: senders and recipients ------------------------------------------

    @router.post("/auth/code", tags=["Sign in"])
    def request_sign_in_code(body: CodeRequest):
        dispatch = service.request_sign_in_code(body.identifier)
        return _code_sent(dispatch, f"If an account exists for {dispatch.destination}, "
                                    f"a 6-digit code has been sent to it.")

    @router.post("/auth/code/verify", tags=["Sign in"])
    def verify_sign_in_code(body: CodeCheck):
        return service.verify_sign_in_code(body.identifier, body.code)

    # Registration: senders and recipients only ---------------------------------

    @router.post("/auth/register", tags=["Registration"])
    def register(body: Registration):
        dispatch = service.register_customer(body.name, body.identifier)
        return _code_sent(dispatch, f"We sent a 6-digit code to {dispatch.destination}. "
                                    f"Enter it to finish creating your account.")

    @router.post("/auth/register/verify", status_code=201, tags=["Registration"])
    def verify_registration(body: CodeCheck):
        return service.verify_registration(body.identifier, body.code)

    # Signed-in areas -----------------------------------------------------------

    @router.get("/me", tags=["Account"])
    def me(user: dict = Depends(current_user)):
        return public_user(user)

    @router.get("/courier/overview", tags=["Role areas"])
    def courier_overview(user: dict = Depends(require_role("COURIER"))):
        return {
            "area": "COURIER",
            "company": user["company"],
            "features": [
                "Register a parcel (C1)",
                "View available lockers (C2)",
                "View locker information (C3)",
                "Scan parcel to deposit (C4)",
                "Confirm parcel placement (C5)",
            ],
        }

    @router.get("/customer/overview", tags=["Role areas"])
    def customer_overview(user: dict = Depends(require_role("CUSTOMER"))):
        return {
            "area": "CUSTOMER",
            "parcels": [],
            "features": [
                "Track a parcel (R1, R10)",
                "Receive pickup code and instructions (R2)",
                "View locker information (R3)",
                "Send or return a parcel (R12)",
            ],
        }

    @router.get("/admin/accounts", tags=["Role areas"])
    def admin_accounts(user: dict = Depends(require_role("ADMINISTRATOR"))):
        return {"area": "ADMINISTRATOR", "accounts": service.list_accounts()}

    return router
