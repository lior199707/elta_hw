from __future__ import annotations

import pytest
from pydantic import ValidationError

from doc_checker.config import AppConfig, ConfigurationError, load_config
from doc_checker.custom_types.config_types import LogLevel


def test_loads_required_values_and_defaults(required_env: pytest.MonkeyPatch) -> None:
    config = AppConfig()

    assert config.gemini_api_key.get_secret_value() == "test-key-not-real"
    assert config.llm_model == "test-primary-model"
    assert config.llm_fallback_model == "test-fallback-model"
    assert config.llm_temperature == 0.0
    assert config.llm_max_concurrency == 2
    assert config.chunk_token_budget == 30000
    assert config.chunk_overlap_blocks == 2
    assert config.max_upload_mb == 20
    assert config.log_level == LogLevel.INFO


@pytest.mark.parametrize("missing", ["GEMINI_API_KEY", "LLM_MODEL", "LLM_FALLBACK_MODEL"])
def test_missing_required_variable_fails_fast(
    required_env: pytest.MonkeyPatch, missing: str
) -> None:
    required_env.delenv(missing)

    with pytest.raises(ValidationError) as exc_info:
        AppConfig()

    assert missing.lower() in str(exc_info.value)


@pytest.mark.parametrize("name", ["GEMINI_API_KEY", "LLM_MODEL", "LLM_FALLBACK_MODEL"])
def test_empty_required_variable_fails_fast(required_env: pytest.MonkeyPatch, name: str) -> None:
    required_env.setenv(name, "   ")

    with pytest.raises(ValidationError):
        AppConfig()


def test_api_key_is_not_exposed_in_repr(app_config: AppConfig) -> None:
    assert "test-key-not-real" not in repr(app_config)
    assert "test-key-not-real" not in str(app_config.model_dump())


def test_optional_values_can_be_overridden(required_env: pytest.MonkeyPatch) -> None:
    required_env.setenv("LLM_MAX_CONCURRENCY", "5")
    required_env.setenv("CHUNK_TOKEN_BUDGET", "8000")
    required_env.setenv("LOG_LEVEL", "DEBUG")

    config = AppConfig()

    assert config.llm_max_concurrency == 5
    assert config.chunk_token_budget == 8000
    assert config.log_level == LogLevel.DEBUG


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("LLM_MAX_CONCURRENCY", "0"),
        ("CHUNK_TOKEN_BUDGET", "0"),
        ("CHUNK_OVERLAP_BLOCKS", "-1"),
        ("MAX_UPLOAD_MB", "0"),
        ("LLM_TEMPERATURE", "-0.1"),
        ("LOG_LEVEL", "LOUD"),
    ],
)
def test_invalid_optional_values_fail_fast(
    required_env: pytest.MonkeyPatch, name: str, value: str
) -> None:
    required_env.setenv(name, value)

    with pytest.raises(ValidationError):
        AppConfig()


def test_config_is_immutable(app_config: AppConfig) -> None:
    with pytest.raises(ValidationError):
        setattr(app_config, "llm_model", "something-else")  # noqa: B010 - bypasses static read-only check on purpose


def test_load_config_returns_config(required_env: pytest.MonkeyPatch) -> None:
    assert load_config().llm_model == "test-primary-model"


def test_load_config_error_names_fields_without_leaking_values(
    required_env: pytest.MonkeyPatch,
) -> None:
    required_env.delenv("LLM_MODEL")
    required_env.setenv("CHUNK_TOKEN_BUDGET", "0")

    with pytest.raises(ConfigurationError) as exc_info:
        load_config()

    message = str(exc_info.value)
    assert "LLM_MODEL" in message
    assert "CHUNK_TOKEN_BUDGET" in message
    assert "test-key-not-real" not in message
    assert "test-fallback-model" not in message
    assert exc_info.value.__cause__ is None
    assert exc_info.value.__suppress_context__
