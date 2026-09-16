"""Structured logging configuration built on ``structlog``.

Produces machine-readable JSON logs in production and coloured, human-friendly
logs in development. A ``request_id`` contextvar is bound onto every log line so
records can be correlated across a single request's lifecycle.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog

# Bound onto every log record and set by the request-id middleware.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def _add_request_id(_: object, __: str, event_dict: dict) -> dict:
    """structlog processor: inject the current request id when present."""
    request_id = request_id_ctx.get()
    if request_id is not None:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(*, json_logs: bool, level: str = "INFO") -> None:
    """Configure the standard library and structlog to share one pipeline."""
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_request_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route the stdlib root logger (uvicorn, sqlalchemy, etc.) through structlog.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(level),
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
