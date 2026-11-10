from __future__ import annotations

import json
import logging
import sys

from doc_checker.logging_config import JsonFormatter


def test_formats_record_as_json_with_standard_and_extra_fields() -> None:
    record = logging.makeLogRecord(
        {
            "levelname": "INFO",
            "levelno": logging.INFO,
            "module": "checker",
            "msg": "check finished",
            "check_id": "c-1",
            "duration_ms": 450,
        }
    )

    payload = json.loads(JsonFormatter("doc-checker").format(record))

    assert payload["severity"] == "INFO"
    assert payload["application"] == "doc-checker"
    assert payload["module"] == "checker"
    assert payload["message"] == "check finished"
    assert payload["check_id"] == "c-1"
    assert payload["duration_ms"] == 450
    assert "timestamp" in payload


def test_includes_exception_traceback() -> None:
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = logging.makeLogRecord({"msg": "failed"})
        record.exc_info = sys.exc_info()

    payload = json.loads(JsonFormatter("doc-checker").format(record))

    assert "RuntimeError" in payload["exception"]
