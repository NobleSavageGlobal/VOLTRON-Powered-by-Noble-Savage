from __future__ import annotations

import logging
import sys

import structlog
from structlog.types import EventDict


def add_severity(logger: logging.Logger, method: str, event_dict: EventDict) -> EventDict:
    if method == "warning":
        event_dict["severity"] = "WARNING"
    elif method == "error" or method == "critical":
        event_dict["severity"] = "ERROR"
    else:
        event_dict["severity"] = "INFO"
    return event_dict


def setup_logging(log_level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            add_severity,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name)
