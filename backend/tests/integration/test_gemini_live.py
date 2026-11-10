"""Live Gemini calls. Run with `uv run poe test-integration` (reads ../.env, uses real quota)."""

from __future__ import annotations

import os

import pytest

from doc_checker.chunking.block_chunker import build_chunks
from doc_checker.config import AppConfig, load_config
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.extraction.document_extraction import extract_document
from doc_checker.llm.gemini_client import GeminiLlmClient, create_gemini_sdk_client
from doc_checker.verification.quote_verifier import verify_violations
from tests.docx_factory import build_docx

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

PERFORMANCE_RULE = CheckRule(
    "R1",
    "No performance figures",
    "The document must not contain any numeric value that reveals the performance of the system.",
)


@pytest.fixture
def live_config() -> AppConfig:
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY is not set")
    return load_config()


@pytest.mark.parametrize("setting", ["llm_model", "llm_fallback_model"])
async def test_configured_model_answers(live_config: AppConfig, setting: str) -> None:
    """A real call, because `models.list` still lists models this key can no longer call."""
    model = getattr(live_config, setting)
    client = create_gemini_sdk_client(live_config)

    response = await client.aio.models.generate_content(model=model, contents="Reply with: ok")

    assert response.text, f"{setting}={model!r} returned no text"


async def test_detects_numeric_performance_disclosure_end_to_end(live_config: AppConfig) -> None:
    content = build_docx(
        lambda doc: (
            doc.add_heading("System Overview", level=1),
            doc.add_paragraph("Document version 2.1, issued in March 2024."),
            doc.add_paragraph("The system is mounted on a standard vehicle platform."),
            doc.add_heading("Performance", level=1),
            doc.add_paragraph("The maximum detection range is 50 km."),
        )
    )
    document = extract_document("system.docx", content)
    chunks = build_chunks(document.blocks, live_config.chunk_token_budget, 0)
    sdk_client = create_gemini_sdk_client(live_config)
    llm = GeminiLlmClient(
        sdk_client.aio.models,
        primary_model=live_config.llm_model,
        fallback_model=live_config.llm_fallback_model,
        temperature=live_config.llm_temperature,
    )

    outcome = await llm.find_violations([PERFORMANCE_RULE], chunks[0])
    result = verify_violations(outcome.candidates, document, {PERFORMANCE_RULE.rule_id})

    quotes = [violation.quote for violation in result.violations]
    print(f"\nmodel={outcome.model_used} quotes={quotes} dropped={len(result.dropped)}")
    assert any("50 km" in quote for quote in quotes)
    assert not any("2024" in quote or "2.1" in quote for quote in quotes)
