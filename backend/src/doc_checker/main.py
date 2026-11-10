from __future__ import annotations

import logging

from fastapi import FastAPI
from sqlalchemy import Engine

from doc_checker.api.checks_router import router as checks_router
from doc_checker.api.error_handlers import register_error_handlers
from doc_checker.api.health_router import router as health_router
from doc_checker.api.rules_router import router as rules_router
from doc_checker.config import AppConfig, load_config
from doc_checker.constants import API_PREFIX, APP_TITLE, APPLICATION_NAME
from doc_checker.llm.gemini_client import GeminiLlmClient, create_gemini_sdk_client
from doc_checker.llm.llm_client import LlmClient
from doc_checker.logging_config import configure_logging
from doc_checker.repository.database import create_db_engine, init_database
from doc_checker.services.compliance_checker import ComplianceChecker

logger = logging.getLogger(__name__)


def create_app(config: AppConfig, llm: LlmClient, engine: Engine) -> FastAPI:
    """Wire the app from already-built infrastructure (tests pass a fake LLM and in-memory DB)."""
    init_database(engine)

    app = FastAPI(title=APP_TITLE)
    app.state.config = config
    app.state.engine = engine
    app.state.checker = ComplianceChecker(
        llm,
        token_budget=config.chunk_token_budget,
        overlap_blocks=config.chunk_overlap_blocks,
        max_concurrency=config.llm_max_concurrency,
    )
    register_error_handlers(app)
    for router in (health_router, rules_router, checks_router):
        app.include_router(router, prefix=API_PREFIX)
    return app


def build_app() -> FastAPI:
    """Uvicorn factory entrypoint: `uvicorn doc_checker.main:build_app --factory`."""
    config = load_config()
    configure_logging(APPLICATION_NAME, config.log_level)

    sdk_client = create_gemini_sdk_client(config)
    llm = GeminiLlmClient(
        sdk_client.aio.models,
        primary_model=config.llm_model,
        fallback_model=config.llm_fallback_model,
        temperature=config.llm_temperature,
    )
    app = create_app(config, llm=llm, engine=create_db_engine(config.database_url))
    # Keeps the SDK client (and its HTTP connection pool) alive as long as the app.
    app.state.gemini_sdk_client = sdk_client
    logger.info(
        "application configured",
        extra={"llm_model": config.llm_model, "llm_fallback_model": config.llm_fallback_model},
    )
    return app
