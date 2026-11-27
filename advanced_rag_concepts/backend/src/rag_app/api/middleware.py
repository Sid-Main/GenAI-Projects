"""Per-request context: assigns a request ID and logs each completed request."""

# High-precision timer for measuring request duration
import time

# Generates random unique IDs
import uuid

import structlog
from fastapi import Request, Response

# BaseHTTPMiddleware: base class for code that wraps every request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Header carrying the ID in both directions (a client may send one, we always return one)
REQUEST_ID_HEADER = "X-Request-ID"
logger = structlog.get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    # Runs for every request; call_next passes it on to the actual endpoint
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Reuse the caller's ID if provided (useful for tracing across services), else create one
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        # Start each request with clean context so values never leak between requests
        structlog.contextvars.clear_contextvars()
        # Every log line written during this request will now include request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start = time.perf_counter()
        # Hand the request to the endpoint and wait for its response
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        # Return the ID so a client (or you, debugging) can match the response to log lines
        response.headers[REQUEST_ID_HEADER] = request_id
        # One structured "access log" line per request
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
