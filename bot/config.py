"""Load configuration from environment (Pydantic Settings)."""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Bot and app settings from env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    admin_ids: str
    database_path: str = "./data/database2.db"
    channel_link: str = ""
    bot_link: str = ""
    support_user_id: int = 1251526792
    support_username: str = ""
    url_telegraph_rules: str = ""
    url_telegraph_games: str = ""
    url_telegraph_deposit: str = ""
    url_telegraph_support: str = ""
    url_telegraph_faq: str = ""
    webapp_base_url: str = ""  # e.g. https://yourdomain.com for Flet WebApp (?user_id= appended)

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: str | List[int]) -> str:
        if isinstance(v, list):
            return ",".join(str(x) for x in v)
        return str(v)

    def get_admin_ids(self) -> List[int]:
        """Return list of admin user IDs."""
        if not self.admin_ids.strip():
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]


@lru_cache
def get_config() -> Settings:
    """Return cached settings instance."""
    return Settings()
