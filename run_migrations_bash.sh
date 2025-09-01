#!/usr/bin/env bash
set -euo pipefail
# --- safe port killer ---
echo "Killing all services on 9001-9006 (if any)..."
for p in 9001 9002 9003 9004 9005 9006; do
  for pid in $(lsof -ti:"$p" 2>/dev/null || true); do
    kill -9 "$pid" 2>/dev/null || true
  done
done
echo "Bringing down any running Docker services..."
docker-compose --profile dev down

echo "Starting Docker DBs..."
docker-compose --profile dev up -d

# --- wait until each DB is ready ---
for port in 54320 54321 54322; do
  echo "Waiting for DB on port $port ..."
  until pg_isready -h localhost -p "$port" >/dev/null 2>&1; do
    sleep 1
  done
done

echo "All DBs are up. Running migrations..."

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

echo "All migrations complete!"
