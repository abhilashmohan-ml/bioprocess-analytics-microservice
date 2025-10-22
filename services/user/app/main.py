"""User service main application with centralized configuration"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import sys

# Import shared configuration
sys.path.append('../../..')
from shared.config import settings
from shared.tracing import setup_tracing
from shared.metrics import track_requests
from .api import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.service.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with centralized configuration"""
    logger.info(f"🚀 Starting {settings.service.name} User Service")
    logger.info(f"   Environment: {settings.service.environment}")
    logger.info(f"   Debug: {settings.features.debug}")
    logger.info(f"   Tracing: {settings.features.enable_tracing}")
    logger.info(f"   Metrics: {settings.features.enable_metrics}")
    
    yield
    
    logger.info("🛑 Shutting down User Service")

# Create FastAPI app
app = FastAPI(
    title="User Service",
    version=settings.service.version,
    description="User management microservice with centralized configuration",
    debug=settings.features.debug,
    lifespan=lifespan
)

# Setup tracing if enabled
if settings.features.enable_tracing:
    tracer = setup_tracing(app, "user-service")

# Include router
app.include_router(router)

# Health check
@app.get("/healthz")
@track_requests("user-service")
async def health_check():
    return {
        "status": "healthy",
        "service": "user-service",
        "version": settings.service.version,
        "environment": settings.service.environment,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat()
    }