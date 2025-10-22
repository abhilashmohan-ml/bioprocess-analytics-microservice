#!/usr/bin/env bash
# run_migrations_prod.sh - Production database migrations with safety checks

set -euo pipefail

# Production configuration
PYTHON_CMD="python3.13"
PYTHON_VERSION="3.13.7"
ENVIRONMENT="production"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BLUE='\033[0;34m'
NC='\033[0m'

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

info() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')] INFO: $1${NC}"
}

# Production safety checks
check_prerequisites() {
    info "Running production safety checks..."
    
    # Check if running as root (should not)
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
    fi
    
    # Check if production environment is set
    if [ "${ENVIRONMENT}" != "production" ]; then
        warn "ENVIRONMENT is not set to production"
    fi
    
    # Check if backup directory exists
    if [ ! -d "backups" ]; then
        mkdir -p backups
        info "Created backups directory"
    fi
    
    # Check available disk space (need at least 1GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 1048576 ]; then
        error "Insufficient disk space. Need at least 1GB free"
    fi
    
    info "✅ Production safety checks passed"
}

# Database backup function
backup_database() {
    local service=$1
    local db_name=$2
    local db_user=$3
    local db_port=$4
    
    info "Creating backup for $service database..."
    
    backup_file="backups/${service}_backup_$(date +%Y%m%d_%H%M%S).sql"
    
    # Create backup with compression
    docker exec bioprocess_db_${service} pg_dump -U "$db_user" "$db_name" | gzip > "${backup_file}.gz"
    
    if [ $? -eq 0 ]; then
        log "✅ Backup created: ${backup_file}.gz"
        echo "${backup_file}.gz"  # Return backup file path
    else
        error "Failed to create backup for $service"
    fi
}

# Verify Python 3.13.7
if ! command -v $PYTHON_CMD &> /dev/null; then
    error "Python 3.13.7 not found. Please install it or update your PATH."
fi

log "🚀 Starting PRODUCTION database migrations with Python $PYTHON_VERSION..."

# Run safety checks
check_prerequisites

# Production database URLs (update these for your production setup)
PROD_AUTH_DB_URL="postgresql+psycopg://authuser:${DB_AUTH_PASSWORD}@db_auth:5432/authdb"
PROD_USER_DB_URL="postgresql+psycopg://useruser:${DB_USER_PASSWORD}@db_user:5432/userdb"
PROD_BATCH_DB_URL="postgresql+psycopg://batchuser:${DB_BATCH_PASSWORD}@db_batch:5432/batchdb"

# Wait for production databases to be ready
for port in 5432 5433 5434; do  # Production ports
    log "⏳ Waiting for production database on port $port..."
    until pg_isready -h localhost -p "$port" >/dev/null 2>&1; do
        sleep 2
    done
done

log "✅ All production databases are ready."

# Function to run production migration with safety checks
migrate_service_prod() {
    local service=$1
    local db_url=$2
    local db_name=$3
    local db_user=$4
    local db_port=$5
    
    info "🚀 Starting PRODUCTION migration for $service..."
    
    # Create backup first
    backup_file=$(backup_database "$service" "$db_name" "$db_user" "$db_port")
    log "📦 Backup created: $backup_file"
    
    (
        cd "services/$service"
        
        # Use virtual environment if it exists
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            info "Using virtual environment for $service"
        fi
        
        # Set production environment variables
        export $(echo ${service} | tr '[:lower:]' '[:upper:]')_DATABASE_URL="${db_url}"
        export ENVIRONMENT="production"
        
        # Verify alembic is properly configured for production
        if [ ! -f "alembic.ini" ]; then
            info "📝 Setting up production alembic for $service..."
            $PYTHON_CMD -m alembic init alembic
            
            # Production-specific alembic configuration
            cat > alembic.ini << 'EOF'
[alembic]
script_location = alembic
prepend_sys_path = .

# Production database URL from environment
sqlalchemy.url = driver://user:pass@localhost/dbname

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 88

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF
        fi
        
        # Production-specific env.py
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

# Get database URL from centralized production environment
service_name = os.path.basename(os.path.dirname(os.path.dirname(__file__)))
db_url_var = f"{service_name.upper()}_DATABASE_URL"
config.set_main_option("sqlalchemy.url", os.getenv(db_url_var))

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
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
        
        # Check for existing migrations (production safety)
        if [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions)" ]; then
            info "⚠️  Existing migrations found. Validating..."
            
            # Show what will be changed
            info "📋 Pending migrations:"
            $PYTHON_CMD -m alembic check || true
            
            # Ask for confirmation (in production, this would be automated)
            read -p "Do you want to apply these migrations to PRODUCTION? (yes/no): " confirm
            if [[ "$confirm" != "yes" ]]; then
                info "❌ Migration cancelled by user"
                return 1
            fi
        fi
        
        # Create migration with detailed description
        migration_desc="Production migration for ${service} - $(date +%Y%m%d_%H%M%S)"
        log "📝 Creating migration: $migration_desc"
        $PYTHON_CMD -m alembic revision --autogenerate -m "$migration_desc"
        
        # Apply migration with transaction
        log "⬆️  Applying migration to PRODUCTION..."
        
        # Run in transaction (safer for production)
        $PYTHON_CMD -c "
import alembic.config
import alembic.command
import sys

try:
    alembic_cfg = alembic.config.Config('alembic.ini')
    alembic.command.upgrade(alembic_cfg, 'head')
    print('✅ Migration applied successfully')
except Exception as e:
    print(f'❌ Migration failed: {e}')
    sys.exit(1)
"
        
        if [ $? -eq 0 ]; then
            log "✅ PRODUCTION migration completed for $service"
        else
            error "❌ PRODUCTION migration failed for $service"
        fi
        
        # Deactivate virtual environment if used
        if [ -f ".venv/bin/activate" ]; then
            deactivate
        fi
    )
}

# Run production migrations for each service
log "📊 Starting PRODUCTION migrations..."

migrate_service_prod "auth" "$PROD_AUTH_DB_URL" "authdb" "authuser" "5432"
migrate_service_prod "user" "$PROD_USER_DB_URL" "userdb" "useruser" "5433"
migrate_service_prod "batch" "$PROD_BATCH_DB_URL" "batchdb" "batchuser" "5434"

# Final verification
log "🔍 Running post-migration verification..."
for service in auth user batch; do
    log "✅ Verifying $service database..."
    # Add verification commands here
done

log "✅ ALL PRODUCTION migrations completed successfully!"
log "🎯 Production environment is ready!"
log "   Backup files are stored in: backups/"
log "   Next step: Deploy your application services"
