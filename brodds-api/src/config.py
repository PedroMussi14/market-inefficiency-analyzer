"""Centralised settings, loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Storage
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url:    str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # API auth — clients must send X-API-Key matching this value
    api_key:      str = Field("dev_local_key_change_me", alias="API_KEY")

    # Scraping
    proxy_url:    str | None = Field(None, alias="PROXY_URL")
    user_agents:  str        = Field(
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        alias="USER_AGENTS",
    )
    scrape_interval_seconds: int = Field(90, alias="SCRAPE_INTERVAL_SECONDS")

    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @property
    def user_agent_pool(self) -> list[str]:
        return [ua.strip() for ua in self.user_agents.split(",") if ua.strip()]


settings = Settings()
