#!/usr/bin/env python3
"""User-service entry-point – flat config, bullet-proof imports."""
import logging
import sys, os, redis
from contextlib import asynccontextmanager

# container paths
sys.path.extend(("/app", "/app/shared"))

# shared flat config
from shared.config import settings
from shared.metrics import track_requests
from shared.tracing import setup_tracing
from fastapi import FastAPI
# local router
from .api import router
# Configure logging with startup details
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced startup with detailed logging"""
    logger.info("🚀 Starting User Service with enhanced monitoring")
    logger.info(f"   Python path: {sys.path}")
    logger.info(f"   Work directory: {os.getcwd()}")
    logger.info(f"   Environment: {settings.ENVIRONMENT}")          # ← uses global
    logger.info(f"   Database: {settings.USER_DATABASE_URL}")
    logger.info(f"   Redis: {settings.REDIS_URL}")
    logger.info(f"   Tracing: {settings.ENABLE_TRACING}")
    logger.info(f"   Metrics: {settings.ENABLE_METRICS}")

    # Test imports during startup
    try:
        # ✅  do **not** re-import settings here
        from shared.security import security_manager   
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        redis_client.ping()
        logger.info("✅ Redis connection successful")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise

    # Startup
    yield

    # Shutdown
    logger.info("🛑 Shutting down User Service")

# Create FastAPI app
app = FastAPI(
    title="User Service",
    version=settings.SERVICE_VERSION,
    description="User management microservice with enhanced monitoring",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Setup tracing if enabled
if settings.ENABLE_TRACING:
    tracer = setup_tracing(app, "user-service")

# Include API router
app.include_router(router)

# Enhanced health check with startup verification
@app.get("/healthz")
@track_requests("user-service")
async def health_check():
    """Enhanced health check with startup verification"""
    try:
        # Verify shared module import
        from shared.config import settings
        from shared.config import redis_client
        
        # Test database connection
        from .db import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        
        # Test Redis connection
        redis_client.ping()
        
        return {
            "status": "healthy",
            "service": "user-service",
            "version": settings.SERVICE_VERSION,
            "environment": settings.SERVICE_ENVIRONMENT,
            "python_path": sys.path,
            "work_directory": os.getcwd(),
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": "connected",
                "redis": "connected",
                "shared_modules": "imported",
                "tracing": settings.ENABLE_TRACING,
                "metrics": settings.ENABLE_METRICS
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "user-service",
            "error": str(e),
            "python_path": sys.path,
            "timestamp": datetime.utcnow().isoformat()
        }