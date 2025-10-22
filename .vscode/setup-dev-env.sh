#!/bin/bash
# setup-dev-env.sh - Complete development environment setup

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
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

# Check if running from VS Code terminal
if [ -n "${TERM_PROGRAM:-}" ]; then
    log "Detected VS Code terminal"
fi

# Check Python version
python_version=$(python3 --version 2>/dev/null || python --version 2>/dev/null || echo "Python not found")
log "Using: $python_version"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    error "Please run this script from the project root directory"
fi

# Function to setup virtual environment
setup_venv() {
    local service_path=$1
    local service_name=$2
    
    log "🔧 Setting up virtual environment for $service_name..."
    
    cd "$service_path"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        log "📦 Creating virtual environment..."
        python3 -m venv .venv || python -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    log "⬆️  Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    log "📥 Installing requirements..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log "✅ Requirements installed for $service_name"
    else
        warn "No requirements.txt found for $service_name"
    fi
    
    # Return to root
    cd - > /dev/null
}

# Main setup process
log "🚀 Starting complete development environment setup..."

# 1. Setup virtual environments
log "📦 Setting up virtual environments..."
setup_venv "gateway" "Gateway Service"
setup_venv "services/auth" "Auth Service"
setup_venv "services/user" "User Service"
setup_venv "services/batch" "Batch Service"

# 2. Create necessary directories
log "📁 Creating necessary directories..."
mkdir -p .vscode logs backups

# 3. Set up Docker containers
log "🐳 Starting Docker containers..."
docker-compose up -d redis jaeger

# 4. Wait for containers to be ready
log "⏳ Waiting for containers to be ready..."
sleep 10

# 5. Run database migrations
if [ -f "run_migrations_dev.sh" ]; then
    log "📊 Running database migrations..."
    chmod +x run_migrations_dev.sh
    ./run_migrations_dev.sh
else
    warn "Migration script not found, skipping..."
fi

# 6. Verify setup
log "🔍 Verifying setup..."
services=("gateway:8080" "auth:9001" "user:9002" "batch:9003")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if curl -f -s "http://localhost:$port/healthz" > /dev/null; then
        log "✅ $name service is healthy"
    else
        warn "⚠️  $name service health check failed"
    fi
done

# 7. Final instructions
log "✅ Development environment setup completed!"
echo ""
echo "🎯 Next steps:"
echo "   1. Press F5 in VS Code to start debugging"
echo "   2. Or use: Code > Run > Start Debugging"
echo "   3. Select 'All micro-services' from the debug configurations"
echo ""
echo "📋 Available debug configurations:"
echo "   - All micro-services (includes Gateway)"
echo "   - Core Services (no Gateway)"
echo "   - Individual services"
echo ""
echo "🌐 Access your services:"
echo "   - Gateway: http://localhost:8080/docs"
echo "   - Auth: http://localhost:9001/docs"
echo "   - User: http://localhost:9002/docs"
echo "   - Batch: http://localhost:9003/docs"
echo "   - Jaeger: http://localhost:16686"