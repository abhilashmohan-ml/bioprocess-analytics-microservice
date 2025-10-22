"""Auth service main application with centralized configuration"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import sys

# Import shared configuration and tracing
sys.path.append('../../..')
from shared.config import settings
from shared.tracing import setup_tracing
from shared.metrics import track_requests
from .api import router

# Configure logging based on centralized settings
logging.basicConfig(
    level=getattr(logging, settings.service.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with centralized configuration"""
    logger.info(f"🚀 Starting {settings.service.name} Auth Service")
    logger.info(f"   Environment: {settings.service.environment}")
    logger.info(f"   Debug: {settings.features.debug}")
    logger.info(f"   Tracing: {settings.features.enable_tracing}")
    logger.info(f"   Metrics: {settings.features.enable_metrics}")
    
    # Startup
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Auth Service")

# Create FastAPI app with centralized configuration
app = FastAPI(
    title="Auth Service",
    version=settings.service.version,
    description="Authentication microservice with centralized configuration",
    docs_url="/docs" if settings.features.debug else None,
    redoc_url="/redoc" if settings.features.debug else None,
    debug=settings.features.debug,
    lifespan=lifespan
)

# Setup distributed tracing if enabled
if settings.features.enable_tracing:
    tracer = setup_tracing(app, "auth-service")
    logger.info("✅ Distributed tracing enabled")

# Include API router
app.include_router(router)

# Health check endpoint
@app.get("/healthz")
@track_requests("auth-service")
async def health_check():
    """Health check with centralized configuration"""
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": settings.service.version,
        "environment": settings.service.environment,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
        "features": {
            "tracing": settings.features.enable_tracing,
            "metrics": settings.features.enable_metrics,
            "rate_limiting": settings.features.enable_rate_limiting
        }
    }