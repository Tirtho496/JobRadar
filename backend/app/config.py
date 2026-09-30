from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://jobradar:jobradar@db:5432/jobradar"
    api_key: str = "jobradar-local"
    app_timezone: str = "UTC"
    daily_ingest_hour: int = 7
    daily_ingest_minute: int = 0
    scan_on_startup: bool = False
    embedding_enabled: bool = True
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    max_concurrent_sources: int = 5
    allow_unclear_language: bool = False
    log_level: str = "INFO"
    config_dir: Path = Path("../config")
    data_dir: Path = Path("../data")


@lru_cache
def get_settings() -> Settings:
    return Settings()
