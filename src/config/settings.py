from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "development"
    debug: bool = True

    # CORS
    cors_origins: str = "http://localhost:5174,http://127.0.0.1:5174"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.3

    # AI Core
    base: str
    access_key: str
    secret_key: str
    model_engine_id: str = "4acbe913-df40-4ac0-b28a-daa5ad91b172"

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Cache
    cache_ttl: int = 3600
    cache_enabled: bool = True

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/app.log"

    # Analysis
    max_prompt_length: int = 5000
    min_prompt_length: int = 5
    enable_llm_analysis: bool = True

    # Performance
    max_workers: int = 4
    request_timeout: int = 30


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
