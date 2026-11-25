"""Authentication rules; no HTTP requests or SQL queries here."""
from dataclasses import dataclass
from uuid import UUID
from app.db.models import Role
from app.repositories.user_repository import UserLookup
from app.security.passwords import verify_password
from app.security.tokens import TokenService


class InvalidCredentials(Exception):
    pass


@dataclass(frozen=True)
class LoginResult:
    token: str
    user_id: UUID
    name: str
    role: Role


class AuthService:
    def __init__(self, users: UserLookup, tokens: TokenService, dummy_hash: str):
        self.users = users
        self.tokens = tokens
        self.dummy_hash = dummy_hash

    def login(self, email: str, password: str) -> LoginResult:
        user = self.users.find_by_email(email.strip().lower())
        # Perform a password check even for unknown accounts to reduce timing leakage.
        valid = verify_password(password, user.password_hash if user else self.dummy_hash)
        if user is None or not valid:
            raise InvalidCredentials()
        try:
            role = Role(user.role)
        except ValueError as exc:
            raise InvalidCredentials() from exc
        return LoginResult(self.tokens.issue(user.user_id, role), user.user_id, user.name, role)
