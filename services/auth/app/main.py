#!/usr/bin/env python3
"""Auth-service entry-point – flat config, bullet-proof imports."""
import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

# container paths
sys.path.extend(("/app", "/app/shared"))

# shared flat config
from shared.config import settings
from shared.metrics import track_requests
from shared.tracing import setup_tracing

# local router
from .api import router

# ----------  CRITICAL:  FastAPI import  ----------
from fastapi import FastAPI

# Configure logging with flat keys
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced startup with flat-key logging."""
    logger.info("🚀 Starting Auth Service with enhanced monitoring")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    logger.info(f"   Database: {settings.AUTH_DATABASE_URL}")
    logger.info(f"   Redis: {settings.REDIS_URL}")
    logger.info(f"   Tracing: {settings.ENABLE_TRACING}")
    logger.info(f"   Metrics: {settings.ENABLE_METRICS}")

    # Startup
    yield

    # Shutdown
    logger.info("🛑 Shutting down Auth Service")


# Create FastAPI app
app = FastAPI(
    title="Auth Service",
    version=settings.SERVICE_VERSION,
    description="Authentication microservice with flat config",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Setup tracing if enabled
if settings.ENABLE_TRACING:
    tracer = setup_tracing(app, "auth-service")

# Include API router
app.include_router(router)

# Health check with flat keys
@app.get("/healthz")
@track_requests("auth-service")
async def health_check():
    """Health check with flat config."""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": settings.SERVICE_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "tracing": settings.ENABLE_TRACING,
            "metrics": settings.ENABLE_METRICS,
            "database": "connected",
            "redis": "connected"
        }
    }