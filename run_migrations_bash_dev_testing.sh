#!/usr/bin/env bash
# run_migrations_dev.sh - Development database migrations with Python 3.13

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

# Python 3.13 specific configuration
PYTHON_CMD="python3.13"
PYTHON_VERSION="3.13.7"

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Verify Python 3.13
if ! command -v $PYTHON_CMD &> /dev/null; then
    error "Python 3.13.7 not found. Please install it or update your PATH."
fi

log "🚀 Starting development database migrations with Python $PYTHON_VERSION..."

# Wait for databases to be ready
for port in 54320 54321 54322; do
    log "⏳ Waiting for database on port $port..."
    until pg_isready -h localhost -p "$port" >/dev/null 2>&1; do
        sleep 1
    done
done

log "✅ All databases are ready. Starting migrations..."

# Function to run migration for a service
migrate_service() {
    local service=$1
    local db_url=$2
    local port=$3
    
    log "📊 Migrating $service database..."
    
    (
        cd "services/$service"
        
        # Use virtual environment if it exists
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            log "Using virtual environment for $service"
        fi
        
        # Set environment variables for centralized config
        export $(echo ${service} | tr '[:lower:]' '[:upper:]')_DATABASE_URL="${db_url}"
        export ENVIRONMENT="development"
        
        # Initialize alembic if not already done
        if [ ! -d "alembic" ]; then
            log "📁 Initializing alembic for $service..."
            $PYTHON_CMD -m alembic init alembic
            
            # Update alembic.ini with centralized config
            sed -i.bak "s|sqlalchemy.url =.*|sqlalchemy.url = ${db_url}|g" alembic.ini
            
            # Update env.py for centralized configuration
            cat > alembic/env.py << 'EOF'
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import sys
import pathlib

# Add parent directory to path for imports
sys.path.append(str(pathlib.Path(__file__).parent.parent.parent))
from shared.config import settings

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
sys.path.append(str(pathlib.Path(__file__).parent.parent))
from app.db import Base

target_metadata = Base.metadata

# Get database URL from centralized environment
service_name = os.path.basename(os.path.dirname(os.path.dirname(__file__)))
db_url_var = f"{service_name.upper()}_DATABASE_URL"
config.set_main_option("sqlalchemy.url", os.getenv(db_url_var, settings.auth_database_url_DATABASE_URL))

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF
        fi
        
        # Create migration
        log "📝 Creating migration..."
        $PYTHON_CMD -m alembic revision --autogenerate -m "Initial ${service} tables"
        
        # Apply migration
        log "⬆️  Applying migration..."
        $PYTHON_CMD -m alembic upgrade head
        
        log "✅ $service migration completed"
        
        # Deactivate virtual environment if used
        if [ -f ".venv/bin/activate" ]; then
            deactivate
        fi
    )
}

# Run migrations for each service
migrate_service "auth" "postgresql+psycopg://authuser:password@localhost:54320/authdb" "54320"
migrate_service "user" "postgresql+psycopg://useruser:password@localhost:54321/userdb" "54321"
migrate_service "batch" "postgresql+psycopg://batchuser:password@localhost:54322/batchdb" "54322"

log "✅ All development migrations completed!"
log "🎯 Your development environment is ready!"
log "   Start debugging with: docker-compose --profile dev up -d"
log "   Then press F5 in VS Code"
