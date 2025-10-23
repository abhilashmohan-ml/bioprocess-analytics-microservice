#!/usr/bin/env python3
"""API Gateway – flat config, bullet-proof imports."""
import json
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

# container paths
sys.path.extend(("/app", "/app/shared"))

# shared flat config
from shared.config import settings
from shared.event_bus import event_bus, EventType
from shared.metrics import (
    error_count,
    generate_metrics_response,
    track_requests,
)
from shared.security import security_manager

# FastAPI ecosystem
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import httpx
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service discovery with health tracking
SERVICE_MAP = {
    "/auth": "http://auth:9001",
    "/users": "http://user:9002",
    "/batches": "http://batch:9003",
    "/qc-batches": "http://batch:9003",
}

# Public endpoints
PUBLIC_ENDPOINTS = {
    "/auth/register",
    "/auth/login",
    "/auth/verify",
    "/health",
    "/healthz",
    "/metrics",
    "/docs",
    "/redoc",
    "/openapi.json"
}

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_counts: Dict[str, int] = {}
        self.last_failure_time: Dict[str, float] = {}
        self.circuit_states: Dict[str, str] = {}  # closed, open, half-open
        
    def is_open(self, service_name: str) -> bool:
        """Check if circuit is open for a service"""
        current_time = time.time()
        
        # Check if we should attempt recovery
        if (service_name in self.circuit_states and 
            self.circuit_states[service_name] == "open" and
            current_time - self.last_failure_time.get(service_name, 0) > self.recovery_timeout):
            self.circuit_states[service_name] = "half-open"
            logger.info(f"Circuit breaker for {service_name} is half-open")
            return False
            
        return self.circuit_states.get(service_name, "closed") == "open"
    
    def record_success(self, service_name: str):
        """Record successful request"""
        if service_name in self.circuit_states:
            if self.circuit_states[service_name] == "half-open":
                self.circuit_states[service_name] = "closed"
                self.failure_counts[service_name] = 0
                logger.info(f"Circuit breaker for {service_name} is closed")
    
    def record_failure(self, service_name: str):
        """Record failed request"""
        current_time = time.time()
        self.failure_counts[service_name] = self.failure_counts.get(service_name, 0) + 1
        self.last_failure_time[service_name] = current_time
        
        if self.failure_counts[service_name] >= self.failure_threshold:
            self.circuit_states[service_name] = "open"
            logger.warning(f"Circuit breaker for {service_name} is open")

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, redis_client: redis.Redis, requests_per_minute: int = 100):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        
    async def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed under rate limit"""
        key = f"rate_limit:{client_id}"
        window = 60  # 1 minute window
        
        try:
            pipe = self.redis.pipeline()
            now = time.time()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, now - window)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_requests = results[1]
            
            return current_requests < self.requests_per_minute
            
        except redis.RedisError as e:
            logger.error(f"Rate limiter error: {e}")
            return True  # Allow on error

# Initialize Redis connection
def get_redis_client():
    """Get Redis client with connection pooling"""
    return redis.Redis.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
        health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL
    )

# Initialize circuit breaker and rate limiter
circuit_breaker = CircuitBreaker()
redis_client = get_redis_client()
rate_limiter = RateLimiter(redis_client, settings.RATE_LIMIT_PER_MINUTE)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting API Gateway...")
    
    # Startup
    yield
    
    # Shutdown
    logger.info("Shutting down API Gateway...")
    if hasattr(event_bus, 'stop_processing'):
        event_bus.stop_processing()

# Create FastAPI app
app = FastAPI(
    title="Bioprocess Analytics API Gateway",
    version="2.0.0",
    description="Production-ready API Gateway with security and monitoring",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure based on your domain
)

async def verify_token(request: Request) -> Optional[Dict[str, Any]]:
    """Verify JWT token with auth service"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{SERVICE_MAP['/auth']}/verify",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Global security middleware"""
    
    # Generate request ID for tracing
    request_id = os.urandom(16).hex()
    request.state.request_id = request_id
    
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not await rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "retry_after": 60,
                "request_id": request_id
            },
            headers={"X-RateLimit-Remaining": "0"}
        )
    
    # Check if endpoint requires authentication
    path = request.url.path
    is_public = any(path.startswith(pub) for pub in PUBLIC_ENDPOINTS)
    
    if not is_public:
        user_data = await verify_token(request)
        if not user_data:
            error_count.labels(
                service="gateway",
                error_type="authentication_failed",
                endpoint=path
            ).inc()
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Invalid or expired token",
                    "request_id": request_id
                }
            )
        request.state.user = user_data
    
    # Add security headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response

@track_requests("gateway")
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def gateway_proxy(request: Request, full_path: str) -> Response:
    """Enhanced proxy with circuit breaker and comprehensive error handling"""
    
    segments = full_path.split("/", 1)
    prefix = "/" + segments[0]
    backend = SERVICE_MAP.get(prefix)
    
    if not backend:
        error_count.labels(
            service="gateway",
            error_type="service_not_found",
            endpoint=prefix
        ).inc()
        return JSONResponse(
            status_code=404,
            content={"error": "Service not found", "service": prefix}
        )
    
    service_name = prefix.replace("/", "")
    
    # Check circuit breaker
    if circuit_breaker.is_open(service_name):
        error_count.labels(
            service="gateway",
            error_type="circuit_breaker_open",
            endpoint=prefix
        ).inc()
        return JSONResponse(
            status_code=503,
            content={"error": f"Service {service_name} is temporarily unavailable"}
        )
    
    path_remain = "" if len(segments) == 1 else segments[1]
    upstream_url = f"{backend}/{path_remain}"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Forward headers
            headers = {k: v for k, v in request.headers.items() if k.lower() not in ["host"]}
            headers["X-Request-ID"] = request.state.request_id
            
            # Add user context if available
            if hasattr(request.state, 'user'):
                headers["X-User-Id"] = request.state.user.get('user_id', '')
                headers["X-User-Role"] = request.state.user.get('role', '')
            
            # Publish request event
            event_bus.publish_event(EventType.SYSTEM_REQUEST, {
                "service": service_name,
                "method": request.method,
                "path": path_remain,
                "user_id": getattr(request.state, 'user', {}).get('user_id'),
                "request_id": request.state.request_id
            })
            
            upstream_resp = await client.request(
                request.method,
                upstream_url,
                headers=headers,
                params=request.query_params,
                content=await request.body(),
            )
            
            # Record success
            circuit_breaker.record_success(service_name)
            
            # Publish response event
            event_bus.publish_event(EventType.SYSTEM_RESPONSE, {
                "service": service_name,
                "status_code": upstream_resp.status_code,
                "request_id": request.state.request_id
            })
            
            return Response(
                status_code=upstream_resp.status_code,
                content=upstream_resp.content,
                headers={
                    k: v for k, v in upstream_resp.headers.items() 
                    if k.lower() not in ["content-encoding", "content-length"]
                },
            )
            
    except httpx.TimeoutException:
        circuit_breaker.record_failure(service_name)
        error_count.labels(
            service="gateway",
            error_type="timeout",
            endpoint=prefix
        ).inc()
        return JSONResponse(
            status_code=504,
            content={"error": "Gateway timeout", "service": service_name}
        )
    except Exception as e:
        circuit_breaker.record_failure(service_name)
        error_count.labels(
            service="gateway",
            error_type="proxy_error",
            endpoint=prefix
        ).inc()
        logger.error(f"Proxy error: {e}")
        return JSONResponse(
            status_code=502,
            content={"error": "Bad gateway", "request_id": request.state.request_id}
        )

@app.get("/health")
async def health_check():
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "gateway",
        "version": "2.0.0",
        "checks": {}
    }
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check all services
    for service_name, service_url in SERVICE_MAP.items():
        service_key = service_name.replace("/", "")
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{service_url}/healthz")
                health_status["checks"][service_key] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
                }
        except Exception as e:
            health_status["checks"][service_key] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    # Overall status
    all_healthy = all(
        check.get("status") == "healthy" 
        for check in health_status["checks"].values() 
        if isinstance(check, dict) and "status" in check
    )
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_metrics_response()

@app.get("/healthz")
async def healthz():
    """Simple health check"""
    return {"status": "ok"}