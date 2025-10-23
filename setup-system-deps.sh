#!/usr/bin/env bash
# setup-system-deps.sh - Universal system dependency installer

set -euo pipefail

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

# ===================================================================
# 🕵️ PACKAGE MANAGER DETECTION
# ===================================================================

detect_package_manager() {
    if command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v zypper &> /dev/null; then
        echo "zypper"
    elif command -v brew &> /dev/null; then
        echo "brew"
    elif command -v apk &> /dev/null; then
        echo "apk"
    else
        echo "unknown"
    fi
}

# ===================================================================
# 📦 PACKAGE INSTALLATION FUNCTIONS
# ===================================================================

install_with_pacman() {
    local packages=("$@")
    log "Using pacman (Manjaro/Arch)..."
    
    # Update package database
    sudo pacman -Sy --noconfirm
    
    # Install packages
    sudo pacman -S --noconfirm "${packages[@]}"
}

install_with_apt() {
    local packages=("$@")
    log "Using apt (Debian/Ubuntu)..."
    
    # Update package database
    sudo apt-get update
    
    # Install packages
    sudo apt-get install -y "${packages[@]}"
}

install_with_dnf() {
    local packages=("$@")
    log "Using dnf (Fedora)..."
    
    # Install packages
    sudo dnf install -y "${packages[@]}"
}

install_with_yum() {
    local packages=("$@")
    log "Using yum (CentOS/RHEL)..."
    
    # Install packages
    sudo yum install -y "${packages[@]}"
}

install_with_zypper() {
    local packages=("$@")
    log "Using zypper (openSUSE)..."
    
    # Install packages
    sudo zypper install -y "${packages[@]}"
}

install_with_brew() {
    local packages=("$@")
    log "Using brew (macOS)..."
    
    # Update brew
    brew update
    
    # Install packages
    brew install "${packages[@]}"
}

install_with_apk() {
    local packages=("$@")
    log "Using apk (Alpine Linux)..."
    
    # Update package index
    sudo apk update
    
    # Install packages
    sudo apk add "${packages[@]}"
}

# ===================================================================
# 🐳 DOCKER-SPECIFIC DEPENDENCIES
# ===================================================================

install_docker_deps() {
    local pm=$(detect_package_manager)
    
    case $pm in
        "pacman")
            install_with_pacman docker postgresql-libs
            ;;
        "apt")
            install_with_apt docker.io postgresql-client libpq-dev
            ;;
        "dnf"|"yum")
            install_with_dnf docker postgresql postgresql-devel
            ;;
        "zypper")
            install_with_zypper docker postgresql postgresql-devel
            ;;
        "brew")
            install_with_brew docker postgresql
            ;;
        "apk")
            install_with_apk docker postgresql-client postgresql-dev
            ;;
        *)
            error "Unsupported package manager: $pm"
            ;;
    esac
}

# ===================================================================
# 🐍 PYTHON 3.13 SPECIFIC DEPENDENCIES
# ===================================================================

install_python_deps() {
    local pm=$(detect_package_manager)
    
    case $pm in
        "pacman")
            install_with_pacman python313 python313-pip base-devel
            ;;
        "apt")
            install_with_apt python3.13 python3.13-dev python3.13-venv build-essential
            ;;
        "dnf")
            install_with_dnf python3.13 python3.13-devel python3.13-pip gcc
            ;;
        "yum")
            install_with_yum python3.13 python3.13-devel python3.13-pip gcc
            ;;
        "zypper")
            install_with_zypper python3.13 python3.13-devel python3.13-pip gcc
            ;;
        "brew")
            install_with_brew python@3.13
            ;;
        "apk")
            install_with_apk python3 python3-dev py3-pip build-base
            ;;
        *)
            error "Unsupported package manager: $pm"
            ;;
    esac
}

# ===================================================================
# 🔧 SYSTEM-SPECIFIC TOOLS
# ===================================================================

install_system_tools() {
    local pm=$(detect_package_manager)
    
    case $pm in
        "pacman")
            install_with_pacman curl wget git gcc make
            ;;
        "apt")
            install_with_apt curl wget git gcc make
            ;;
        "dnf"|"yum")
            install_with_dnf curl wget git gcc make
            ;;
        "zypper")
            install_with_zypper curl wget git gcc make
            ;;
        "brew")
            install_with_brew curl wget git make
            ;;
        "apk")
            install_with_apk curl wget git gcc make musl-dev
            ;;
        *)
            error "Unsupported package manager: $pm"
            ;;
    esac
}

# ===================================================================
# 🐳 DOCKER COMPOSE INSTALLATION
# ===================================================================

install_docker_compose() {
    local pm=$(detect_package_manager)
    
    case $pm in
        "pacman")
            install_with_pacman docker-compose
            ;;
        "apt")
            # Install Docker Compose plugin
            sudo apt-get update
            sudo apt-get install -y docker-compose-plugin
            ;;
        "dnf")
            install_with_dnf docker-compose-plugin
            ;;
        "yum")
            sudo yum install -y epel-release
            sudo yum install -y docker-compose-plugin
            ;;
        "zypper")
            install_with_zypper docker-compose-plugin
            ;;
        "brew")
            install_with_brew docker-compose
            ;;
        "apk")
            install_with_apk docker-compose
            ;;
        *)
            # Fallback: Install via pip
            log "Installing Docker Compose via pip..."
            pip3 install docker-compose
            ;;
    esac
}

# ===================================================================
# 🧪 SYSTEM VERIFICATION
# ===================================================================

verify_installation() {
    local pm=$(detect_package_manager)
    
    log "🔍 Verifying installation..."
    
    # Check essential tools
    local tools=("docker" "docker-compose" "python3.13" "curl" "git")
    
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            local version=$($tool --version 2>/dev/null | head -n1)
            log "✅ $tool: $version"
        else
            warn "⚠️  $tool not found or not working properly"
        fi
    done
    
    # Check Python version specifically
    if command -v python3.13 &> /dev/null; then
        local py_version=$(python3.13 --version)
        log "✅ Python version: $py_version"
    else
        error "Python 3.13 not properly installed"
    fi
}

# ===================================================================
# 📋 MAIN EXECUTION
# ===================================================================

main() {
    log "🚀 Starting universal system dependency installation..."
    
    # Detect system
    local os_name=$(uname -s)
    local os_version=$(uname -r)
    local pm=$(detect_package_manager)
    
    info "Detected system: $os_name $os_version"
    info "Detected package manager: $pm"
    
    # Install system tools first
    log "🔧 Installing system tools..."
    install_system_tools
    
    # Install Python 3.13
    log "🐍 Installing Python 3.13..."
    install_python_deps
    
    # Install Docker and Docker Compose
    log "🐳 Installing Docker and Docker Compose..."
    install_docker_deps
    install_docker_compose
    
    # Verify everything
    log "🔍 Verifying installation..."
    verify_installation
    
    log "✅ System dependency installation completed!"
    log "🎯 Your system is now ready for bioprocess-analytics development!"
    
    # Show next steps
    echo ""
    echo "📋 Next steps:"
    echo "   1. Run: ./setup-dev-env-py313.sh (if not already done)"
    echo "   2. Run: ./run_migrations_dev.sh"
    echo "   3. Start debugging with F5 in VS Code"
    echo ""
    echo "🔧 Available commands:"
    echo "   - docker --version"
    echo "   - docker-compose --version"
    echo "   - python3.13 --version"
}
