from __future__ import annotations

from tests.fixtures.live_scoring import Reported, overlaps, score_quotes
from tests.fixtures.sample_documents import (
    MEDIUM,
    PlantedViolation,
    RuleKey,
    SampleDocument,
)

RULE_IDS = {RuleKey.PERFORMANCE: "R1", RuleKey.NAMES: "R2", RuleKey.LOCATIONS: "R3"}


def test_overlap_counts_either_direction_but_not_disjoint_text() -> None:
    assert overlaps("300", "300 simultaneous tracks")
    assert overlaps("Kestrel Ridge test site", "Kestrel Ridge")
    assert not overlaps("120 km", "0.5 degrees")


def test_minimal_quote_of_a_planted_passage_counts_as_found() -> None:
    # Real gemini-3.5-flash answer for the medium sample (2026-11-10).
    reported: list[Reported] = [
        ("R2", "Dana Mizrahi"),
        ("R2", "Yossi Ben-Ami"),
        ("R1", "120 km"),
        ("R1", "0.5 degrees"),
        ("R1", "300"),
        ("R3", "Kestrel Ridge test site"),
    ]

    found, missed, false_positives = score_quotes(MEDIUM, reported, RULE_IDS)

    assert missed == []
    assert len(found) == len(MEDIUM.planted)
    assert false_positives == []


def test_wrong_rule_does_not_count_as_found() -> None:
    sample = SampleDocument(
        level="t",
        filename="t.docx",
        build=lambda: b"",
        planted=(PlantedViolation(RuleKey.NAMES, "Dana Mizrahi"),),
        must_not_flag=(),
        intact_sentences=(),
    )

    _, missed, _ = score_quotes(sample, [("R1", "Dana Mizrahi")], RULE_IDS)

    assert missed == ["R2:Dana Mizrahi"]


def test_short_quote_inside_a_must_not_flag_phrase_is_a_false_positive() -> None:
    _, _, false_positives = score_quotes(MEDIUM, [("R1", "2024")], RULE_IDS)

    assert false_positives == ["R1:2024"]
