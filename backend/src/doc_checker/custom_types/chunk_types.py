from __future__ import annotations

from dataclasses import dataclass

from doc_checker.custom_types.document_types import Block


@dataclass(frozen=True)
class Chunk:
    """Consecutive blocks sent to the model in one request. `index` is 1-based."""

    chunk_id: str
    index: int
    blocks: tuple[Block, ...]
    estimated_tokens: int
