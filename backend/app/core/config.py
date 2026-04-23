from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "DBF Comparator Pro API"
    api_v1_prefix: str = "/api/v1"
    app_env: str = "development"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://postgres:postgres@postgres:5432/dbf_comparator"
    redis_url: str = "redis://redis:6379/0"
    temp_storage_root: Path = Field(default=Path("/tmp/dbf-comparator"))
    upload_max_size_bytes: int = 100 * 1024 * 1024
    artifact_ttl_hours: int = 24
    cors_origins: list[str] = ["http://localhost:5173"]
    request_id_header: str = "X-Request-ID"
    execution_mode: str = "web"
    job_runner: str = "celery"
    enable_redis_checks: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
