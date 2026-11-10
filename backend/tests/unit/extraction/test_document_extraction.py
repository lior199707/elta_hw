from __future__ import annotations

import pytest
from docx.document import Document as DocxDocument

from doc_checker.custom_types.document_types import DocumentFormat
from doc_checker.extraction.document_extraction import extract_document
from doc_checker.extraction.extraction_errors import (
    EmptyDocumentError,
    UnsupportedDocumentTypeError,
)
from tests.docx_factory import build_docx


def _two_paragraphs(doc: DocxDocument) -> None:
    doc.add_paragraph("One.")
    doc.add_paragraph("Two.")


def test_dispatches_by_extension_case_insensitively() -> None:
    document = extract_document("REPORT.DOCX", build_docx(_two_paragraphs))

    assert document.document_format == DocumentFormat.DOCX
    assert document.name == "REPORT.DOCX"


def test_blocks_get_sequential_ids_and_one_based_indexes() -> None:
    blocks = extract_document("a.txt", b"One.\n\nTwo.\n\nThree.").blocks

    assert [(block.block_id, block.index) for block in blocks] == [
        ("B1", 1),
        ("B2", 2),
        ("B3", 3),
    ]


@pytest.mark.parametrize("filename", ["report.pdf", "legacy.doc", "no_extension", "sheet.xlsx"])
def test_unsupported_extension_raises(filename: str) -> None:
    with pytest.raises(UnsupportedDocumentTypeError):
        extract_document(filename, b"irrelevant")


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("blank.txt", b"  \n\n \t \n"),
        ("blank.docx", build_docx(lambda doc: doc.add_paragraph("   "))),
    ],
)
def test_document_without_text_raises_empty_error(filename: str, content: bytes) -> None:
    with pytest.raises(EmptyDocumentError):
        extract_document(filename, content)
