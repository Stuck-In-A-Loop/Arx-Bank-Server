"""Global settings for the application."""

from typing import List, Optional

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "arxbank"
    PROJECT_NAME: str = "Arx Bank Server"
    LOG_LEVEL: str = "DEBUG"
    PORT: int = 8000

    DEV_MODE: bool = False

    SHOW_CAMERA: bool = False

    BASE_URL: AnyHttpUrl = AnyHttpUrl("http://localhost:8000")

    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", \
    # "http://localhost:8080", "http://local.dockertoolbox.tiangolo.com"]'
    BACKEND_CORS_ORIGINS: List[str] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        if isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    SQLITEDB_URL: str = "sqlite:///./test.db"

    DATABASE_URL: str = "postgresql://user:password@localhost/db"
    # CELERY_DATABASE_URL: str = "db+postgresql://user:password@localhost/celerydb"
    CELERY_DATABASE_URL: str = (
        "db+postgresql://postgres:postgres@localhost:5432/celerydb"
    )

    # REDIS_URL: str = "redis://redis:6379/0"
    REDIS_URL: str = "redis://localhost:6432/0"

    SMTP_USER: str = "user"
    SMTP_PASSWORD: str = "password"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
# print(settings)
