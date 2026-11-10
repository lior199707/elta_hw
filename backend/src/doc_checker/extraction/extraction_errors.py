from __future__ import annotations


class ExtractionError(Exception):
    """Base for all document extraction failures."""


class UnsupportedDocumentTypeError(ExtractionError):
    """The file extension is not one of the supported document formats."""


class DocumentParseError(ExtractionError):
    """The file could not be parsed (corrupt, encrypted, wrong encoding)."""


class EmptyDocumentError(ExtractionError):
    """The file parsed but contains no text to check."""
