from __future__ import annotations

from doc_checker.chunking.block_rendering import estimate_tokens, render_block_line
from doc_checker.custom_types.document_types import Block, BlockKind


def test_renders_id_heading_path_and_text() -> None:
    block = Block("B12", 12, BlockKind.PARAGRAPH, "Range is 50 km.", ("1 Specs", "1.2 Radar"))

    assert render_block_line(block) == "[B12] (1 Specs > 1.2 Radar) Range is 50 km."


def test_renders_without_heading_path() -> None:
    block = Block("B3", 3, BlockKind.PARAGRAPH, "Hello.", ())

    assert render_block_line(block) == "[B3] Hello."


def test_estimates_tokens_as_chars_over_four_rounded_up() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2
