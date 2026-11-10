from __future__ import annotations

import pytest

from doc_checker.custom_types.document_types import BlockKind, ExtractedDocument
from doc_checker.extraction.document_extraction import extract_document
from tests.fixtures.sample_documents import (
    HARD,
    HARD_REGISTER_PLANTED,
    HARD_REGISTER_ROWS,
    HARD_SPLIT_PAIR,
    SAMPLE_DOCUMENTS,
    SampleDocument,
)


def extracted(sample: SampleDocument) -> ExtractedDocument:
    return extract_document(sample.filename, sample.build())


@pytest.mark.parametrize("sample", SAMPLE_DOCUMENTS, ids=lambda s: s.level)
def test_every_intact_sentence_is_in_exactly_one_block(sample: SampleDocument) -> None:
    blocks = extracted(sample).blocks

    for sentence in sample.intact_sentences:
        holders = [block.block_id for block in blocks if sentence in block.text]
        assert len(holders) == 1, f"{sentence!r} found in {holders}"


@pytest.mark.parametrize("sample", SAMPLE_DOCUMENTS, ids=lambda s: s.level)
def test_every_planted_violation_text_is_extracted(sample: SampleDocument) -> None:
    text = "\n".join(block.text for block in extracted(sample).blocks)

    missing = [p.quote_contains for p in sample.planted if p.quote_contains not in text]
    assert missing == []


@pytest.mark.parametrize("sample", SAMPLE_DOCUMENTS, ids=lambda s: s.level)
def test_blocks_are_numbered_sequentially_and_never_empty(sample: SampleDocument) -> None:
    blocks = extracted(sample).blocks

    assert [block.index for block in blocks] == list(range(1, len(blocks) + 1))
    assert [block.block_id for block in blocks] == [f"B{i}" for i in range(1, len(blocks) + 1)]
    assert all(block.text.strip() for block in blocks)


def test_hard_page_break_paragraphs_produce_no_blocks() -> None:
    blocks = extracted(HARD).blocks

    assert all(block.text == block.text.strip() and block.text for block in blocks)
    first, second = HARD_SPLIT_PAIR
    first_block = next(block for block in blocks if block.text == first)
    second_block = next(block for block in blocks if block.text == second)
    assert second_block.index == first_block.index + 1, "page-break paragraph left a block"


def test_hard_long_table_rows_are_blocks_under_their_section() -> None:
    rows = [block for block in extracted(HARD).blocks if block.kind == BlockKind.TABLE_ROW]
    register = [row for row in rows if row.heading_path == ("23 Maintenance procedure 23",)]

    assert len(register) == HARD_REGISTER_ROWS + 1
    assert register[0].text == "Item | Value"
    assert " | ".join(HARD_REGISTER_PLANTED) in [row.text for row in register]


def test_hard_header_and_footer_appear_once_after_the_body() -> None:
    blocks = extracted(HARD).blocks

    headers = [block for block in blocks if block.kind == BlockKind.HEADER]
    footers = [block for block in blocks if block.kind == BlockKind.FOOTER]
    assert [block.text for block in headers] == ["Sentinel-7 Field Trial Report - Restricted"]
    assert [block.text for block in footers] == ["Prepared for internal review"]
    assert blocks[-1].kind in (BlockKind.HEADER, BlockKind.FOOTER)


def test_hard_merged_signature_cell_is_not_duplicated() -> None:
    blocks = extracted(HARD).blocks

    assert "Prepared by: Noa Levinson, field trial engineer" in [block.text for block in blocks]


def test_hard_planted_register_row_is_located_as_word_shows_it() -> None:
    planted = next(
        block for block in extracted(HARD).blocks if block.text == " | ".join(HARD_REGISTER_PLANTED)
    )

    # Row 1 is the header, so data row 60 is the table's 61st row.
    assert (planted.table_number, planted.table_row) == (1, 61)
