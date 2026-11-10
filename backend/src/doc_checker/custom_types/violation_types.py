from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DropReason(StrEnum):
    UNKNOWN_RULE = "unknown_rule"
    EMPTY_QUOTE = "empty_quote"
    QUOTE_NOT_FOUND = "quote_not_found"


@dataclass(frozen=True)
class CandidateViolation:
    """A violation as reported by the model, not yet checked against the document."""

    rule_id: str
    block_id: str
    quote: str
    explanation: str
    severity: Severity


@dataclass(frozen=True)
class VerifiedViolation:
    """A violation whose quote was found verbatim; `quote == block.text[start:end]`."""

    rule_id: str
    block_id: str
    quote: str
    start: int
    end: int
    explanation: str
    severity: Severity


@dataclass(frozen=True)
class DroppedCandidate:
    candidate: CandidateViolation
    reason: DropReason


@dataclass(frozen=True)
class VerificationResult:
    violations: tuple[VerifiedViolation, ...]
    dropped: tuple[DroppedCandidate, ...]
