"""Health endpoints: liveness (process is up) and readiness (dependencies are reachable)."""

from typing import Literal

import structlog

# APIRouter: a group of related endpoints; status: named HTTP status codes
from fastapi import APIRouter, Response, status

# BaseModel: defines the shape of the JSON response
from pydantic import BaseModel

# text(): wraps a raw SQL string so SQLAlchemy can execute it
from sqlalchemy import text

# Base class for all database errors raised by SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from rag_app.api.deps import DbSession

# Every route below gets the /health prefix and is grouped under "health" in /docs
router = APIRouter(prefix="/health", tags=["health"])
logger = structlog.get_logger(__name__)


# Response shape for /live: always {"status": "ok"}
class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"


# Response shape for /ready
class ReadinessResponse(BaseModel):
    status: Literal["ok", "unavailable"]
    database: Literal["ok", "unavailable"]
    # None until the Alembic migration (Step 8) enables the extension
    pgvector_version: str | None = None


# Liveness: answers if the process is running at all; checks no dependencies
@router.get("/live")
async def live() -> LivenessResponse:
    return LivenessResponse()


# Readiness: can we actually serve traffic? Checks the database connection
@router.get("/ready")
async def ready(session: DbSession, response: Response) -> ReadinessResponse:
    try:
        # One real query: proves the connection works and reports the pgvector version
        result = await session.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        )
        # A single value, or None if the extension isn't enabled yet
        pgvector_version: str | None = result.scalar_one_or_none()
    except (SQLAlchemyError, OSError):
        # Log the full error (with traceback) for debugging, but don't crash
        logger.warning("readiness_check_failed", exc_info=True)
        # 503 tells load balancers and monitors "don't send traffic here right now"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadinessResponse(status="unavailable", database="unavailable")
    return ReadinessResponse(status="ok", database="ok", pgvector_version=pgvector_version)
