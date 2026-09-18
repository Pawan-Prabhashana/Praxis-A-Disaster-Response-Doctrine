"""Application configuration.

All runtime configuration is sourced from environment variables (or a local
``.env`` file) via ``pydantic-settings``. Sensible defaults are provided so the
API can boot for local development without any manual setup, while every value
remains overridable in staging/production.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PRAXIS_",
        extra="ignore",
    )

    # --- Identity -----------------------------------------------------------
    app_name: str = "Praxis"
    app_version: str = "0.1.0"
    environment: str = "development"

    # --- API surface --------------------------------------------------------
    api_v1_prefix: str = "/api/v1"

    # --- Database -----------------------------------------------------------
    # Async SQLAlchemy URL. Defaults target the local Docker Compose Postgres
    # (host port 5433 — see docker-compose.yml / .env.example).
    database_url: str = "postgresql+asyncpg://praxis:praxis@localhost:5433/praxis"

    # --- LLM (Phase 6 — operational brief narration) ------------------------
    # The brief generator narrates REAL computed facts. The LLM is strictly
    # optional: with it disabled or no key present, the app renders a complete
    # brief from the deterministic template — every code path works offline and
    # with no key (tests never call a real API). Configure via PRAXIS_LLM_*.
    llm_enabled: bool = False
    llm_api_key: str | None = None
    llm_model: str = "claude-sonnet-5"
    # Anthropic Messages API by default; override for a compatible gateway.
    llm_base_url: str = "https://api.anthropic.com"
    llm_api_version: str = "2023-06-01"
    llm_max_tokens: int = 2000
    llm_timeout_s: float = 30.0

    @property
    def llm_ready(self) -> bool:
        """True only when narration is both enabled and has a key to use."""
        return self.llm_enabled and bool(self.llm_api_key)

    # --- CORS ---------------------------------------------------------------
    # Comma-separated list of allowed origins for the browser client.
    # `NoDecode` disables pydantic-settings' automatic JSON decoding so a plain
    # comma-separated env value (e.g. "http://a,http://b") is handled by the
    # validator below rather than being rejected as invalid JSON.
    cors_origins: Annotated[list[str], NoDecode] = Field(default=["http://localhost:5173"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Accept a comma-separated string as well as a native list value."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def sync_database_url(self) -> str:
        """Synchronous SQLAlchemy URL derived from the async one.

        The API uses the async engine (asyncpg); the ETL layer uses a separate
        SYNC engine (psycopg) because GeoPandas ``to_postgis`` and bulk inserts
        are simplest against a blocking connection. Both point at the same DB.
        """
        return self.database_url.replace("+asyncpg", "+psycopg")


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance (one per process)."""
    return Settings()
