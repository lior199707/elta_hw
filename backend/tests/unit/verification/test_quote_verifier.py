from __future__ import annotations

import logging

import pytest

from doc_checker.custom_types.document_types import (
    Block,
    BlockKind,
    DocumentFormat,
    ExtractedDocument,
)
from doc_checker.custom_types.violation_types import (
    CandidateViolation,
    DropReason,
    Severity,
    VerifiedViolation,
)
from doc_checker.verification.quote_verifier import verify_violations

RULES = {"R1", "R2"}

DOCUMENT = ExtractedDocument(
    name="spec.docx",
    document_format=DocumentFormat.DOCX,
    blocks=(
        Block("B1", 1, BlockKind.HEADING, "Radar Specs", ("Radar Specs",)),
        Block("B2", 2, BlockKind.PARAGRAPH, "The detection range is 50 km.", ("Radar Specs",)),
        Block("B3", 3, BlockKind.TABLE_ROW, "Max speed | Mach 2", ("Radar Specs",)),
    ),
)


def candidate(
    quote: str, block_id: str = "B2", rule_id: str = "R1", explanation: str = "why"
) -> CandidateViolation:
    return CandidateViolation(rule_id, block_id, quote, explanation, Severity.HIGH)


def test_valid_candidate_is_kept_with_exact_wording_and_offsets() -> None:
    result = verify_violations([candidate("detection range is 50 KM")], DOCUMENT, RULES)

    assert result.dropped == ()
    assert result.violations == (
        VerifiedViolation("R1", "B2", "detection range is 50 km", 4, 28, "why", Severity.HIGH),
    )


def test_unknown_rule_is_dropped() -> None:
    result = verify_violations([candidate("50 km", rule_id="R9")], DOCUMENT, RULES)

    assert result.violations == ()
    assert [d.reason for d in result.dropped] == [DropReason.UNKNOWN_RULE]


@pytest.mark.parametrize("quote", ["", "   ", '""'])
def test_empty_quote_is_dropped(quote: str) -> None:
    result = verify_violations([candidate(quote)], DOCUMENT, RULES)

    assert [d.reason for d in result.dropped] == [DropReason.EMPTY_QUOTE]


def test_quote_not_in_document_is_dropped_and_logged_without_its_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        result = verify_violations([candidate("range is 80 km")], DOCUMENT, RULES)

    assert result.violations == ()
    assert [d.reason for d in result.dropped] == [DropReason.QUOTE_NOT_FOUND]
    assert caplog.records, "a dropped candidate must be logged"
    assert "80 km" not in caplog.text


@pytest.mark.parametrize("wrong_block_id", ["B2", "B99"])
def test_quote_found_in_another_block_gets_the_correct_block_id(wrong_block_id: str) -> None:
    result = verify_violations([candidate("Mach 2", block_id=wrong_block_id)], DOCUMENT, RULES)

    assert [(v.block_id, v.quote) for v in result.violations] == [("B3", "Mach 2")]


def test_duplicates_from_overlapping_chunks_are_kept_once() -> None:
    first = candidate("50 km", explanation="first")
    second = candidate("50 km", explanation="second")

    result = verify_violations([first, second], DOCUMENT, RULES)

    assert [v.explanation for v in result.violations] == ["first"]


def test_span_inside_a_longer_span_of_the_same_rule_is_removed() -> None:
    result = verify_violations(
        [candidate("50 km"), candidate("detection range is 50 km")], DOCUMENT, RULES
    )

    assert [v.quote for v in result.violations] == ["detection range is 50 km"]


def test_same_span_under_different_rules_is_kept_for_each_rule() -> None:
    result = verify_violations(
        [candidate("50 km", rule_id="R1"), candidate("50 km", rule_id="R2")], DOCUMENT, RULES
    )

    assert sorted(v.rule_id for v in result.violations) == ["R1", "R2"]


def test_violations_are_ordered_by_position_in_document() -> None:
    result = verify_violations(
        [candidate("Mach 2", block_id="B3"), candidate("50 km"), candidate("detection")],
        DOCUMENT,
        RULES,
    )

    assert [v.quote for v in result.violations] == ["detection", "50 km", "Mach 2"]
