import re
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.db.models import Role


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=1024, repr=False)

    @field_validator('email')
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Invalid email format')
        return value


class UserResponse(BaseModel):
    userId: UUID
    name: str
    role: Role


class LoginResponse(BaseModel):
    token: str
    user: UserResponse
