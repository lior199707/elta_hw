from __future__ import annotations

import pytest

from doc_checker.custom_types.check_types import CheckStatus, ChunkFailureReason
from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.llm_types import LlmCheckOutcome
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.extraction.extraction_errors import UnsupportedDocumentTypeError
from doc_checker.llm.llm_errors import (
    LlmBlockedError,
    LlmOverloadedError,
    LlmQuotaExceededError,
    LlmResponseError,
    LlmTimeoutError,
    LlmUnavailableError,
)
from doc_checker.services.compliance_checker import ComplianceChecker, NoRulesSelectedError
from tests.fakes import FakeLlm, finds_numbers, outcome, violation

pytestmark = pytest.mark.anyio

RULES = [CheckRule("R1", "No performance numbers", "Do not disclose numeric performance.")]
# Rendered costs: "[B1] Intro." = 3 tokens, "[B2] Range is 50 km." = 5, "[B3] Speed is Mach 2." = 6.
DOCUMENT = b"Intro.\n\nRange is 50 km.\n\nSpeed is Mach 2."
ONE_CHUNK_BUDGET = 1000
ONE_BLOCK_PER_CHUNK_BUDGET = 6


def make_checker(
    llm: FakeLlm, token_budget: int = ONE_CHUNK_BUDGET, overlap: int = 0, concurrency: int = 2
) -> ComplianceChecker:
    return ComplianceChecker(
        llm, token_budget=token_budget, overlap_blocks=overlap, max_concurrency=concurrency
    )


async def test_completed_check_returns_verified_violations_with_context() -> None:
    llm = FakeLlm(finds_numbers)

    result = await make_checker(llm).check("spec.txt", DOCUMENT, RULES)

    assert result.status == CheckStatus.COMPLETED
    assert [(v.block_id, v.quote) for v in result.violations] == [("B2", "50 km"), ("B3", "Mach 2")]
    assert [block.block_id for block in result.context_blocks] == ["B2", "B3"]
    assert result.document_name == "spec.txt"
    assert result.rules == tuple(RULES)
    assert result.block_count == 3
    assert result.chunks_total == 1
    assert result.failed_chunks == ()
    assert result.dropped_count == 0
    assert result.models_used == ("primary",)
    assert result.duration_ms >= 0


async def test_no_rules_fails_fast_without_calling_the_model() -> None:
    llm = FakeLlm(finds_numbers)

    with pytest.raises(NoRulesSelectedError):
        await make_checker(llm).check("spec.txt", DOCUMENT, [])
    assert llm.calls == []


async def test_extraction_errors_propagate_without_calling_the_model() -> None:
    llm = FakeLlm(finds_numbers)

    with pytest.raises(UnsupportedDocumentTypeError):
        await make_checker(llm).check("spec.pdf", DOCUMENT, RULES)
    assert llm.calls == []


async def test_every_chunk_is_sent_with_all_rules() -> None:
    llm = FakeLlm(finds_numbers)

    result = await make_checker(llm, token_budget=ONE_BLOCK_PER_CHUNK_BUDGET).check(
        "spec.txt", DOCUMENT, RULES
    )

    assert result.chunks_total == 3
    sent = sorted(block.block_id for _, chunk in llm.calls for block in chunk.blocks)
    assert sent == ["B1", "B2", "B3"]
    assert all(list(rules) == RULES for rules, _ in llm.calls)


async def test_a_failed_chunk_makes_the_result_partial_and_keeps_other_findings() -> None:
    def blocked_on_b3(chunk: Chunk) -> LlmCheckOutcome | Exception:
        if chunk.blocks[0].block_id == "B3":
            return LlmBlockedError("blocked")
        return finds_numbers(chunk)

    llm = FakeLlm(blocked_on_b3)

    result = await make_checker(llm, token_budget=ONE_BLOCK_PER_CHUNK_BUDGET).check(
        "spec.txt", DOCUMENT, RULES
    )

    assert result.status == CheckStatus.PARTIAL
    assert [v.quote for v in result.violations] == ["50 km"]
    assert len(result.failed_chunks) == 1
    failed = result.failed_chunks[0]
    assert (failed.first_block_id, failed.last_block_id) == ("B3", "B3")
    assert failed.reason == ChunkFailureReason.BLOCKED


async def test_all_chunks_failing_makes_the_result_failed() -> None:
    llm = FakeLlm(lambda chunk: LlmQuotaExceededError("quota"))

    result = await make_checker(llm, token_budget=ONE_BLOCK_PER_CHUNK_BUDGET).check(
        "spec.txt", DOCUMENT, RULES
    )

    assert result.status == CheckStatus.FAILED
    assert result.violations == ()
    assert len(result.failed_chunks) == 3
    assert result.models_used == ()


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (LlmQuotaExceededError("x"), ChunkFailureReason.QUOTA_EXCEEDED),
        (LlmOverloadedError("x"), ChunkFailureReason.OVERLOADED),
        (LlmTimeoutError("x"), ChunkFailureReason.TIMEOUT),
        (LlmBlockedError("x"), ChunkFailureReason.BLOCKED),
        (LlmResponseError("x"), ChunkFailureReason.INVALID_RESPONSE),
        (LlmUnavailableError("x"), ChunkFailureReason.UNAVAILABLE),
    ],
)
async def test_llm_errors_map_to_failure_reasons(
    error: Exception, reason: ChunkFailureReason
) -> None:
    result = await make_checker(FakeLlm(lambda chunk: error)).check("spec.txt", DOCUMENT, RULES)

    assert result.failed_chunks[0].reason == reason
    assert result.failed_chunks[0].message == "x"


async def test_unexpected_exceptions_propagate() -> None:
    llm = FakeLlm(lambda chunk: RuntimeError("bug"))

    with pytest.raises(RuntimeError):
        await make_checker(llm).check("spec.txt", DOCUMENT, RULES)


async def test_concurrency_never_exceeds_the_limit() -> None:
    many_paragraphs = "\n\n".join(f"Paragraph number {i} is here." for i in range(8)).encode()
    llm = FakeLlm(lambda chunk: outcome(), delay_seconds=0.01)

    await make_checker(llm, token_budget=10, concurrency=2).check(
        "long.txt", many_paragraphs, RULES
    )

    assert len(llm.calls) == 8
    assert llm.peak_in_flight == 2


async def test_hallucinated_quotes_are_dropped_and_counted() -> None:
    llm = FakeLlm(lambda chunk: outcome(violation("range is 80 km", "B2")))

    result = await make_checker(llm).check("spec.txt", DOCUMENT, RULES)

    assert result.violations == ()
    assert result.dropped_count == 1
    assert result.status == CheckStatus.COMPLETED


async def test_duplicates_from_overlapping_chunks_are_reported_once() -> None:
    llm = FakeLlm(finds_numbers)

    result = await make_checker(llm, token_budget=11, overlap=1).check("spec.txt", DOCUMENT, RULES)

    assert result.chunks_total > 1
    assert [v.quote for v in result.violations] == ["50 km", "Mach 2"]


async def test_models_used_lists_every_model_that_answered() -> None:
    def fallback_on_b2(chunk: Chunk) -> LlmCheckOutcome:
        model = "fallback" if chunk.blocks[0].block_id == "B2" else "primary"
        return outcome(model=model)

    result = await make_checker(
        FakeLlm(fallback_on_b2), token_budget=ONE_BLOCK_PER_CHUNK_BUDGET
    ).check("spec.txt", DOCUMENT, RULES)

    assert result.models_used == ("fallback", "primary")


async def test_fallback_chunk_count_reports_chunks_answered_by_the_fallback() -> None:
    def fallback_on_b2(chunk: Chunk) -> LlmCheckOutcome:
        used_fallback = chunk.blocks[0].block_id == "B2"
        return LlmCheckOutcome(
            candidates=(),
            model_used="fallback" if used_fallback else "primary",
            used_fallback=used_fallback,
        )

    result = await make_checker(
        FakeLlm(fallback_on_b2), token_budget=ONE_BLOCK_PER_CHUNK_BUDGET
    ).check("spec.txt", DOCUMENT, RULES)

    assert result.fallback_chunk_count == 1


async def test_result_records_whether_the_document_has_a_saved_page_layout() -> None:
    result = await make_checker(FakeLlm(finds_numbers)).check("spec.txt", DOCUMENT, RULES)

    assert result.has_page_layout is False
