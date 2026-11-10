from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlmodel import Session

from doc_checker.config import AppConfig
from doc_checker.constants import SQLITE_MEMORY_DATABASE
from doc_checker.main import create_app
from doc_checker.repository.database import create_db_engine, init_database
from tests.fakes import FakeLlm, finds_numbers

REQUIRED_ENV = {
    "GEMINI_API_KEY": "test-key-not-real",
    "LLM_MODEL": "test-primary-model",
    "LLM_FALLBACK_MODEL": "test-fallback-model",
}


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Remove every AppConfig variable from the process env so tests never see a real .env."""
    for field_name in AppConfig.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)
    return monkeypatch


@pytest.fixture
def required_env(clean_env: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for name, value in REQUIRED_ENV.items():
        clean_env.setenv(name, value)
    return clean_env


@pytest.fixture
def app_config(required_env: pytest.MonkeyPatch) -> AppConfig:
    return AppConfig()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def engine() -> Engine:
    return create_db_engine(f"sqlite:///{SQLITE_MEMORY_DATABASE}")


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    init_database(engine)
    with Session(engine) as db_session:
        yield db_session


@pytest.fixture
def fake_llm() -> FakeLlm:
    return FakeLlm(finds_numbers)


@pytest.fixture
def client(app_config: AppConfig, fake_llm: FakeLlm, engine: Engine) -> Iterator[TestClient]:
    with TestClient(create_app(app_config, llm=fake_llm, engine=engine)) as test_client:
        yield test_client
