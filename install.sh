#!/bin/bash
# ──────────────────────────────────────────────────────────────────────
# Space Black Installer
# Usage: curl -fsSL https://spaceblack.info/install.sh | bash
#    or: curl -fsSL https://raw.githubusercontent.com/udaysagarm/SpaceBlack/main/install.sh | bash
# ──────────────────────────────────────────────────────────────────────

set -e

# ── Config ────────────────────────────────────────────────────────────
REPO="https://github.com/udaysagarm/SpaceBlack.git"
INSTALL_DIR="$HOME/SpaceBlack"
RELEASES_URL="https://github.com/udaysagarm/SpaceBlack/releases/latest/download"

# ── Colors ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

print_banner() {
    echo ""
    echo -e "${CYAN}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════╗"
    echo "  ║            Space Black Installer                 ║"
    echo "  ║         Infrastructure for AI Agents             ║"
    echo "  ╚══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

info()    { echo -e "${CYAN}▸${NC} $1"; }
success() { echo -e "${GREEN}✔${NC} $1"; }
error()   { echo -e "${RED}✖${NC} $1"; exit 1; }

# ── Detect OS ─────────────────────────────────────────────────────────
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_ID="$ID"
        OS_FAMILY="$ID_LIKE"
    elif [ "$(uname)" = "Darwin" ]; then
        OS_ID="macos"
        OS_FAMILY="macos"
    else
        OS_ID="unknown"
        OS_FAMILY="unknown"
    fi
}

# ── Check Dependencies ───────────────────────────────────────────────
check_deps() {
    if ! command -v python3 &> /dev/null; then
        error "python3 is required but not installed. Please install Python 3.10+."
    fi

    if ! command -v git &> /dev/null; then
        error "git is required but not installed. Please install git."
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    info "Python version: $PYTHON_VERSION"
}

# ── Install via Package (.deb / .rpm) ────────────────────────────────
install_deb() {
    info "Downloading .deb package..."
    DEB_FILE="/tmp/spaceblack_latest_all.deb"
    if curl -fsSL -o "$DEB_FILE" "$RELEASES_URL/spaceblack_1.0.0_all.deb" 2>/dev/null; then
        info "Installing .deb package (requires sudo)..."
        sudo dpkg -i "$DEB_FILE"
        sudo apt-get install -f -y 2>/dev/null || true
        rm -f "$DEB_FILE"
        
        # Safety net: ensure CLI launcher is linked
        sudo mkdir -p /usr/local/bin
        sudo ln -sf /opt/spaceblack/packaging/ghost /usr/local/bin/ghost
        
        success "Installed via .deb package!"
        return 0
    fi
    return 1 
}

install_rpm() {
    info "Downloading .rpm package..."
    RPM_FILE="/tmp/spaceblack_latest.noarch.rpm"
    if curl -fsSL -o "$RPM_FILE" "$RELEASES_URL/spaceblack-1.0.0-1.noarch.rpm" 2>/dev/null; then
        info "Installing .rpm package (requires sudo)..."
        sudo rpm -i "$RPM_FILE" 2>/dev/null || sudo dnf install -y "$RPM_FILE" 2>/dev/null || true
        rm -f "$RPM_FILE"
        
        # Safety net: ensure CLI launcher is linked
        sudo mkdir -p /usr/local/bin
        sudo ln -sf /opt/spaceblack/packaging/ghost /usr/local/bin/ghost
        
        success "Installed via .rpm package!"
        return 0
    fi
    return 1
}

# ── Install from Source (Fallback / Universal) ───────────────────────
install_from_source() {
    info "Installing from source..."

    if [ -d "$INSTALL_DIR" ]; then
        info "Existing installation found at $INSTALL_DIR"
        info "Updating..."
        cd "$INSTALL_DIR"
        git pull --ff-only 2>/dev/null || true
    else
        info "Cloning repository..."
        git clone "$REPO" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi

    # Make ghost executable
    chmod +x ghost 2>/dev/null || true
    chmod +x scripts/*.sh 2>/dev/null || true

    success "Source installed to $INSTALL_DIR"

    # Create global symlink so `ghost start` works from anywhere
    GHOST_LINK="/usr/local/bin/ghost"
    if [ ! -f "$GHOST_LINK" ]; then
        info "Creating global 'ghost' command..."
        if [ -w "/usr/local/bin" ]; then
            ln -sf "$INSTALL_DIR/ghost" "$GHOST_LINK"
        else
            sudo ln -sf "$INSTALL_DIR/ghost" "$GHOST_LINK"
        fi
        success "You can now run 'ghost start' from anywhere!"
    fi
}

# ── Auto-Launch Ghost ────────────────────────────────────────────────
launch_ghost() {
    echo ""
    echo -e "${GREEN}${BOLD}  ✅ Space Black is ready!${NC}"
    echo ""
    echo -e "  ${CYAN}Docs:${NC}   https://spaceblack.info/docs"
    echo -e "  ${CYAN}GitHub:${NC} https://github.com/udaysagarm/SpaceBlack"
    echo ""
    echo -e "  ${BOLD}Launching Ghost...${NC}"
    echo ""

    # Reattach stdin to the terminal so interactive prompts work
    # (required when running via `curl | bash` where stdin is the pipe)
    if [ "$1" = "package" ]; then
        exec /usr/local/bin/ghost start < /dev/tty
    else
        cd "$INSTALL_DIR"
        exec ./ghost start < /dev/tty
    fi
}

# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════
print_banner
detect_os
check_deps

INSTALLED=false

# Try package install on Linux
case "$OS_ID" in
    ubuntu|debian|pop|linuxmint|elementary)
        info "Detected Debian-based system ($OS_ID)"
        if install_deb; then
            INSTALLED=true
        else
            info "Package download not available. Falling back to source install..."
        fi
        ;;
    fedora|rhel|centos|rocky|alma)
        info "Detected RPM-based system ($OS_ID)"
        if install_rpm; then
            INSTALLED=true
        else
            info "Package download not available. Falling back to source install..."
        fi
        ;;
    *)
        # Check OS_FAMILY as fallback
        case "$OS_FAMILY" in
            *debian*|*ubuntu*)
                info "Detected Debian-based system"
                if install_deb; then INSTALLED=true; fi
                ;;
            *rhel*|*fedora*)
                info "Detected RPM-based system"
                if install_rpm; then INSTALLED=true; fi
                ;;
        esac
        ;;
esac

# Install from source if no package was installed
if [ "$INSTALLED" = false ]; then
    install_from_source
fi

# Auto-launch Ghost
if [ "$INSTALLED" = true ]; then
    launch_ghost "package"
else
    launch_ghost "source"
fi
