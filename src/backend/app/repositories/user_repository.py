from dataclasses import dataclass
from typing import Protocol
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.models import User


@dataclass(frozen=True)
class UserCredentials:
    user_id: UUID
    name: str
    role: str
    password_hash: str


class UserLookup(Protocol):
    def find_by_email(self, email: str) -> UserCredentials | None: ...


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_email(self, email: str) -> UserCredentials | None:
        # Parameterised ORM query; the unique lower-case index prevents ambiguity.
        user = self.db.scalar(select(User).where(func.lower(User.email) == email))
        if user is None:
            return None
        return UserCredentials(user.user_id, user.name, user.role, user.password_hash)
