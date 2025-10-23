#!/usr/bin/env python3
"""
Centralised configuration – flat, bullet-proof, Pydantic v2
Every key lives at the top level → no nested-model mismatch.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional, Annotated

from pydantic import Field, StringConstraints  # v2
from pydantic_settings import BaseSettings, SettingsConfigDict  # v2

# ------------------------------------------------------------------
# Repo root (where .env lives)
# ------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"


# ------------------------------------------------------------------
# Flat settings – 1-to-1 with your .env keys
# ------------------------------------------------------------------
class Settings(BaseSettings):
    """Global application settings – flat, future-proof"""

    # ---- Application -------------------------------------------------
    ENVIRONMENT: str = Field(default="development")
    SERVICE_NAME: str = Field(default="bioprocess-service")
    SERVICE_PORT: int = Field(default=8000)
    SERVICE_HOST: str = Field(default="0.0.0.0")
    SERVICE_WORKERS: int = Field(default=1)
    LOG_LEVEL: Annotated[str, StringConstraints(pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")] = Field(
        default="INFO"
    )

    # ---- Security ----------------------------------------------------
    SECRET_KEY: str = Field(min_length=32)
    FERNET_KEY: str
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    BCRYPT_ROUNDS: int = Field(default=12, ge=10, le=20)
    RATE_LIMIT_PER_MINUTE: int = Field(default=100)
    RATE_LIMIT_BURST: int = Field(default=20)

    # ---- Database ----------------------------------------------------
    AUTH_DATABASE_URL: str
    USER_DATABASE_URL: str
    BATCH_DATABASE_URL: str
    DB_POOL_SIZE: int = Field(default=20, ge=1, le=100)
    DB_MAX_OVERFLOW: int = Field(default=30, ge=0)
    DB_POOL_TIMEOUT: int = Field(default=30)
    DB_POOL_RECYCLE: int = Field(default=3600)
    DB_ECHO: bool = Field(default=False)

    # ---- Redis -------------------------------------------------------
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    REDIS_PASSWORD: Optional[str] = None
    REDIS_MAX_CONNECTIONS: int = Field(default=50)
    REDIS_SOCKET_TIMEOUT: int = Field(default=5)
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5)
    REDIS_RETRY_ON_TIMEOUT: bool = Field(default=True)
    REDIS_HEALTH_CHECK_INTERVAL: int = Field(default=30)

    # ---- Jaeger ------------------------------------------------------
    JAEGER_AGENT_HOST: str = Field(default="jaeger")
    JAEGER_AGENT_PORT: int = Field(default=6831)
    JAEGER_SAMPLER_TYPE: str = Field(default="const")
    JAEGER_SAMPLER_PARAM: float = Field(default=1.0, ge=0.0, le=1.0)

    # ---- Feature Flags ----------------------------------------------
    ENABLE_TRACING: bool = Field(default=True)
    ENABLE_METRICS: bool = Field(default=True)
    ENABLE_RATE_LIMITING: bool = Field(default=True)
    ENABLE_CORS: bool = Field(default=True)
    ENABLE_SSL: bool = Field(default=False)
    DEBUG: bool = Field(default=True)
    DEBUG_SQL: bool = Field(default=False)
    AUTO_RELOAD: bool = Field(default=False)
    HOT_RELOAD: bool = Field(default=False)
    
    # ---- Service meta -------------------------------------------------
    SERVICE_NAME: str = Field(default="bioprocess-service", alias="SERVICE_NAME")
    SERVICE_VERSION: str = Field(default="2.2.0", alias="SERVICE_VERSION")
    SERVICE_HOST: str = Field(default="0.0.0.0", alias="SERVICE_HOST")
    SERVICE_PORT: int = Field(default=8000, alias="SERVICE_PORT")
    SERVICE_WORKERS: int = Field(default=1, alias="SERVICE_WORKERS")

    # ---- CORS --------------------------------------------------------
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8080")

    @property
    def allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ---- Service URLs ------------------------------------------------
    AUTH_SERVICE_URL: str = Field(default="http://auth:9001")
    USER_SERVICE_URL: str = Field(default="http://user:9002")
    BATCH_SERVICE_URL: str = Field(default="http://batch:9003")
    GATEWAY_URL: str = Field(default="http://gateway:8080")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# ------------------------------------------------------------------
# Singleton accessor
# ------------------------------------------------------------------
@lru_cache()
def get_settings() -> Settings:
    if not ENV_FILE.exists():
        raise FileNotFoundError(
            f"Environment file not found: {ENV_FILE}.  "
            f"Copy .env.example → .env and adapt."
        )
    return Settings()


# convenience globals (kept for backward compat)
settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
FERNET_KEY = settings.FERNET_KEY
JWT_ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REDIS_URL = settings.REDIS_URL
JAEGER_AGENT_HOST = settings.JAEGER_AGENT_HOST
JAEGER_AGENT_PORT = settings.JAEGER_AGENT_PORT