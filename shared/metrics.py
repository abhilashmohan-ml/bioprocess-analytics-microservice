"""Prometheus metrics for the bioprocess system"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CollectorRegistry
from functools import wraps
import time
from typing import Callable, Any, Optional
import logging
from fastapi import Response

logger = logging.getLogger(__name__)

# Create a custom registry
registry = CollectorRegistry()

# Define metrics
request_count = Counter(
    'bioprocess_requests_total',
    'Total requests',
    ['service', 'method', 'endpoint', 'status'],
    registry=registry
)

request_duration = Histogram(
    'bioprocess_request_duration_seconds',
    'Request duration in seconds',
    ['service', 'method', 'endpoint'],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0),
    registry=registry
)

active_connections = Gauge(
    'bioprocess_active_connections',
    'Number of active connections',
    ['service'],
    registry=registry
)

db_query_duration = Histogram(
    'bioprocess_db_query_duration_seconds',
    'Database query duration',
    ['service', 'operation'],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0),
    registry=registry
)

db_connections = Gauge(
    'bioprocess_db_connections',
    'Database connections',
    ['service', 'database', 'state'],
    registry=registry
)

cache_operations = Counter(
    'bioprocess_cache_operations_total',
    'Cache operations',
    ['service', 'operation', 'result'],
    registry=registry
)

business_metrics = Counter(
    'bioprocess_business_events_total',
    'Business events',
    ['service', 'event_type'],
    registry=registry
)

error_count = Counter(
    'bioprocess_errors_total',
    'Total errors',
    ['service', 'error_type', 'endpoint'],
    registry=registry
)

def track_requests(service_name: str):
    """Decorator to track request metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            error_type = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                error_type = type(e).__name__
                error_count.labels(
                    service=service_name,
                    error_type=error_type,
                    endpoint=getattr(func, '__name__', 'unknown')
                ).inc()
                raise
            finally:
                duration = time.time() - start_time
                request_count.labels(
                    service=service_name,
                    method=func.__name__,
                    endpoint=getattr(func, '__name__', 'unknown'),
                    status=status
                ).inc()
                
                request_duration.labels(
                    service=service_name,
                    method=func.__name__,
                    endpoint=getattr(func, '__name__', 'unknown')
                ).observe(duration)
        
        return wrapper
    return decorator

def track_db_queries(service_name: str):
    """Decorator to track database query metrics"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = func.__name__
            
            try:
                result = await func(*args, **kwargs)
                db_query_duration.labels(
                    service=service_name,
                    operation=operation
                ).observe(time.time() - start_time)
                return result
            except Exception as e:
                logger.error(f"Database query failed in {operation}: {e}")
                raise
        
        return wrapper
    return decorator

def increment_business_metric(service_name: str, event_type: str):
    """Increment business metric counter"""
    business_metrics.labels(
        service=service_name,
        event_type=event_type
    ).inc()

def track_cache_operation(service_name: str, operation: str, result: str):
    """Track cache operations"""
    cache_operations.labels(
        service=service_name,
        operation=operation,
        result=result
    ).inc()

def set_active_connections(service_name: str, count: int):
    """Set active connections gauge"""
    active_connections.labels(service=service_name).set(count)

def set_db_connections(service_name: str, database: str, state: str, count: int):
    """Set database connections gauge"""
    db_connections.labels(
        service=service_name,
        database=database,
        state=state
    ).set(count)

def generate_metrics_response() -> Response:
    """Generate Prometheus metrics response"""
    return Response(generate_latest(registry), media_type="text/plain")