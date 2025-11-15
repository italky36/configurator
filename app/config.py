"""Application configuration management."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings pulled from environment / .env file."""

    database_url: str = Field(
        default="sqlite+aiosqlite:///./db.sqlite3",
        alias="DATABASE_URL",
        description="SQLAlchemy database URL",
    )
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="password", alias="ADMIN_PASSWORD")
    allowed_origins_raw: str | None = Field(default=None, alias="ALLOWED_ORIGINS")
    session_secret_key: str = Field(
        default="super-secret-key",
        alias="SESSION_SECRET_KEY",
        description="Secret key for session middleware",
    )
    uploads_dir: str = Field(default="uploads", alias="UPLOADS_DIR")
    uploads_url_prefix: str = Field(default="/uploads", alias="UPLOADS_URL_PREFIX")

    _allowed_origins: List[str] = PrivateAttr(default_factory=list)
    _uploads_path: Path = PrivateAttr(default_factory=Path)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    def model_post_init(self, __context: dict) -> None:
        self._allowed_origins = self._split_origins(self.allowed_origins_raw)
        upload_path = Path(self.uploads_dir)
        if not upload_path.is_absolute():
            upload_path = Path.cwd() / upload_path
        self._uploads_path = upload_path

    @staticmethod
    def _split_origins(value: str | List[str] | None) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def allowed_origins(self) -> List[str]:
        return self._allowed_origins

    @property
    def uploads_path(self) -> Path:
        return self._uploads_path

    @property
    def uploads_url_prefix_clean(self) -> str:
        prefix = (self.uploads_url_prefix or "/uploads").strip()
        if not prefix:
            prefix = "/uploads"
        if not prefix.startswith("/"):
            prefix = "/" + prefix
        return prefix.rstrip("/") or "/uploads"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
