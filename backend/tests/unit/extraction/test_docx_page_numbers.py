"""Page numbers come from `w:lastRenderedPageBreak`, the markers Word saves for its layout."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from docx.document import Document as DocxDocument
from docx.oxml import OxmlElement
from docx.text.run import Run

from doc_checker.custom_types.document_types import Block, BlockKind
from doc_checker.extraction.document_extraction import extract_document
from tests.docx_factory import build_docx


def rendered_break_before_text(run: Run) -> Run:
    """Mimic Word: the marker sits inside the run, before the text that starts the new page."""
    run._r.insert(0, OxmlElement("w:lastRenderedPageBreak"))
    return run


def pages_by_text(populate: Callable[[DocxDocument], object]) -> dict[str, int | None]:
    blocks: tuple[Block, ...] = extract_document("word-saved.docx", build_docx(populate)).blocks
    return {block.text: block.page for block in blocks}


def test_document_without_saved_layout_has_no_page_numbers() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_paragraph("One.")
        doc.add_page_break()
        doc.add_paragraph("Two.")

    assert set(pages_by_text(populate).values()) == {None}


def test_paragraph_pages_follow_saved_markers() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_heading("Intro", level=1)
        doc.add_paragraph("Page one.")
        starts_page_two = doc.add_paragraph()
        rendered_break_before_text(starts_page_two.add_run("Page two start."))
        doc.add_paragraph("Still two.")
        spans = doc.add_paragraph()
        spans.add_run("Begins on two")
        rendered_break_before_text(spans.add_run(" and ends on three."))
        doc.add_paragraph("On three.")

    pages = pages_by_text(populate)

    assert pages["Intro"] == 1
    assert pages["Page one."] == 1
    assert pages["Page two start."] == 2
    assert pages["Still two."] == 2
    assert pages["Begins on two and ends on three."] == 2, "a block's page is where it starts"
    assert pages["On three."] == 3


def test_marker_in_an_empty_paragraph_still_advances_the_page() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_paragraph("Page one.")
        rendered_break_before_text(doc.add_paragraph().add_run(""))
        doc.add_paragraph("Page two.")

    assert pages_by_text(populate)["Page two."] == 2


def test_table_rows_get_the_page_they_start_on() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.add_paragraph("Before table.")
        table = doc.add_table(rows=3, cols=1)
        table.cell(0, 0).text = "Row one"
        cell = table.cell(1, 0)
        rendered_break_before_text(cell.paragraphs[0].add_run("Row two"))
        table.cell(2, 0).text = "Row three"
        doc.add_paragraph("After table.")

    pages = pages_by_text(populate)

    assert (pages["Row one"], pages["Row two"], pages["Row three"]) == (1, 2, 2)
    assert pages["After table."] == 2


def test_headers_and_footers_have_no_page_number() -> None:
    def populate(doc: DocxDocument) -> None:
        doc.sections[0].header.paragraphs[0].text = "Header text"
        doc.add_paragraph("Page one.")
        rendered_break_before_text(doc.add_paragraph().add_run("Page two."))

    blocks = extract_document("word-saved.docx", build_docx(populate)).blocks
    header = next(block for block in blocks if block.kind == BlockKind.HEADER)

    assert header.page is None
    assert next(block for block in blocks if block.text == "Page two.").page == 2


def test_txt_has_no_page_numbers() -> None:
    blocks = extract_document("notes.txt", b"One.\n\nTwo.").blocks

    assert [block.page for block in blocks] == [None, None]


WORD_SAVED_SAMPLE = (
    Path(__file__).resolve().parents[4] / "samples" / "hard_field_trial_report_word_saved.docx"
)
# Start pages reported by Microsoft Word itself (Range.Information) for this file, 2026-11-10.
WORD_REPORTED_PAGES = {
    "reaches targets at up to": 2,
    "Mean time between failures": 20,
    "Peak transmit power": 27,
    "Under heavy rain": 28,
    "35 km, which": 29,
    "300 targets": 42,
    "Harbor Station Delta": 35,
    "Noa Levinson": 48,
}


def test_pages_match_what_word_reports_for_a_real_word_saved_file() -> None:
    blocks = extract_document(WORD_SAVED_SAMPLE.name, WORD_SAVED_SAMPLE.read_bytes()).blocks

    computed = {
        needle: next(block.page for block in blocks if needle in block.text)
        for needle in WORD_REPORTED_PAGES
    }

    assert computed == WORD_REPORTED_PAGES
    assert max(block.page or 0 for block in blocks) == 49, "Word reports 49 pages"


# Full locations Microsoft Word reports for the same file (page, nearest heading, position among
# non-empty body paragraphs since that heading, or table index + row), collected 2026-11-10.
WORD_REPORTED_LOCATIONS = {
    "reaches targets at up to": (2, "2 Maintenance procedure 2", 5, None, None),
    "Mean time between failures": (20, "20 Maintenance procedure 20", 5, None, None),
    "Peak transmit power": (27, "23 Maintenance procedure 23", None, 1, 61),
    "35 km, which": (29, "24 Maintenance procedure 24", 6, None, None),
    "Harbor Station Delta": (35, "31 Maintenance procedure 31", 5, None, None),
    "300 targets": (42, "38 Maintenance procedure 38", 5, None, None),
    "Noa Levinson": (48, "44 Maintenance procedure 44", None, 2, 1),
}


def test_full_locations_match_what_word_reports() -> None:
    blocks = extract_document(WORD_SAVED_SAMPLE.name, WORD_SAVED_SAMPLE.read_bytes()).blocks

    computed = {}
    for needle in WORD_REPORTED_LOCATIONS:
        block = next(b for b in blocks if needle in b.text)
        computed[needle] = (
            block.page,
            block.heading_path[-1],
            block.section_position,
            block.table_number,
            block.table_row,
        )

    assert computed == WORD_REPORTED_LOCATIONS
