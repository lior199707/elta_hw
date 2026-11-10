from __future__ import annotations

import logging

import pytest

from doc_checker.chunking.block_chunker import build_chunks
from doc_checker.chunking.block_rendering import estimate_tokens, render_block_line
from doc_checker.custom_types.chunk_types import Chunk
from doc_checker.custom_types.document_types import Block, BlockKind


def make_blocks(text_lengths: list[int]) -> list[Block]:
    return [
        Block(f"B{i}", i, BlockKind.PARAGRAPH, "x" * length, ())
        for i, length in enumerate(text_lengths, start=1)
    ]


def cost(block: Block) -> int:
    return estimate_tokens(render_block_line(block))


def ids(chunks: tuple[Chunk, ...]) -> list[list[str]]:
    return [[block.block_id for block in chunk.blocks] for chunk in chunks]


def test_no_blocks_gives_no_chunks() -> None:
    assert build_chunks([], token_budget=100, overlap_blocks=2) == ()


def test_small_document_fits_in_one_chunk() -> None:
    blocks = make_blocks([20, 20, 20])

    chunks = build_chunks(blocks, token_budget=1000, overlap_blocks=2)

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "C1"
    assert chunks[0].index == 1
    assert chunks[0].blocks == tuple(blocks)
    assert chunks[0].estimated_tokens == sum(cost(block) for block in blocks)


def test_consecutive_chunks_share_exactly_the_overlap() -> None:
    blocks = make_blocks([15] * 9)  # "[Bn] " + 15 chars = 20 chars = 5 tokens each
    budget = 4 * cost(blocks[0])

    chunks = build_chunks(blocks, token_budget=budget, overlap_blocks=2)

    assert ids(chunks) == [
        ["B1", "B2", "B3", "B4"],
        ["B3", "B4", "B5", "B6"],
        ["B5", "B6", "B7", "B8"],
        ["B7", "B8", "B9"],
    ]
    assert [chunk.chunk_id for chunk in chunks] == ["C1", "C2", "C3", "C4"]


def test_zero_overlap_partitions_the_blocks() -> None:
    blocks = make_blocks([15] * 9)

    chunks = build_chunks(blocks, token_budget=4 * cost(blocks[0]), overlap_blocks=0)

    assert ids(chunks) == [["B1", "B2", "B3", "B4"], ["B5", "B6", "B7", "B8"], ["B9"]]


def test_overlap_shrinks_so_every_chunk_adds_a_new_block() -> None:
    blocks = make_blocks([15] * 4)

    chunks = build_chunks(blocks, token_budget=2 * cost(blocks[0]), overlap_blocks=2)

    assert ids(chunks) == [["B1", "B2"], ["B2", "B3"], ["B3", "B4"]]


def test_oversized_block_gets_its_own_chunk_and_a_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    blocks = make_blocks([15, 400, 15])
    budget = 3 * cost(blocks[0])

    with caplog.at_level(logging.WARNING):
        chunks = build_chunks(blocks, token_budget=budget, overlap_blocks=1)

    assert ids(chunks) == [["B1"], ["B2"], ["B3"]]
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert warnings[0].__dict__["block_id"] == "B2"


@pytest.mark.parametrize("token_budget", [1, 5, 12, 40, 10_000])
@pytest.mark.parametrize("overlap_blocks", [0, 1, 2, 5])
def test_invariants_hold_for_mixed_block_sizes(token_budget: int, overlap_blocks: int) -> None:
    blocks = make_blocks([3, 50, 7, 120, 1, 1, 30, 200, 9, 60, 2, 44])

    chunks = build_chunks(blocks, token_budget=token_budget, overlap_blocks=overlap_blocks)

    covered = [block for chunk in chunks for block in chunk.blocks]
    assert list(dict.fromkeys(covered)) == blocks, "every block covered, in order"
    for chunk in chunks:
        assert chunk.estimated_tokens == sum(cost(block) for block in chunk.blocks)
        assert chunk.estimated_tokens <= token_budget or len(chunk.blocks) == 1
    for previous, current in zip(chunks, chunks[1:], strict=False):
        assert current.blocks[-1].index > previous.blocks[-1].index, "progress"
        assert current.blocks[0].index <= previous.blocks[-1].index + 1, "no gaps"
        shared = previous.blocks[-1].index - current.blocks[0].index + 1
        assert 0 <= shared <= overlap_blocks


@pytest.mark.parametrize(("token_budget", "overlap_blocks"), [(0, 1), (-5, 1), (100, -1)])
def test_invalid_arguments_fail_fast(token_budget: int, overlap_blocks: int) -> None:
    with pytest.raises(ValueError):
        build_chunks(make_blocks([10]), token_budget=token_budget, overlap_blocks=overlap_blocks)
