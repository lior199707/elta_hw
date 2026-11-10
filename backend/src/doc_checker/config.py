from __future__ import annotations

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from doc_checker.custom_types.config_types import LogLevel


class AppConfig(BaseSettings):
    """Environment-driven configuration. Created once at startup and passed down.

    Values come only from process environment variables. Locally, load the repo-root
    `.env` with `uv run --env-file ../.env ...`; in Docker, Compose injects it via `env_file`.
    """

    model_config = SettingsConfigDict(frozen=True, extra="ignore")

    gemini_api_key: SecretStr
    llm_model: str = Field(min_length=1)
    llm_fallback_model: str = Field(min_length=1)

    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    llm_max_concurrency: int = Field(default=2, ge=1)
    chunk_token_budget: int = Field(default=30000, ge=1)
    chunk_overlap_blocks: int = Field(default=2, ge=0)
    max_upload_mb: int = Field(default=20, ge=1)
    database_url: str = "sqlite:///./doc_checker.db"
    log_level: LogLevel = LogLevel.INFO

    @field_validator("llm_model", "llm_fallback_model", mode="before")
    @classmethod
    def _strip_model_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("gemini_api_key")
    @classmethod
    def _require_non_blank_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            raise ValueError("GEMINI_API_KEY must not be blank")
        return value


class ConfigurationError(Exception):
    """The environment does not describe a valid configuration."""


def load_config() -> AppConfig:
    """Build the config, reporting problems by variable name only.

    Pydantic's own error text echoes input values, which would leak GEMINI_API_KEY into logs.
    """
    try:
        return AppConfig()
    except ValidationError as exc:
        problems = [
            f"{'.'.join(str(part) for part in error['loc']).upper()} ({error['type']})"
            for error in exc.errors(include_input=False)
        ]
        raise ConfigurationError(f"Invalid configuration: {', '.join(problems)}") from None
