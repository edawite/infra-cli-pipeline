"""
Structured logging utilities.

This module configures Python's standard ``logging`` module to emit
structured JSON records to both stdout and a rotating file. Logs are
structured so that log aggregation tools (e.g. Stackdriver, ELK) can
parse and filter them easily.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
from datetime import datetime, timezone
from typing import Optional


class JsonFormatter(logging.Formatter):
    """A logging formatter that outputs JSON objects.

    Fields from the log record are injected into a dictionary and
    serialised as JSON. Additional metadata can be added via the
    ``extra`` parameter when logging (e.g. ``logger.info(..., extra={"file_id": ...})``).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Inject additional attributes if present.
        for key, value in record.__dict__.items():
            if key not in (
                "args",
                "msg",
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
            ):
                log_record[key] = value
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False)


def configure_logging(
    level: str = "INFO",
    json_output: bool = True,
    file_path: Optional[str] = None,
) -> logging.Logger:
    """Configure root logging handlers.

    Parameters
    ----------
    level:
        Log level as a string (e.g. ``"INFO"`` or ``"DEBUG"``).
    json_output:
        If true, emit JSON‑formatted logs; otherwise use a plain text formatter.
    file_path:
        Optional path to a log file. When provided, a rotating file
        handler will be added in addition to the console handler.

    Returns
    -------
    logging.Logger
        The root logger configured with the specified handlers.
    """

    root = logging.getLogger()
    # Remove any existing handlers to avoid duplicate logs.
    for h in list(root.handlers):
        root.removeHandler(h)
    root.setLevel(level.upper())

    if json_output:
        formatter: logging.Formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    # Console handler to stdout
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # Rotating file handler if requested
    if file_path:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    return root
