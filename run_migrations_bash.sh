#!/usr/bin/env bash
# run_migrations_dev.sh - Development migrations with proper sequencing

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

PYTHON_CMD="python"

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

log "🚀 Starting development database migrations..."

# CRITICAL: Check if Docker containers are running first
log "🔍 Checking if Docker containers are running..."
for port in 54320 54321 54322; do
    if ! nc -z localhost $port 2>/dev/null; then
        error "Database on port $port is not accessible. Did you run 'docker-compose --profile dev up -d' first?"
    fi
done

# Wait for databases to be fully ready
log "⏳ Waiting for databases to be fully ready..."
for port in 54320 54321 54322; do
    log "Waiting for database on port $port to accept connections..."
    timeout=60
    while ! pg_isready -h localhost -p "$port" >/dev/null 2>&1; do
        sleep 2
        timeout=$((timeout - 2))
        if [ $timeout -le 0 ]; then
            error "Database on port $port failed to become ready within 60 seconds"
        fi
    done
    log "✅ Database on port $port is ready"
done

log "✅ All databases are healthy. Starting migrations..."
# ---------- AUTH ----------
(
  cd services/auth
  source .venv/bin/activate
  export AUTH_DATABASE_URL="postgresql+psycopg2://authuser:password@localhost:54320/authdb"
  alembic init tmp_alembic          # temporary folder with full skeleton
  cp tmp_alembic/script.py.mako alembic/
  rm -rf tmp_alembic
  mkdir -p alembic/versions
  alembic revision --autogenerate -m "Initial auth tables"
  sleep 5
  alembic upgrade head
  sleep 60
  deactivate
  cd ../../
)

# ---------- USER ----------
(
  cd services/user
  source .venv/bin/activate
  export USER_DATABASE_URL="postgresql+psycopg2://useruser:password@localhost:54321/userdb"
  alembic init tmp_alembic          # temporary folder with full skeleton
  cp tmp_alembic/script.py.mako alembic/
  rm -rf tmp_alembic
  mkdir -p alembic/versions
  alembic revision --autogenerate -m "Initial user tables"
  sleep 5
  alembic upgrade head
  sleep 60
  deactivate
  cd ../../
)

# ---------- BATCH ----------
(
  cd services/batch
  source .venv/bin/activate
  export BATCH_DATABASE_URL="postgresql+psycopg2://batchuser:password@localhost:54322/batchdb"
  alembic init tmp_alembic          # temporary folder with full skeleton
  cp tmp_alembic/script.py.mako alembic/
  rm -rf tmp_alembic
  mkdir -p alembic/versions
  alembic revision --autogenerate -m "Initial batch tables"
  sleep 5
  alembic upgrade head
  sleep 60
  deactivate
  cd ../../
)
log "✅ All development migrations completed!"
echo "All migrations complete!"
