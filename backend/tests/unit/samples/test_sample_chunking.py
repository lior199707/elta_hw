from __future__ import annotations

import pytest

from doc_checker.chunking.block_chunker import build_chunks
from doc_checker.config import AppConfig
from doc_checker.extraction.document_extraction import extract_document
from tests.fixtures.sample_documents import EASY, HARD, MEDIUM, SampleDocument

DEFAULT_BUDGET = AppConfig.model_fields["chunk_token_budget"].default
DEFAULT_OVERLAP = AppConfig.model_fields["chunk_overlap_blocks"].default
BUDGETS = (2_000, 8_000, DEFAULT_BUDGET)


@pytest.mark.parametrize("sample", [EASY, MEDIUM], ids=lambda s: s.level)
def test_small_documents_fit_in_one_chunk_at_the_default_budget(sample: SampleDocument) -> None:
    blocks = extract_document(sample.filename, sample.build()).blocks

    assert len(build_chunks(blocks, DEFAULT_BUDGET, DEFAULT_OVERLAP)) == 1


def test_hard_document_needs_several_chunks_at_the_default_budget() -> None:
    blocks = extract_document(HARD.filename, HARD.build()).blocks

    assert len(build_chunks(blocks, DEFAULT_BUDGET, DEFAULT_OVERLAP)) >= 2


@pytest.mark.parametrize("budget", BUDGETS)
def test_hard_chunks_cover_every_block_within_budget(budget: int) -> None:
    blocks = extract_document(HARD.filename, HARD.build()).blocks

    chunks = build_chunks(blocks, budget, DEFAULT_OVERLAP)

    covered = {block.block_id for chunk in chunks for block in chunk.blocks}
    assert covered == {block.block_id for block in blocks}
    assert all(chunk.estimated_tokens <= budget for chunk in chunks)
    for previous, current in zip(chunks, chunks[1:], strict=False):
        shared = previous.blocks[-1].index - current.blocks[0].index + 1
        assert shared == DEFAULT_OVERLAP, "consecutive chunks must share the configured overlap"


@pytest.mark.parametrize("budget", BUDGETS)
def test_statement_split_around_a_page_break_is_seen_whole_in_some_chunk(budget: int) -> None:
    assert HARD.split_pair is not None
    blocks = extract_document(HARD.filename, HARD.build()).blocks

    chunks = build_chunks(blocks, budget, DEFAULT_OVERLAP)

    first, second = HARD.split_pair
    together = [
        chunk.chunk_id
        for chunk in chunks
        if {first, second} <= {block.text for block in chunk.blocks}
    ]
    assert together, "the two halves never appear in the same chunk"


@pytest.mark.parametrize("budget", BUDGETS)
def test_every_planted_violation_reaches_the_model_inside_a_chunk(budget: int) -> None:
    blocks = extract_document(HARD.filename, HARD.build()).blocks

    chunks = build_chunks(blocks, budget, DEFAULT_OVERLAP)

    chunk_texts = ["\n".join(block.text for block in chunk.blocks) for chunk in chunks]
    for planted in HARD.planted:
        assert any(planted.quote_contains in text for text in chunk_texts), planted
