from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://pickpilot:pickpilot@localhost:5432/pickpilot"
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:3000"])
    max_upload_bytes: int = 20 * 1024 * 1024
    max_import_rows: int = 50000
    max_sku_filter_rows: int = 10000
    import_batch_size: int = 1000
    sku_filter_ttl_seconds: int = 3600
    scrape_output_dir: str = "backend/scrape_outputs"
    scrape_timeout_seconds: int = 30
    scrape_max_results: int = 10
    scrape_delay_seconds: float = 0
    scrape_max_concurrency: int = 2
    openrouter_api_key: str | None = None
    openrouter_model: str = "tencent/hy3:free"
    openrouter_timeout_seconds: int = 60
    match_auto_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_prefix="PICKPILOT_", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
