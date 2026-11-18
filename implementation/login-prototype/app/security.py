"""Password hashing, one-time codes and session tokens."""
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import secrets

import jwt

from .config import Settings

# scrypt parameters (standard library, no extra dependency). About 16 MB of
# memory per hash, which makes offline guessing of stolen hashes expensive.
_N, _R, _P, _DKLEN = 2**14, 8, 1, 32


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return "$".join(["scrypt", str(_N), str(_R), str(_P),
                     base64.b64encode(salt).decode(), base64.b64encode(digest).decode()])


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(digest_b64)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=base64.b64decode(salt_b64),
                                n=int(n), r=int(r), p=int(p), dklen=len(expected))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


# Checked against when a company ID does not exist, so the response time does
# not reveal which IDs are real.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(16))


def generate_code() -> str:
    return f"{secrets.randbelow(10**6):06d}"


def hash_code(code: str, key: str) -> str:
    return hmac.new(key.encode(), code.encode(), hashlib.sha256).hexdigest()


def issue_token(settings: Settings, user: dict) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=settings.token_minutes)
    token = jwt.encode({
        "sub": user["user_id"],
        "role": user["role"],
        "name": user["name"],
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": now,
        "exp": expires,
    }, settings.jwt_secret, algorithm="HS256")
    return token, expires


def decode_token(settings: Settings, token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        options={"require": ["sub", "role", "exp", "iss", "aud"]},
    )
