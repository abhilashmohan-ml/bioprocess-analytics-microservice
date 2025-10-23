#!/usr/bin/env bash
# detect-and-install.sh - Universal package manager detection for Docker

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

# ===================================================================
# 🕵️ PACKAGE MANAGER DETECTION
# ===================================================================

detect_package_manager() {
    # Check for package managers in order of preference
    if command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v apk &> /dev/null; then
        echo "apk"
    elif command -v microdnf &> /dev/null; then
        echo "microdnf"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v zypper &> /dev/null; then
        echo "zypper"
    else
        echo "unknown"
    fi
}

# ===================================================================
# 📦 PACKAGE INSTALLATION FUNCTIONS
# ===================================================================

install_apt_deps() {
    log "Detected Debian/Ubuntu (apt) - Installing Docker & PostgreSQL dependencies..."
    
    # Update package list
    apt-get update
    
    # Install dependencies
    apt-get install -y \
        curl \
        postgresql-client \
        libpq-dev \
        gcc \
        make \
        wget
    
    # Clean up
    rm -rf /var/lib/apt/lists/*
}

install_apk_deps() {
    log "Detected Alpine Linux (apk) - Installing Docker & PostgreSQL dependencies..."
    
    # Update package index
    apk update
    
    # Install dependencies
    apk add --no-cache \
        curl \
        postgresql-client \
        postgresql-dev \
        gcc \
        make \
        wget \
        musl-dev
}

install_dnf_deps() {
    log "Detected Fedora/RHEL (dnf) - Installing Docker & PostgreSQL dependencies..."
    
    # Install dependencies
    dnf install -y \
        curl \
        postgresql \
        postgresql-devel \
        gcc \
        make \
        wget
    
    # Clean up
    dnf clean all
}

install_yum_deps() {
    log "Detected CentOS (yum) - Installing Docker & PostgreSQL dependencies..."
    
    # Install dependencies
    yum install -y \
        curl \
        postgresql \
        postgresql-devel \
        gcc \
        make \
        wget
    
    # Clean up
    yum clean all
}

install_microdnf_deps() {
    log "Detected microdnf (minimal) - Installing Docker & PostgreSQL dependencies..."
    
    # Install dependencies (minimal set)
    microdnf install -y \
        curl \
        postgresql \
        postgresql-devel \
        gcc \
        make \
        wget
    
    # Clean up
    microdnf clean all
}

install_pacman_deps() {
    log "Detected Arch/Manjaro (pacman) - Installing Docker & PostgreSQL dependencies..."
    
    # Update package database
    pacman -Sy --noconfirm
    
    # Install dependencies
    pacman -S --noconfirm \
        curl \
        postgresql-libs \
        gcc \
        make \
        wget
    
    # Clean up
    pacman -Scc --noconfirm
}

install_zypper_deps() {
    log "Detected openSUSE (zypper) - Installing Docker & PostgreSQL dependencies..."
    
    # Install dependencies
    zypper install -y \
        curl \
        postgresql \
        postgresql-devel \
        gcc \
        make \
        wget
    
    # Clean up
    zypper clean -a
}

# ===================================================================
# 🎯 MAIN EXECUTION
# ===================================================================

main() {
    local pm=$(detect_package_manager)
    
    log "🔍 Detected package manager: $pm"
    
    case "$1" in
        "docker-deps")
            case $pm in
                "apt") install_apt_deps ;;
                "apk") install_apk_deps ;;
                "dnf") install_dnf_deps ;;
                "yum") install_yum_deps ;;
                "microdnf") install_microdnf_deps ;;
                "pacman") install_pacman_deps ;;
                "zypper") install_zypper_deps ;;
                *) 
                    error "Unsupported package manager: $pm"
                    echo "Please install manually: curl, postgresql-client, gcc, make"
                    exit 1
                    ;;
            esac
            ;;
        "python-deps")
            # Python dependencies (if needed at system level)
            log "Installing Python build dependencies..."
            # This would be for building Python extensions, etc.
            ;;
        *)
            error "Unknown dependency type: $1"
            echo "Usage: $0 {docker-deps|python-deps}"
            exit 1
            ;;
    esac
    
    log "✅ System dependencies installed successfully!"
    
    # Show what was installed
    echo ""
    echo "📋 Installed packages:"
    case $pm in
        "apt") dpkg -l | grep -E "(curl|postgres|gcc|make)" || true ;;
        "apk") apk info | grep -E "(curl|postgres|gcc|make)" || true ;;
        "dnf"|"yum") rpm -qa | grep -E "(curl|postgres|gcc|make)" || true ;;
        "pacman") pacman -Q | grep -E "(curl|postgres|gcc|make)" || true ;;
        "zypper") rpm -qa | grep -E "(curl|postgres|gcc|make)" || true ;;
    esac
}

# Run main function with arguments
main "$@"
