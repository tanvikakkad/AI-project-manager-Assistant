from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import AIProviderName


class Settings(BaseSettings):
    """Single source of truth for all environment-driven configuration.

    No other module in the application reads `os.environ`/`.env` directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Mini AI Project Manager Assistant"
    environment: str = "local"
    log_level: str = "INFO"

    database_url: str

    cors_origins: str = "http://localhost:5173"

    ai_provider: AIProviderName = AIProviderName.GEMINI

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
