from __future__ import annotations

import pytest

from doc_checker.verification.quote_matching import clean_quote, find_quote

TEXT = "The maximum detection range is 50 km at an altitude of 3,000 m."


def test_exact_match_returns_offsets_into_text() -> None:
    span = find_quote(TEXT, "detection range is 50 km")

    assert span is not None
    assert TEXT[span[0] : span[1]] == "detection range is 50 km"


def test_whitespace_differences_in_quote_are_tolerated() -> None:
    span = find_quote(TEXT, "range is\n  50   km")

    assert span is not None
    assert TEXT[span[0] : span[1]] == "range is 50 km"


def test_case_differences_are_tolerated() -> None:
    span = find_quote(TEXT, "Maximum Detection Range")

    assert span is not None
    assert TEXT[span[0] : span[1]] == "maximum detection range"


@pytest.mark.parametrize(
    ("text", "quote", "expected"),
    [
        ("The system’s range is 50 km.", "system's range", "system’s range"),
        ("It is “classified” data.", '"classified"', "“classified”"),
        ("Range 40–50 km.", "40-50 km", "40–50 km"),
        ("Speed — Mach 2.", "Speed - Mach 2", "Speed — Mach 2"),
    ],
)
def test_typographic_variants_match_and_return_original_wording(
    text: str, quote: str, expected: str
) -> None:
    span = find_quote(text, quote)

    assert span is not None
    assert text[span[0] : span[1]] == expected


def test_wrapping_quote_marks_added_by_the_model_are_ignored() -> None:
    span = find_quote(TEXT, '"detection range is 50 km"')

    assert span is not None
    assert TEXT[span[0] : span[1]] == "detection range is 50 km"


def test_first_occurrence_wins() -> None:
    text = "50 km here and 50 km there"

    assert find_quote(text, "50 km") == (0, 5)


@pytest.mark.parametrize("quote", ["detection range is 60 km", "", "   ", '""'])
def test_absent_or_empty_quote_returns_none(quote: str) -> None:
    assert find_quote(TEXT, quote) is None


def test_clean_quote_normalizes_and_strips_wrappers() -> None:
    assert clean_quote('  "“max   range\n is 50 km”"  ') == "max range is 50 km"
