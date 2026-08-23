"""
Structured logging configuration for the ConnextionZ Platform.

Uses structlog for structured JSON logging with:
- Request ID propagation via ASGI middleware
- JSON format in production, console (text) in development
- Correlation IDs for request tracing

Configuration is driven by app.config.settings (LOG_LEVEL, LOG_FORMAT).
"""

from __future__ import annotations

import logging
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings


def configure_logging() -> None:
    """
    Configure structlog and standard library logging.

    Must be called once during application startup.
    Sets up processors, renderer, and log level based on app settings.
    """
    # Determine the renderer based on LOG_FORMAT setting
    if settings.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Shared processors for all loggers
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging to route through structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.log_level.upper())

    # Quiet noisy external loggers in production
    if not settings.debug:
        for noisy in ("uvicorn.access", "sqlalchemy.engine", "botocore"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that injects an X-Request-ID header into every response.

    If the incoming request already has an X-Request-ID header, it is reused.
    Otherwise, a new UUIDv4 is generated.

    The request ID is also bound to the structlog context for the duration
    of the request, enabling correlation across log lines.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
