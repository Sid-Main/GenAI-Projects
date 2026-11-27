"""Structured logging: readable console output locally, JSON in production."""

# Standard library logging, used here only to map level names to numbers
import logging

import structlog

# Type of a structlog "processor" (one step in the log pipeline)
from structlog.typing import Processor


# The * forces json_logs to be passed by name: configure_logging("INFO", json_logs=True)
def configure_logging(level: str = "INFO", *, json_logs: bool = False) -> None:
    # Each processor transforms the log event in order, like an assembly line
    processors: list[Processor] = [
        # Pull in context bound earlier (e.g. request_id from the middleware)
        structlog.contextvars.merge_contextvars,
        # Add "level": "info" / "error" to each event
        structlog.processors.add_log_level,
        # Add an ISO-8601 UTC timestamp
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if json_logs:
        # Production: exceptions as structured dicts, whole event rendered as one JSON line
        processors += [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]
    else:
        # Development: colored, aligned, human-friendly output
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        # Drop events below the chosen level (e.g. DEBUG is skipped when level is INFO)
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelNamesMapping()[level]),
        # Build each logger once, for speed
        cache_logger_on_first_use=True,
    )
