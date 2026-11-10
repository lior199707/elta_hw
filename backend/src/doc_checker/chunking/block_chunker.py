from __future__ import annotations

import logging
from collections.abc import Sequence

from doc_checker.chunking.block_rendering import estimate_tokens, render_block_line
from doc_checker.constants import CHUNK_ID_PREFIX
from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.document_types import Block

logger = logging.getLogger(__name__)


def build_chunks(
    blocks: Sequence[Block], token_budget: int, overlap_blocks: int
) -> tuple[Chunk, ...]:
    """Pack consecutive blocks into chunks of at most `token_budget` estimated tokens.

    Each chunk after the first starts with up to `overlap_blocks` blocks from the end of the
    previous one, so text near a boundary is always seen whole. The overlap shrinks when it would
    leave no room for a new block. A block larger than the budget gets a chunk of its own.

    Raises ValueError when `token_budget < 1` or `overlap_blocks < 0`.
    """
    if token_budget < 1:
        raise ValueError(f"token_budget must be >= 1, got {token_budget}")
    if overlap_blocks < 0:
        raise ValueError(f"overlap_blocks must be >= 0, got {overlap_blocks}")

    costs = [estimate_tokens(render_block_line(block)) for block in blocks]
    _warn_about_oversized_blocks(blocks, costs, token_budget)

    chunks: list[Chunk] = []
    start = 0
    while start < len(blocks):
        end = _fill_end(costs, start, token_budget)
        index = len(chunks) + 1
        chunks.append(
            Chunk(
                chunk_id=f"{CHUNK_ID_PREFIX}{index}",
                index=index,
                blocks=tuple(blocks[start:end]),
                estimated_tokens=sum(costs[start:end]),
            )
        )
        if end == len(blocks):
            break
        start = end - _fitting_overlap(costs, start, end, token_budget, overlap_blocks)
    return tuple(chunks)


def _fill_end(costs: list[int], start: int, token_budget: int) -> int:
    """Exclusive end of the chunk starting at `start`; always takes at least one block."""
    end = start + 1
    total = costs[start]
    while end < len(costs) and total + costs[end] <= token_budget:
        total += costs[end]
        end += 1
    return end


def _fitting_overlap(
    costs: list[int], start: int, end: int, token_budget: int, overlap_blocks: int
) -> int:
    """Largest overlap that still leaves room for the next new block (so the loop progresses)."""
    overlap = min(overlap_blocks, end - start - 1)
    while overlap > 0 and sum(costs[end - overlap : end]) + costs[end] > token_budget:
        overlap -= 1
    return overlap


def _warn_about_oversized_blocks(
    blocks: Sequence[Block], costs: list[int], token_budget: int
) -> None:
    for block, block_cost in zip(blocks, costs, strict=True):
        if block_cost > token_budget:
            logger.warning(
                "block exceeds chunk token budget, sending it alone",
                extra={
                    "block_id": block.block_id,
                    "estimated_tokens": block_cost,
                    "token_budget": token_budget,
                },
            )
