"""Centralized configuration management for bioprocess analytics"""
import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, validator, Field
from functools import lru_cache
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Ensure we're loading from the root .env file
ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / ".env"

class DatabaseConfig(BaseSettings):
    """Database configuration with connection pooling"""
    auth_database_url: str
    user_database_url: str  
    batch_database_url: str
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    
    @validator("pool_size", "max_overflow")
    def validate_pool_settings(cls, v):
        if v < 1:
            raise ValueError("Pool settings must be positive")
        return v

class RedisConfig(BaseSettings):
    """Redis configuration for caching and event bus"""
    url: str = "redis://redis:6379/0"
    password: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    @property
    def connection_url(self) -> str:
        """Get Redis connection URL with password if set"""
        if self.password:
            return self.url.replace("://", f"://:{self.password}@")
        return self.url

class SecurityConfig(BaseSettings):
    """Security configuration shared across all services"""
    secret_key: str
    fernet_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    bcrypt_rounds: int = 12
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 20
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    @validator("fernet_key")
    def validate_fernet_key(cls, v):
        try:
            from cryptography.fernet import Fernet
            Fernet(v.encode() if isinstance(v, str) else v)
        except Exception:
            raise ValueError("Invalid Fernet key format")
        return v

class JaegerConfig(BaseSettings):
    """Jaeger distributed tracing configuration"""
    agent_host: str = "jaeger"
    agent_port: int = 6831
    sampler_type: str = "const"
    sampler_param: float = 1.0
    
    @validator("sampler_param")
    def validate_sampler_param(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Sampler parameter must be between 0 and 1")
        return v

class ServiceConfig(BaseSettings):
    """Service-specific configuration"""
    name: str = "bioprocess-service"
    version: str = "2.0.0"
    port: int = 8000
    host: str = "0.0.0.0"
    workers: int = 1
    log_level: str = "INFO"
    environment: str = "development"
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {valid_levels}")
        return v.upper()

class FeatureFlags(BaseSettings):
    """Feature toggle configuration"""
    enable_tracing: bool = True
    enable_metrics: bool = True
    enable_rate_limiting: bool = True
    enable_cors: bool = True
    enable_ssl: bool = False
    debug: bool = False
    debug_sql: bool = False
    auto_reload: bool = False
    hot_reload: bool = False

class CORSConfig(BaseSettings):
    """CORS configuration"""
    origins: str = "http://localhost:3000,http://localhost:8080"
    
    @property
    def allowed_origins(self) -> list:
        """Get list of allowed origins"""
        return [origin.strip() for origin in self.origins.split(",")]

class ServiceURLs(BaseSettings):
    """Internal service URLs for Docker networking"""
    auth_service_url: str = "http://auth:9001"
    user_service_url: str = "http://user:9002"
    batch_service_url: str = "http://batch:9003"
    gateway_url: str = "http://gateway:8080"

class Settings(BaseSettings):
    """Global application settings loaded from centralized .env file"""
    
    # Service configuration
    service: ServiceConfig = ServiceConfig()
    
    # Database configuration
    database: DatabaseConfig
    
    # Redis configuration
    redis: RedisConfig = RedisConfig()
    
    # Security configuration
    security: SecurityConfig
    
    # Jaeger configuration
    jaeger: JaegerConfig = JaegerConfig()
    
    # Feature flags
    features: FeatureFlags = FeatureFlags()
    
    # CORS configuration
    cors: CORSConfig = CORSConfig()
    
    # Service URLs
    urls: ServiceURLs = ServiceURLs()
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow extra fields for future expansion
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance from centralized .env file"""
    try:
        # Ensure .env file exists
        if not ENV_FILE.exists():
            raise FileNotFoundError(f"Environment file not found: {ENV_FILE}")
        
        settings = Settings()
        logger.info(f"✅ Settings loaded successfully from {ENV_FILE}")
        logger.info(f"   Service: {settings.service.name}")
        logger.info(f"   Environment: {settings.service.environment}")
        logger.info(f"   Tracing: {settings.features.enable_tracing}")
        logger.info(f"   Metrics: {settings.features.enable_metrics}")
        
        return settings
        
    except Exception as e:
        logger.error(f"❌ Failed to load settings from {ENV_FILE}: {e}")
        raise

# Global settings instance
settings = get_settings()

# Convenience exports for backward compatibility
SECRET_KEY = settings.security.secret_key
FERNET_KEY = settings.security.fernet_key
JWT_ALGORITHM = settings.security.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.access_token_expire_minutes
REDIS_URL = settings.redis.url
JAEGER_AGENT_HOST = settings.jaeger.agent_host
JAEGER_AGENT_PORT = settings.jaeger.agent_port