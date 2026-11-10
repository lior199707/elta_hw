"""Score the real model on the sample documents. Run with `uv run poe eval-live` (uses quota).

One request per chunk: easy 1, medium 1, hard 2 at the default budget.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

from doc_checker.config import AppConfig, load_config
from doc_checker.custom_types.check_types import CheckResult, CheckStatus
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.llm.gemini_client import GeminiLlmClient, create_gemini_sdk_client
from doc_checker.repository.default_rules import DEFAULT_RULES
from doc_checker.services.compliance_checker import ComplianceChecker
from tests.fixtures.live_scoring import score_quotes
from tests.fixtures.sample_documents import EASY, SAMPLE_DOCUMENTS, RuleKey, SampleDocument

pytestmark = [pytest.mark.integration, pytest.mark.anyio]

RULE_ID_BY_KEY = {RuleKey.PERFORMANCE: "R1", RuleKey.NAMES: "R2", RuleKey.LOCATIONS: "R3"}
RULES = [
    CheckRule(f"R{position}", title, text)
    for position, (title, text) in enumerate(DEFAULT_RULES, start=1)
]
MIN_RECALL = {"easy": 1.0, "medium": 0.75, "hard": 0.75}


@dataclass(frozen=True)
class Scorecard:
    level: str
    found: list[str]
    missed: list[str]
    false_positives: list[str]
    result: CheckResult

    @property
    def recall(self) -> float:
        total = len(self.found) + len(self.missed)
        return len(self.found) / total if total else 1.0

    def render(self) -> str:
        r = self.result
        return (
            f"\n=== {self.level.upper()}: {r.document_name}\n"
            f"status={r.status} chunks={r.chunks_total} failed={len(r.failed_chunks)} "
            f"models={list(r.models_used)} duration={r.duration_ms} ms\n"
            f"recall={self.recall:.0%} found={self.found}\n"
            f"missed={self.missed}\n"
            f"false_positives={self.false_positives} dropped_unverified={r.dropped_count}\n"
            "reported:\n"
            + "\n".join(f"  {v.rule_id} [{v.severity}] {v.quote!r}" for v in r.violations)
        )


def score(sample: SampleDocument, result: CheckResult) -> Scorecard:
    reported = [(violation.rule_id, violation.quote) for violation in result.violations]
    found, missed, false_positives = score_quotes(sample, reported, RULE_ID_BY_KEY)
    return Scorecard(sample.level, found, missed, false_positives, result)


@pytest.fixture
def live_config() -> AppConfig:
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY is not set")
    return load_config()


@pytest.mark.parametrize("sample", SAMPLE_DOCUMENTS, ids=lambda s: s.level)
async def test_model_finds_planted_violations(
    live_config: AppConfig, sample: SampleDocument
) -> None:
    sdk_client = create_gemini_sdk_client(live_config)
    llm = GeminiLlmClient(
        sdk_client.aio.models,
        primary_model=live_config.llm_model,
        fallback_model=live_config.llm_fallback_model,
        temperature=live_config.llm_temperature,
    )
    checker = ComplianceChecker(
        llm,
        token_budget=live_config.chunk_token_budget,
        overlap_blocks=live_config.chunk_overlap_blocks,
        max_concurrency=live_config.llm_max_concurrency,
    )

    result = await checker.check(sample.filename, sample.build(), RULES)
    card = score(sample, result)
    print(card.render())

    assert result.status == CheckStatus.COMPLETED, result.failed_chunks
    assert card.false_positives == []
    assert card.recall >= MIN_RECALL[sample.level], card.missed
    if sample is EASY:
        assert card.missed == []
