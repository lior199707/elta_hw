from __future__ import annotations

import logging
from collections.abc import Collection, Iterator, Sequence

from doc_checker.custom_types.document_types import Block, ExtractedDocument
from doc_checker.custom_types.violation_types import (
    CandidateViolation,
    DroppedCandidate,
    DropReason,
    VerificationResult,
    VerifiedViolation,
)
from doc_checker.verification.quote_matching import clean_quote, find_quote

logger = logging.getLogger(__name__)


def verify_violations(
    candidates: Sequence[CandidateViolation],
    document: ExtractedDocument,
    rule_ids: Collection[str],
) -> VerificationResult:
    """Keep only candidates whose rule exists and whose quote appears in the document.

    The referenced block is searched first, then the whole document (the block id is corrected).
    Duplicates and spans contained in a longer span (same rule, same block) are removed.
    Kept violations are ordered by position in the document.
    """
    verified: list[VerifiedViolation] = []
    dropped: list[DroppedCandidate] = []
    for candidate in candidates:
        outcome = _verify_candidate(candidate, document, rule_ids)
        if isinstance(outcome, VerifiedViolation):
            verified.append(outcome)
            continue
        dropped.append(DroppedCandidate(candidate, outcome))
        # The quote is document content, so only identifiers are logged.
        logger.warning(
            "candidate violation dropped",
            extra={"rule_id": candidate.rule_id, "block_id": candidate.block_id, "reason": outcome},
        )

    violations = _deduplicate(verified, document)
    logger.info(
        "violations verified",
        extra={
            "candidate_count": len(candidates),
            "kept_count": len(violations),
            "dropped_count": len(dropped),
        },
    )
    return VerificationResult(violations=violations, dropped=tuple(dropped))


def _verify_candidate(
    candidate: CandidateViolation, document: ExtractedDocument, rule_ids: Collection[str]
) -> VerifiedViolation | DropReason:
    if candidate.rule_id not in rule_ids:
        return DropReason.UNKNOWN_RULE
    if not clean_quote(candidate.quote):
        return DropReason.EMPTY_QUOTE
    for block in _search_order(candidate.block_id, document):
        span = find_quote(block.text, candidate.quote)
        if span is not None:
            start, end = span
            return VerifiedViolation(
                rule_id=candidate.rule_id,
                block_id=block.block_id,
                quote=block.text[start:end],
                start=start,
                end=end,
                explanation=candidate.explanation,
                severity=candidate.severity,
            )
    return DropReason.QUOTE_NOT_FOUND


def _search_order(block_id: str, document: ExtractedDocument) -> Iterator[Block]:
    referenced = [block for block in document.blocks if block.block_id == block_id]
    yield from referenced
    yield from (block for block in document.blocks if block.block_id != block_id)


def _deduplicate(
    violations: list[VerifiedViolation], document: ExtractedDocument
) -> tuple[VerifiedViolation, ...]:
    unique: dict[tuple[str, str, int, int], VerifiedViolation] = {}
    for violation in violations:
        key = (violation.rule_id, violation.block_id, violation.start, violation.end)
        unique.setdefault(key, violation)

    remaining = list(unique.values())
    outermost = [v for v in remaining if not any(_contains(o, v) for o in remaining if o is not v)]

    position = {block.block_id: block.index for block in document.blocks}
    return tuple(sorted(outermost, key=lambda v: (position[v.block_id], v.start, v.rule_id)))


def _contains(outer: VerifiedViolation, inner: VerifiedViolation) -> bool:
    return (
        outer.rule_id == inner.rule_id
        and outer.block_id == inner.block_id
        and outer.start <= inner.start
        and inner.end <= outer.end
    )
