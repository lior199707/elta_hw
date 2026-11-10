from __future__ import annotations

import logging
from pathlib import PurePath
from typing import Protocol

from doc_checker.constants import BLOCK_ID_PREFIX
from doc_checker.custom_types.document_types import (
    Block,
    BlockDraft,
    DocumentFormat,
    ExtractedDocument,
)
from doc_checker.extraction.docx_extractor import DocxExtractor
from doc_checker.extraction.extraction_errors import (
    EmptyDocumentError,
    UnsupportedDocumentTypeError,
)
from doc_checker.extraction.text_normalization import normalize_whitespace
from doc_checker.extraction.txt_extractor import TxtExtractor

logger = logging.getLogger(__name__)


class DocumentExtractor(Protocol):
    def extract(self, content: bytes) -> list[BlockDraft]: ...


_EXTRACTORS: dict[DocumentFormat, DocumentExtractor] = {
    DocumentFormat.DOCX: DocxExtractor(),
    DocumentFormat.TXT: TxtExtractor(),
}


def extract_document(filename: str, content: bytes) -> ExtractedDocument:
    """Pick the extractor by file extension and return normalized, numbered blocks.

    Raises UnsupportedDocumentTypeError, DocumentParseError, or EmptyDocumentError.
    """
    document_format = _resolve_format(filename)
    blocks = _build_blocks(_EXTRACTORS[document_format].extract(content))
    if not blocks:
        raise EmptyDocumentError("The document contains no text to check.")

    logger.info(
        "document extracted",
        extra={"document_format": document_format, "block_count": len(blocks)},
    )
    return ExtractedDocument(name=filename, document_format=document_format, blocks=blocks)


def _resolve_format(filename: str) -> DocumentFormat:
    suffix = PurePath(filename).suffix.lower()
    try:
        return DocumentFormat(suffix)
    except ValueError:
        supported = ", ".join(DocumentFormat)
        raise UnsupportedDocumentTypeError(
            f"Unsupported file type {suffix or '(none)'!r}. Supported: {supported}."
        ) from None


def _build_blocks(drafts: list[BlockDraft]) -> tuple[Block, ...]:
    blocks: list[Block] = []
    for draft in drafts:
        text = normalize_whitespace(draft.text)
        if not text:
            continue
        index = len(blocks) + 1
        blocks.append(
            Block(
                block_id=f"{BLOCK_ID_PREFIX}{index}",
                index=index,
                kind=draft.kind,
                text=text,
                heading_path=draft.heading_path,
                section_position=draft.section_position,
                table_number=draft.table_number,
                table_row=draft.table_row,
                page=draft.page,
            )
        )
    return tuple(blocks)
