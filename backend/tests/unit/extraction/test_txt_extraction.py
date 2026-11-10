from __future__ import annotations

import pytest

from doc_checker.custom_types.document_types import BlockKind
from doc_checker.extraction.document_extraction import extract_document
from doc_checker.extraction.extraction_errors import DocumentParseError


def test_splits_on_blank_lines_and_joins_wrapped_lines() -> None:
    content = b"First para\r\nstill first.\r\n\r\nSecond para.\n\n\n\nThird."

    blocks = extract_document("notes.txt", content).blocks

    assert [block.text for block in blocks] == ["First para still first.", "Second para.", "Third."]
    assert all(block.kind == BlockKind.PARAGRAPH for block in blocks)
    assert all(block.heading_path == () for block in blocks)


def test_utf8_bom_is_stripped() -> None:
    blocks = extract_document("bom.txt", b"\xef\xbb\xbfHello").blocks

    assert blocks[0].text == "Hello"


def test_invalid_utf8_raises_parse_error() -> None:
    with pytest.raises(DocumentParseError):
        extract_document("latin1.txt", b"caf\xe9 \xff")


def test_txt_paragraphs_are_numbered_from_the_start() -> None:
    blocks = extract_document("notes.txt", b"One.\n\n\n\nTwo.\n\nThree.").blocks

    assert [block.section_position for block in blocks] == [1, 2, 3]
