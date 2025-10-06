"""Application configuration for the damsan API layer."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Expose environment-driven settings for the API."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    model_name: str = Field(default="gpt-5", alias="MODEL")
    prompt_path: str
    openai_api_key: str
    email: str
    return_articles: bool = True

    def ensure_prompt_path(self) -> Path:
        """Ensure the configured prompt path exists."""
        path = Path(self.prompt_path).expanduser()
        if not path.exists():
            msg = f"Prompt architecture file not found: {path}"
            raise FileNotFoundError(msg)
        return path

    def restriction_date_format(self, date_value: Optional[str]) -> Optional[str]:
        """No-op helper to keep settings logic centralised."""
        return date_value


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    return Settings()
