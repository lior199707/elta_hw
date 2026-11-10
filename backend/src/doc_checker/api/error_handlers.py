from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from doc_checker.extraction.extraction_errors import (
    DocumentParseError,
    EmptyDocumentError,
    UnsupportedDocumentTypeError,
)
from doc_checker.repository.repository_errors import RecordNotFoundError
from doc_checker.services.compliance_checker import NoRulesSelectedError

logger = logging.getLogger(__name__)


class FileTooLargeError(Exception):
    """The uploaded file exceeds the configured size limit."""


_STATUS_BY_ERROR: dict[type[Exception], int] = {
    UnsupportedDocumentTypeError: status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    DocumentParseError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    EmptyDocumentError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    NoRulesSelectedError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    RecordNotFoundError: status.HTTP_404_NOT_FOUND,
    FileTooLargeError: status.HTTP_413_CONTENT_TOO_LARGE,
}


def register_error_handlers(app: FastAPI) -> None:
    """Map expected domain errors to HTTP statuses with a `{"detail": message}` body."""
    for error_type, status_code in _STATUS_BY_ERROR.items():
        app.add_exception_handler(error_type, _make_handler(status_code))


def _make_handler(status_code: int):  # noqa: ANN202 - Starlette's handler type is loosely typed
    async def handle(request: Request, exc: Exception) -> JSONResponse:
        logger.info(
            "request rejected",
            extra={
                "path": request.url.path,
                "status_code": status_code,
                "error_type": type(exc).__name__,
            },
        )
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handle
