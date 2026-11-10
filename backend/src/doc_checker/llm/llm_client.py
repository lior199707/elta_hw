from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.llm_types import LlmCheckOutcome
from doc_checker.custom_types.rule_types import CheckRule


class LlmClient(Protocol):
    async def find_violations(self, rules: Sequence[CheckRule], chunk: Chunk) -> LlmCheckOutcome:
        """Ask the model which passages of `chunk` violate `rules`.

        Raises an LlmError subtype on any failure; never returns a partial or guessed result.
        """
        ...
