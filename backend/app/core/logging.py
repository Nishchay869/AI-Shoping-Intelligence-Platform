"""Structured, request-correlated logging configuration."""
import json
import logging
import sys


class JsonFormatter(logging.Formatter):
    """One JSON object per log line - trivial for CloudWatch (or any log shipper) to parse, filter, and
    alert on, versus grepping free-text lines. Existing %-style logger.info("...%s...", value) call sites
    don't need to change: record.getMessage() already renders them before this formatter ever sees them."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    """Configure structured (JSON) process-wide logging once during application creation."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
