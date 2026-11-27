"""FastAPI application factory."""

from collections.abc import AsyncIterator

# Turns a generator function into an async "with"-style context manager
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

# Built-in middleware that adds the CORS headers browsers require
from fastapi.middleware.cors import CORSMiddleware

# create_async_engine: connection pool; async_sessionmaker: produces sessions from it
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from rag_app.api.middleware import RequestContextMiddleware
from rag_app.api.routes import health
from rag_app.core.config import Settings, get_settings
from rag_app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


# Factory: builds and returns the app; tests can pass their own Settings
def create_app(settings: Settings | None = None) -> FastAPI:
    # Use the given settings, or load them from .env
    cfg = settings if settings is not None else get_settings()
    configure_logging(cfg.log_level, json_logs=cfg.log_json)

    # Lifespan: code before "yield" runs at startup, code after it at shutdown
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # One connection pool for the whole app; pre_ping drops dead connections before use
        engine = create_async_engine(str(cfg.database_url), pool_pre_ping=True)
        # Store the session factory where deps.get_db_session can find it
        app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        logger.info("app_started", environment=cfg.environment)
        # The app runs and serves requests while paused here
        yield
        # Shutdown: close all pooled connections cleanly
        await engine.dispose()
        logger.info("app_stopped")

    app = FastAPI(title=cfg.app_name, version="0.1.0", lifespan=lifespan)
    # Allow the React dev server (another origin) to call this API from the browser
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Request ID and access logging for every request
    app.add_middleware(RequestContextMiddleware)
    # Mount the health routes under /api/v1, giving /api/v1/health/live and /api/v1/health/ready
    app.include_router(health.router, prefix="/api/v1")
    return app
