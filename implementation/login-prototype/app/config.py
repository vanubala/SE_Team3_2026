"""Runtime settings for the login prototype."""
from dataclasses import dataclass, field
import secrets


@dataclass(frozen=True)
class Settings:
    database_path: str
    # Signing key for session tokens. A fresh random key is used on every start
    # unless one is passed in, so old tokens stop working after a restart.
    jwt_secret: str = field(default_factory=lambda: secrets.token_urlsafe(48))
    # Separate key used to store one-time codes as keyed hashes.
    code_secret: str = field(default_factory=lambda: secrets.token_urlsafe(48))
    jwt_issuer: str = "smart-locker-auth"
    jwt_audience: str = "smart-locker-api"
    token_minutes: int = 60
    # There is no SMS/email gateway yet, so one-time codes are returned to the
    # page and printed in the terminal. Turn this off once a gateway exists.
    show_codes_on_screen: bool = True
    # Optional shared password for all seeded staff accounts. When it is not
    # set, every staff account gets a new random password on each start.
    staff_password: str | None = None
    code_ttl_minutes: int = 10
    code_resend_seconds: int = 30
    max_failed_attempts: int = 5
    lockout_minutes: int = 15

    def __post_init__(self) -> None:
        if len(self.jwt_secret.encode()) < 32 or len(self.code_secret.encode()) < 32:
            raise ValueError("jwt_secret and code_secret must each be at least 32 bytes")
        if self.jwt_secret == self.code_secret:
            raise ValueError("jwt_secret and code_secret must be different")
        if self.staff_password is not None and len(self.staff_password) < 8:
            raise ValueError("The staff password must be at least 8 characters long")
