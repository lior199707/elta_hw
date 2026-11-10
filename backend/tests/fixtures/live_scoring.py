"""Scores real model answers against a sample's ground truth.

The prompt asks for the *shortest* quote, so the model may quote "300" for the planted passage
"300 simultaneous tracks". A quote and a phrase therefore match when either contains the other.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from tests.fixtures.sample_documents import RuleKey, SampleDocument

Reported = tuple[str, str]  # (rule_id, quote)


def overlaps(quote: str, phrase: str) -> bool:
    return phrase in quote or quote in phrase


def score_quotes(
    sample: SampleDocument, reported: Sequence[Reported], rule_ids: Mapping[RuleKey, str]
) -> tuple[list[str], list[str], list[str]]:
    """Return (found, missed, false_positives) as `rule_id:text` labels."""
    found: list[str] = []
    missed: list[str] = []
    for planted in sample.planted:
        rule_id = rule_ids[planted.rule]
        hit = any(
            reported_rule == rule_id and overlaps(quote, planted.quote_contains)
            for reported_rule, quote in reported
        )
        (found if hit else missed).append(f"{rule_id}:{planted.quote_contains}")

    false_positives = [
        f"{reported_rule}:{quote}"
        for reported_rule, quote in reported
        if any(overlaps(quote, phrase) for phrase in sample.must_not_flag)
    ]
    return found, missed, false_positives
