from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM (OpenRouter)
    openrouter_api_key: str
    model_name: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # GitHub integration (optional)
    github_token: str | None = None

    # Storage
    database_url: str = "sqlite:///./data/reviews.db"
    workspace_dir: str = "./workspaces"

    # Server
    cors_origins: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
