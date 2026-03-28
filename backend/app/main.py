"""CrisisLens API - Gemini-powered Medical Emergency Triage.

FastAPI application with CORS, rate limiting, structured logging,
and Google Cloud service integrations.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routers import analyze, health, translate

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger: logging.Logger = logging.getLogger(__name__)

# Try to set up Google Cloud Logging in production
if settings.environment == "production":
    try:
        import google.cloud.logging

        cloud_client: google.cloud.logging.Client = google.cloud.logging.Client(
            project=settings.gcp_project_id
        )
        cloud_client.setup_logging(log_level=logging.INFO)
        logger.info("Google Cloud Logging initialized")
    except (ImportError, OSError) as e:
        logger.warning("Could not initialize Cloud Logging: %s", e)

# Rate limiter
limiter: Limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown events."""
    logger.info(
        "CrisisLens API starting (env=%s, project=%s)",
        settings.environment,
        settings.gcp_project_id,
    )
    yield
    logger.info("CrisisLens API shutting down")


app = FastAPI(
    title="CrisisLens API",
    description="Gemini-powered Medical Emergency Triage & Action System",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - strict origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)

# Routers
app.include_router(health.router, prefix="/health")
app.include_router(analyze.router, prefix="/api")
app.include_router(translate.router, prefix="/api")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return a safe error response."""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
