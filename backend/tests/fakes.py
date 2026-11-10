"""Test doubles shared across test modules."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.llm_types import LlmCheckOutcome
from doc_checker.custom_types.rule_types import CheckRule
from doc_checker.custom_types.violation_types import CandidateViolation, Severity

Responder = Callable[[Chunk], LlmCheckOutcome | Exception]


def violation(quote: str, block_id: str) -> CandidateViolation:
    return CandidateViolation("R1", block_id, quote, "Reveals performance.", Severity.HIGH)


def outcome(*candidates: CandidateViolation, model: str = "primary") -> LlmCheckOutcome:
    return LlmCheckOutcome(candidates=candidates, model_used=model)


def finds_numbers(chunk: Chunk) -> LlmCheckOutcome:
    found = [
        violation(quote, block.block_id)
        for block in chunk.blocks
        for quote in ("50 km", "Mach 2")
        if quote in block.text
    ]
    return outcome(*found)


@dataclass
class FakeLlm:
    respond: Responder
    delay_seconds: float = 0.0
    calls: list[tuple[Sequence[CheckRule], Chunk]] = field(default_factory=list)
    in_flight: int = 0
    peak_in_flight: int = 0

    async def find_violations(self, rules: Sequence[CheckRule], chunk: Chunk) -> LlmCheckOutcome:
        self.calls.append((rules, chunk))
        self.in_flight += 1
        self.peak_in_flight = max(self.peak_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delay_seconds)
            result = self.respond(chunk)
        finally:
            self.in_flight -= 1
        if isinstance(result, Exception):
            raise result
        return result
