"""Pickup PIN generation; share the secret with the UC4 verification service."""
import hashlib
import hmac
import re
import secrets
from uuid import uuid4

from .contracts import IssuedPickupCode


class PickupCodeIssuer:
    """Create a six-digit PIN and a keyed hash suitable for storage."""

    def __init__(self, secret: str | bytes) -> None:
        secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else secret
        if len(secret_bytes) < 32:
            raise ValueError("pickup-code secret must be at least 32 bytes")
        self._secret = secret_bytes

    def issue(self) -> IssuedPickupCode:
        plaintext = f"{secrets.randbelow(1_000_000):06d}"
        return IssuedPickupCode(
            code_id=uuid4(),
            plaintext=plaintext,
            code_hash=self.hash_code(plaintext),
        )

    def hash_code(self, plaintext: str) -> str:
        """Hash a PIN using the format UC4 must use when verifying it."""
        if not re.fullmatch(r"[0-9]{6}", plaintext):
            raise ValueError("pickup code must contain exactly six digits")
        return hmac.new(
            self._secret, plaintext.encode("ascii"), hashlib.sha256
        ).hexdigest()

    def verify(self, plaintext: str, expected_hash: str) -> bool:
        """Constant-time verification helper for the UC4 pickup service."""
        if not re.fullmatch(r"[0-9]{6}", plaintext):
            return False
        return hmac.compare_digest(self.hash_code(plaintext), expected_hash)
