#!/usr/bin/env python3
"""Batch-service entry-point – flat config, bullet-proof imports."""
import logging
import sys, os
from contextlib import asynccontextmanager

# container paths
sys.path.extend(("/app", "/app/shared"))

# shared flat config
from shared.config import settings
from shared.metrics import track_requests
from shared.tracing import setup_tracing

# local router
from .api import router

from fastapi import FastAPI
# Configure logging based on centralized settings
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with centralized configuration"""
    logger.info(f"🚀 Starting {settings.SERVICE_NAME} Batch Service")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")
    logger.info(f"   Debug: {settings.DEBUG}")
    logger.info(f"   Tracing: {settings.ENABLE_TRACING}")
    logger.info(f"   Metrics: {settings.ENABLE_METRICS}")
    logger.info(f"   Rate Limiting: {settings.ENABLE_RATE_LIMITING}")
    
    # Startup
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Batch Service")

# Create FastAPI app with centralized configuration
app = FastAPI(
    title="Batch Service",
    version=settings.SERVICE_VERSION,
    description="Batch processing microservice with centralized configuration",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Setup distributed tracing if enabled
if settings.ENABLE_TRACING:
    tracer = setup_tracing(app, "batch-service")
    logger.info("✅ Distributed tracing enabled")

# Include the API router
app.include_router(router)

# Health check endpoint with metrics tracking
@app.get("/healthz")
@track_requests("batch-service")
async def health_check():
    """Health check with centralized configuration"""
    return {
        "status": "healthy",
        "service": "batch-service",
        "version": settings.SERVICE_VERSION,
        "environment": settings.SERVICE_ENVIRONMENT,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
        "features": {
            "tracing": settings.ENABLE_TRACING,
            "metrics": settings.ENABLE_METRICS,
            "rate_limiting": settings.ENABLE_RATE_LIMITING,
        }
    }