from __future__ import annotations

import logging
import zipfile
from io import BytesIO

from docx import Document
from docx.document import Document as DocxDocument
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph
from lxml.etree import XMLSyntaxError, _Element

from doc_checker.constants import (
    DOCX_HEADING_STYLE_PREFIX,
    DOCX_LIST_STYLE_PREFIX,
    DOCX_TITLE_STYLE_NAME,
    TABLE_CELL_SEPARATOR,
)
from doc_checker.custom_types.document_types import BlockDraft, BlockKind
from doc_checker.extraction.extraction_errors import DocumentParseError
from doc_checker.extraction.text_normalization import normalize_whitespace

logger = logging.getLogger(__name__)

# KeyError: zip without Word parts; ValueError: an OOXML package that is not a Word document.
_PARSE_ERRORS = (PackageNotFoundError, zipfile.BadZipFile, KeyError, ValueError, XMLSyntaxError)
_RENDERED_PAGE_BREAK = qn("w:lastRenderedPageBreak")
_TEXT = qn("w:t")


class _PageTracker:
    """Pages from the layout Word saved in the file (`w:lastRenderedPageBreak` markers).

    Files never saved by Word have no markers; pages are then unknown (None), never guessed.
    """

    def __init__(self, document: DocxDocument) -> None:
        body = document.element.body
        self._enabled = next(body.iter(_RENDERED_PAGE_BREAK), None) is not None
        self._page = 1

    def advance(self, element: _Element) -> int | None:
        """Consume `element`'s markers; return the page its first text starts on."""
        start: int | None = None
        for node in element.iter(_RENDERED_PAGE_BREAK, _TEXT):
            if node.tag == _RENDERED_PAGE_BREAK:
                self._page += 1
            elif start is None and node.text and node.text.strip():
                start = self._page
        if not self._enabled:
            return None
        return start if start is not None else self._page


class DocxExtractor:
    def extract(self, content: bytes) -> list[BlockDraft]:
        """Return body paragraphs and table rows in document order, then headers and footers.

        Raises DocumentParseError when `content` is not a readable DOCX package.
        """
        document = _open_document(content)
        drafts: list[BlockDraft] = []
        heading_path: list[str] = []
        section_position = 0
        table_number = 0
        pages = _PageTracker(document)

        for item in document.iter_inner_content():
            if isinstance(item, Table):
                table_number += 1
                drafts.extend(_table_row_drafts(item, tuple(heading_path), table_number, pages))
                continue

            page = pages.advance(item._p)
            level = _heading_level(item)
            if level is not None and item.text.strip():
                del heading_path[level - 1 :]
                heading_path.append(normalize_whitespace(item.text))
                section_position = 0
                drafts.append(
                    BlockDraft(BlockKind.HEADING, item.text, tuple(heading_path), page=page)
                )
            elif _style_name(item) == DOCX_TITLE_STYLE_NAME:
                drafts.append(BlockDraft(BlockKind.HEADING, item.text, page=page))
            elif item.text.strip():
                section_position += 1
                drafts.append(
                    BlockDraft(
                        _paragraph_kind(item),
                        item.text,
                        tuple(heading_path),
                        section_position=section_position,
                        page=page,
                    )
                )

        drafts.extend(_header_footer_drafts(document))
        return drafts


def _open_document(content: bytes) -> DocxDocument:
    try:
        return Document(BytesIO(content))
    except _PARSE_ERRORS as exc:
        logger.warning("docx parse failed", extra={"error_type": type(exc).__name__})
        raise DocumentParseError(
            "The file is not a readable DOCX document (corrupt, encrypted, or another format)."
        ) from exc


def _style_name(paragraph: Paragraph) -> str:
    style = paragraph.style
    return style.name if style is not None and style.name is not None else ""


def _heading_level(paragraph: Paragraph) -> int | None:
    name = _style_name(paragraph)
    if not name.startswith(DOCX_HEADING_STYLE_PREFIX):
        return None
    suffix = name.removeprefix(DOCX_HEADING_STYLE_PREFIX)
    return int(suffix) if suffix.isdigit() else None


def _paragraph_kind(paragraph: Paragraph) -> BlockKind:
    properties = paragraph._p.pPr
    has_numbering = properties is not None and properties.numPr is not None
    if has_numbering or _style_name(paragraph).startswith(DOCX_LIST_STYLE_PREFIX):
        return BlockKind.LIST_ITEM
    return BlockKind.PARAGRAPH


def _table_row_drafts(
    table: Table, heading_path: tuple[str, ...], table_number: int, pages: _PageTracker
) -> list[BlockDraft]:
    drafts: list[BlockDraft] = []
    for row_number, row in enumerate(table.rows, start=1):
        page = pages.advance(row._tr)
        cell_texts: list[str] = []
        previous_cell_element = None
        for cell in row.cells:
            # A merged cell is returned once per grid column it spans, as the same element.
            if cell._tc is previous_cell_element:
                continue
            previous_cell_element = cell._tc
            text = normalize_whitespace(cell.text)
            if text:
                cell_texts.append(text)
        drafts.append(
            BlockDraft(
                BlockKind.TABLE_ROW,
                TABLE_CELL_SEPARATOR.join(cell_texts),
                heading_path,
                table_number=table_number,
                table_row=row_number,
                page=page,
            )
        )
    return drafts


def _header_footer_drafts(document: DocxDocument) -> list[BlockDraft]:
    drafts: list[BlockDraft] = []
    seen: set[tuple[BlockKind, str]] = set()
    for section in document.sections:
        for part, kind in ((section.header, BlockKind.HEADER), (section.footer, BlockKind.FOOTER)):
            if part.is_linked_to_previous:
                continue
            for paragraph in part.paragraphs:
                key = (kind, normalize_whitespace(paragraph.text))
                if key in seen:
                    continue
                seen.add(key)
                drafts.append(BlockDraft(kind, paragraph.text))
    return drafts
