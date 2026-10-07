from functools import lru_cache
from typing import Annotated
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)
    app_env: str = "development"
    database_url: str | None = None
    redis_url: str | None = None
    api_keys: Annotated[list[str], NoDecode] = Field(default_factory=list)
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    model_ready: bool = True
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str = "crowd-ops-advisory"
    embedding_dim: int = 1536
    telemetry_stale_seconds: int = 10
    redis_channel: str = "crowd-ops:telemetry"

    @field_validator("api_keys", "cors_origins", mode="before")
    @classmethod
    def split_csv(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def validate_production(self) -> None:
        if self.app_env.lower() in {"production", "staging"}:
            missing = []
            if not self.database_url:
                missing.append("DATABASE_URL")
            if not self.redis_url:
                missing.append("REDIS_URL")
            if not self.api_keys:
                missing.append("API_KEYS")
            if missing:
                raise RuntimeError("Missing required production settings: " + ", ".join(missing))

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if settings.app_env.lower() in {"production", "staging"}:
        settings.validate_production()
    return settings
