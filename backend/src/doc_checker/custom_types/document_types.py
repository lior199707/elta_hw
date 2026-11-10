from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DocumentFormat(StrEnum):
    DOCX = ".docx"
    TXT = ".txt"


class BlockKind(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE_ROW = "table_row"
    HEADER = "header"
    FOOTER = "footer"


@dataclass(frozen=True)
class BlockDraft:
    """A unit of text as produced by a format-specific extractor, before normalization."""

    kind: BlockKind
    text: str
    heading_path: tuple[str, ...] = ()
    section_position: int | None = None
    table_number: int | None = None
    table_row: int | None = None
    page: int | None = None


@dataclass(frozen=True)
class Block:
    """A normalized, addressable unit of document text. `index` is 1-based.

    Human-findable location: `section_position` is the 1-based position of a paragraph or
    list item among the non-empty ones since the last heading; `table_number` and
    `table_row` are 1-based as Word counts them (the header row is row 1). `page` is the page
    the block starts on in the layout Word saved in the file, or None when the file has none.
    """

    block_id: str
    index: int
    kind: BlockKind
    text: str
    heading_path: tuple[str, ...]
    section_position: int | None = None
    table_number: int | None = None
    table_row: int | None = None
    page: int | None = None


@dataclass(frozen=True)
class ExtractedDocument:
    name: str
    document_format: DocumentFormat
    blocks: tuple[Block, ...]
