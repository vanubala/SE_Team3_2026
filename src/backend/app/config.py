from functools import lru_cache
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_url: str
    jwt_secret: SecretStr
    jwt_issuer: str = 'smart-locker-auth'
    jwt_audience: str = 'smart-locker-api'
    jwt_ttl_minutes: int = Field(default=30, ge=1, le=60)
    cors_origins: list[str] = ['http://localhost:5173', 'http://127.0.0.1:5173']
    # HMAC key for pickup PINs; must be identical for deposit (UC3) and pickup (UC4).
    pickup_code_secret: SecretStr | None = None
    terminal_token_ttl_days: int = Field(default=365, ge=1, le=730)

    @field_validator('jwt_secret')
    @classmethod
    def strong_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode()) < 32 or 'replace-with' in value.get_secret_value():
            raise ValueError('JWT_SECRET must contain at least 32 bytes of randomly generated secret material')
        return value

    @field_validator('pickup_code_secret')
    @classmethod
    def strong_pickup_secret(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and (len(value.get_secret_value().encode()) < 32
                                  or 'replace-with' in value.get_secret_value()):
            raise ValueError('PICKUP_CODE_SECRET must contain at least 32 bytes of randomly generated secret material')
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
