from __future__ import annotations

from dataclasses import dataclass

from doc_checker.custom_types.violation_types import CandidateViolation


@dataclass(frozen=True)
class LlmCheckOutcome:
    candidates: tuple[CandidateViolation, ...]
    model_used: str
    used_fallback: bool = False
