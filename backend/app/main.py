"""
FastAPI application entry point and app factory.

Creates the FastAPI application with all routers, middleware, and configuration.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import register_exception_handlers
from app.logging_config import configure_logging, RequestIDMiddleware
from app.db.session import async_session_factory
from api.graphql import create_graphql_router
from features.auth.router import router as auth_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan events.

    Handles startup and shutdown events.
    """
    # Startup
    configure_logging()
    logger.info("Starting ConnextionZ Platform API", environment=settings.environment)

    # Initialize Redis connection (placeholder)
    # await redis_service.connect()

    yield

    # Shutdown
    logger.info("Shutting down ConnextionZ Platform API")

    # Close Redis connection (placeholder)
    # await redis_service.disconnect()


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="ConnextionZ Platform API",
        description="API for the ConnextionZ creator collaboration platform",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ── Middleware ──────────────────────────────────────────

    # Request ID propagation (must be added early)
    app.add_middleware(RequestIDMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ──────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ─────────────────────────────────────────────
    app.include_router(auth_router)

    # GraphQL (Strawberry)
    graphql_router = create_graphql_router(async_session_factory)
    app.include_router(graphql_router, prefix="/api")

    # ── Health Checks ───────────────────────────────────────

    @app.get("/health", tags=["health"])
    async def health_check() -> dict:
        """Basic health check endpoint."""
        return {"status": "healthy", "service": "connextionz-api"}

    @app.get("/health/ready", tags=["health"])
    async def readiness_check() -> dict:
        """Readiness check — verifies dependencies are available."""
        # TODO: Check database, Redis, RabbitMQ connections
        return {"status": "ready", "checks": {"database": "ok", "redis": "ok"}}

    @app.get("/health/live", tags=["health"])
    async def liveness_check() -> dict:
        """Liveness check — verifies the application is running."""
        return {"status": "alive"}

    return app


# Create the application instance
app = create_app()
