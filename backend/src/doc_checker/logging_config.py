from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

# Attributes every LogRecord carries; anything else on a record came from `extra={}`.
_RESERVED_ATTRS = frozenset(vars(logging.makeLogRecord({}))) | {"message", "asctime", "taskName"}


class JsonFormatter(logging.Formatter):
    def __init__(self, application: str) -> None:
        super().__init__()
        self._application = application

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "severity": record.levelname,
            "application": self._application,
            "module": record.module,
            "message": record.getMessage(),
        }
        payload.update({k: v for k, v in vars(record).items() if k not in _RESERVED_ATTRS})
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(application: str, level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(application))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
