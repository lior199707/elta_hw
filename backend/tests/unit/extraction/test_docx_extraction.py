from __future__ import annotations

import zipfile
from collections.abc import Callable
from io import BytesIO

import pytest
from docx.document import Document as DocxDocument

from doc_checker.custom_types.document_types import Block, BlockKind
from doc_checker.extraction.document_extraction import extract_document
from doc_checker.extraction.extraction_errors import DocumentParseError
from tests.docx_factory import build_docx


def _blocks(populate: Callable[[DocxDocument], object]) -> tuple[Block, ...]:
    content = build_docx(populate)
    return extract_document("spec.docx", content).blocks


def _texts(blocks: tuple[Block, ...]) -> list[str]:
    return [block.text for block in blocks]


def test_headings_and_paragraphs_keep_order_and_heading_paths() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_heading("1 Overview", level=1)
        doc.add_paragraph("Intro text.")
        doc.add_heading("1.1 Purpose", level=2)
        doc.add_paragraph("Purpose text.")
        doc.add_heading("2 Specs", level=1)
        doc.add_paragraph("Specs text.")

    blocks = _blocks(populate)

    assert _texts(blocks) == [
        "1 Overview",
        "Intro text.",
        "1.1 Purpose",
        "Purpose text.",
        "2 Specs",
        "Specs text.",
    ]
    by_text = {block.text: block for block in blocks}
    assert by_text["1 Overview"].kind == BlockKind.HEADING
    assert by_text["Intro text."].heading_path == ("1 Overview",)
    assert by_text["1.1 Purpose"].heading_path == ("1 Overview", "1.1 Purpose")
    assert by_text["Purpose text."].heading_path == ("1 Overview", "1.1 Purpose")
    assert by_text["Specs text."].heading_path == ("2 Specs",)
    assert by_text["Specs text."].kind == BlockKind.PARAGRAPH


def test_title_is_a_heading_block_but_not_part_of_heading_paths() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_heading("System Description", level=0)
        doc.add_heading("1 Overview", level=1)
        doc.add_paragraph("Body.")

    blocks = _blocks(populate)

    assert blocks[0].kind == BlockKind.HEADING
    assert blocks[0].heading_path == ()
    assert blocks[2].heading_path == ("1 Overview",)


def test_table_rows_are_blocks_in_document_order() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_heading("Specs", level=1)
        doc.add_paragraph("Before.")
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Parameter"
        table.cell(0, 1).text = "Value"
        table.cell(1, 0).text = "Detection range"
        table.cell(1, 1).text = "50 km"
        doc.add_paragraph("After.")

    blocks = _blocks(populate)

    assert _texts(blocks) == [
        "Specs",
        "Before.",
        "Parameter | Value",
        "Detection range | 50 km",
        "After.",
    ]
    assert blocks[3].kind == BlockKind.TABLE_ROW
    assert blocks[3].heading_path == ("Specs",)


def test_merged_table_cells_are_not_duplicated() -> None:
    def populate(doc: DocxDocument) -> None:
        table = doc.add_table(rows=1, cols=3)
        merged = table.cell(0, 0).merge(table.cell(0, 1))
        merged.text = "Merged"
        table.cell(0, 2).text = "X"

    assert _texts(_blocks(populate)) == ["Merged | X"]


def test_list_items_are_marked() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_paragraph("First point", style="List Bullet")
        doc.add_paragraph("Second point", style="List Number")

    blocks = _blocks(populate)

    assert [block.kind for block in blocks] == [BlockKind.LIST_ITEM, BlockKind.LIST_ITEM]


def test_empty_paragraphs_are_skipped_and_whitespace_normalized() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_paragraph("")
        doc.add_paragraph("   ")
        doc.add_paragraph("  multiple   spaces\there  ")

    assert _texts(_blocks(populate)) == ["multiple spaces here"]


def test_headers_and_footers_follow_the_body() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_paragraph("Body.")
        doc.sections[0].header.paragraphs[0].text = "CONFIDENTIAL"
        doc.sections[0].footer.paragraphs[0].text = "Rev 3"

    blocks = _blocks(populate)

    assert [(block.kind, block.text) for block in blocks] == [
        (BlockKind.PARAGRAPH, "Body."),
        (BlockKind.HEADER, "CONFIDENTIAL"),
        (BlockKind.FOOTER, "Rev 3"),
    ]


def test_non_zip_bytes_raise_parse_error() -> None:
    with pytest.raises(DocumentParseError):
        extract_document("broken.docx", b"this is not a docx file")


def test_zip_that_is_not_a_docx_raises_parse_error() -> None:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("readme.txt", "hello")

    with pytest.raises(DocumentParseError):
        extract_document("fake.docx", buffer.getvalue())


def test_paragraphs_are_numbered_within_their_section() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_heading("1 Overview", level=1)
        doc.add_paragraph("First.")
        doc.add_paragraph("")
        doc.add_paragraph("Second.", style="List Bullet")
        doc.add_heading("2 Specs", level=1)
        doc.add_paragraph("Third.")

    by_text = {block.text: block for block in _blocks(populate)}

    assert by_text["First."].section_position == 1
    assert by_text["Second."].section_position == 2, "empty paragraphs are not counted"
    assert by_text["Third."].section_position == 1, "numbering restarts at each heading"
    assert by_text["1 Overview"].section_position is None


def test_table_rows_carry_table_number_and_row_number_as_word_counts_them() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_heading("Specs", level=1)
        doc.add_paragraph("Before.")
        first = doc.add_table(rows=3, cols=1)
        first.cell(0, 0).text = "Header"
        first.cell(2, 0).text = "Third row"
        doc.add_paragraph("Between.")
        second = doc.add_table(rows=1, cols=1)
        second.cell(0, 0).text = "Only row"

    by_text = {block.text: block for block in _blocks(populate)}

    assert (by_text["Header"].table_number, by_text["Header"].table_row) == (1, 1)
    assert (by_text["Third row"].table_number, by_text["Third row"].table_row) == (1, 3)
    assert (by_text["Only row"].table_number, by_text["Only row"].table_row) == (2, 1)
    assert by_text["Between."].section_position == 2
    assert by_text["Before."].table_number is None
