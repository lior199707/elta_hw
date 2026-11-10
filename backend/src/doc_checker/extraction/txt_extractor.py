from __future__ import annotations

import logging
import re

from doc_checker.constants import TXT_ENCODING
from doc_checker.custom_types.document_types import BlockDraft, BlockKind
from doc_checker.extraction.extraction_errors import DocumentParseError

logger = logging.getLogger(__name__)

_BLANK_LINE_SEPARATOR = re.compile(r"\n\s*\n")


class TxtExtractor:
    def extract(self, content: bytes) -> list[BlockDraft]:
        """Split UTF-8 text into paragraphs on blank lines.

        Raises DocumentParseError when `content` is not valid UTF-8.
        """
        try:
            text = content.decode(TXT_ENCODING)
        except UnicodeDecodeError as exc:
            logger.warning("txt decode failed", extra={"error_type": type(exc).__name__})
            raise DocumentParseError("The text file is not valid UTF-8.") from exc

        unified = text.replace("\r\n", "\n").replace("\r", "\n")
        paragraphs = [p for p in _BLANK_LINE_SEPARATOR.split(unified) if p.strip()]
        return [
            BlockDraft(kind=BlockKind.PARAGRAPH, text=paragraph, section_position=position)
            for position, paragraph in enumerate(paragraphs, start=1)
        ]
