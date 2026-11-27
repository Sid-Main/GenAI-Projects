"""Application settings, loaded from environment variables and the project .env file."""

# Cache the settings object so .env is read only once
from functools import lru_cache

# Build file paths in an OS-independent way
from pathlib import Path

# Restrict a value to a fixed set of allowed strings
from typing import Literal

# Field: extra options for a setting; PostgresDsn: validates database URLs
from pydantic import Field, PostgresDsn

# BaseSettings: a model that fills itself from env vars; SettingsConfigDict: its options
from pydantic_settings import BaseSettings, SettingsConfigDict

# This file is backend/src/rag_app/core/config.py, so 4 levels up is advanced_rag_concepts/
PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    # Where and how to read the .env file
    model_config = SettingsConfigDict(
        # Absolute path to advanced_rag_concepts/.env, works from any working directory
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        # Ignore .env keys this class doesn't define (e.g. POSTGRES_* used only by Docker)
        extra="ignore",
    )

    # Each field reads the env var of the same name in UPPERCASE (app_name <- APP_NAME)
    app_name: str = "rag-app"
    # Only these three values are valid; anything else fails at startup
    environment: Literal["local", "test", "production"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    # False = readable console logs for development; True = JSON logs for production
    log_json: bool = False
    # Required (no default): the app refuses to start without DATABASE_URL
    database_url: PostgresDsn
    # Frontend origins allowed to call this API (Vite dev server runs on 5173)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])


# Create Settings once and reuse it everywhere
@lru_cache
def get_settings() -> Settings:
    return Settings()
