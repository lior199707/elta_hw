from __future__ import annotations

from collections.abc import Callable
from io import BytesIO

from docx import Document
from docx.document import Document as DocxDocument


def build_docx(populate: Callable[[DocxDocument], object]) -> bytes:
    """Create an in-memory DOCX, let `populate` add content, and return the file bytes."""
    document = Document()
    populate(document)
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()
