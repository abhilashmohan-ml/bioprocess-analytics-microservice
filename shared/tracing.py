"""Distributed tracing configuration - Fixed for correct Jaeger packages"""
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter  # ✅ Correct import
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from fastapi import FastAPI
import os
import logging

logger = logging.getLogger(__name__)

def setup_tracing(app: FastAPI, service_name: str) -> trace.Tracer:
    """
    Setup distributed tracing for a service using correct Jaeger packages
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service
        
    Returns:
        Tracer instance
    """
    try:
        # Configure tracer provider
        trace.set_tracer_provider(
            TracerProvider(
                resource=Resource.create({
                    SERVICE_NAME: service_name,
                    "deployment.environment": os.getenv("ENVIRONMENT", "development"),
                    "service.version": "2.0.0"
                })
            )
        )
        
        # Configure Jaeger exporter using Thrift (UDP)
        jaeger_exporter = JaegerExporter(
            agent_host_name=os.getenv("JAEGER_AGENT_HOST", "jaeger"),
            agent_port=int(os.getenv("JAEGER_AGENT_PORT", "6831")),
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        # Get tracer
        tracer = trace.get_tracer(service_name)
        
        # Instrument FastAPI
        FastAPIInstrumentor.instrument_app(app)
        
        # Instrument other libraries
        SQLAlchemyInstrumentor().instrument()
        RedisInstrumentor().instrument()
        
        logger.info(f"✅ Tracing configured for {service_name}")
        return tracer
        
    except Exception as e:
        logger.error(f"Failed to setup tracing: {e}")
        # Return a dummy tracer if Jaeger is not available
        return trace.get_tracer(service_name)