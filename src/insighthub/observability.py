import contextvars
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

RUN_ID_CONTEXT: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default="-")

STANDARD_LOG_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def set_run_id(run_id: str) -> None:
    RUN_ID_CONTEXT.set(run_id)


class RunContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = RUN_ID_CONTEXT.get()
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", RUN_ID_CONTEXT.get()),
        }

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in STANDARD_LOG_ATTRS and not key.startswith("_")
        }
        if extra_fields:
            payload["fields"] = extra_fields

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)
