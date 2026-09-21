"""Application configuration. All values come from the environment (see .env.example)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Zenkai API"
    ENV: str = "development"
    DEBUG: bool = True

    # PostgreSQL in production:
    #   postgresql+psycopg://studentos:studentos@localhost:5432/studentos
    # SQLite is the zero-dependency default so the project runs without a database server.
    DATABASE_URL: str = "sqlite:///./studentos.db"

    # Comma-separated list of allowed browser origins.
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Shared secret required by /api/v1/admin/*. Change it outside development.
    ADMIN_TOKEN: str = "dev-admin-token"

    # The demo identity used when a request carries no session token, and the
    # password it is seeded with. Development convenience only — see
    # `allow_demo_fallback`.
    DEMO_USER_EMAIL: str = "student@zenkai.dev"
    DEMO_USER_PASSWORD: str = "zenkai-demo-2026"
    DEMO_ADMIN_EMAIL: str = "reviewer@zenkai.dev"
    DEMO_ADMIN_PASSWORD: str = "zenkai-review-2026"

    # When true, a request with no session resolves to the demo student. Unset
    # it in production: a shared implicit identity would let every visitor read
    # and write the same account.
    ALLOW_DEMO_FALLBACK: bool | None = None

    # Opportunities are re-checked on this cadence by the (future) scheduler.
    DEFAULT_CHECK_FREQUENCY_MINUTES: int = 720

    # LLM provider for the extraction/classification pipeline. "stub" needs no key.
    AI_PROVIDER: str = "stub"
    AI_API_KEY: str | None = None
    AI_MODEL: str = "claude-sonnet-5"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def allow_demo_fallback(self) -> bool:
        """Defaults to on in development, off everywhere else."""
        if self.ALLOW_DEMO_FALLBACK is not None:
            return self.ALLOW_DEMO_FALLBACK
        return self.ENV == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
