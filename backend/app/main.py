"""FastAPI application entry point."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI

from app import __version__
from app.api.routes import router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Redis client (initialized on startup)
_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    """Get the Redis client instance."""
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    global _redis_client

    # Startup
    logger.info("Starting RedditSentinel API v%s", __version__)
    try:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
        _redis_client.ping()
        logger.info("Connected to Redis at %s", settings.redis_url)
    except redis.ConnectionError as e:
        logger.warning("Failed to connect to Redis: %s", e)
        _redis_client = None

    yield

    # Shutdown
    if _redis_client:
        _redis_client.close()
        logger.info("Closed Redis connection")


app = FastAPI(
    title="RedditSentinel API",
    description="Reddit bot detection and filtering system",
    version=__version__,
    lifespan=lifespan,
)

app.include_router(router, prefix="/v1")


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "RedditSentinel API", "version": __version__}
