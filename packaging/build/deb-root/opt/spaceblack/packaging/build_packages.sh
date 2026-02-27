#!/bin/bash
# ──────────────────────────────────────────────────────────────────────
# build_packages.sh — Build .deb and .rpm packages for Space Black
#
# Usage: bash packaging/build_packages.sh
# Output: packaging/dist/spaceblack_1.0.0_all.deb
#         packaging/dist/spaceblack-1.0.0-1.noarch.rpm
# ──────────────────────────────────────────────────────────────────────

set -e

VERSION="1.0.0"
PKG_NAME="spaceblack"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
DIST_DIR="$SCRIPT_DIR/dist"

echo "╔══════════════════════════════════════════════════╗"
echo "║        Space Black Package Builder               ║"
echo "║        Version: $VERSION                           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── Clean previous builds ─────────────────────────────────────────────
echo "🧹 Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$DIST_DIR"

# ── Collect source files ──────────────────────────────────────────────
echo "📦 Staging application files..."
STAGE_DIR="$BUILD_DIR/staged"
mkdir -p "$STAGE_DIR"

# Copy application files, excluding dev/runtime artifacts
rsync -a \
    --exclude='.venv' \
    --exclude='.git' \
    --exclude='.gitignore' \
    --exclude='__pycache__' \
    --exclude='.env' \
    --exclude='config.json' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    --exclude='brain/USER.md' \
    --exclude='brain/SOUL.md' \
    --exclude='brain/memory/' \
    --exclude='brain/soul.bak' \
    --exclude='brain/*.json' \
    --exclude='brain/vault/' \
    --exclude='brain/screenshots/' \
    --exclude='packaging/build/' \
    --exclude='packaging/dist/' \
    "$PROJECT_DIR/" "$STAGE_DIR/"

echo "   ✅ Staged $(find "$STAGE_DIR" -type f | wc -l | tr -d ' ') files"

# ══════════════════════════════════════════════════════════════════════
# BUILD .DEB PACKAGE
# ══════════════════════════════════════════════════════════════════════
build_deb() {
    echo ""
    echo "🔨 Building .deb package..."

    DEB_ROOT="$BUILD_DIR/deb-root"
    mkdir -p "$DEB_ROOT/opt/spaceblack"
    mkdir -p "$DEB_ROOT/DEBIAN"

    # Copy application files
    cp -a "$STAGE_DIR/"* "$DEB_ROOT/opt/spaceblack/"

    # Copy control files
    cp "$SCRIPT_DIR/deb/DEBIAN/control" "$DEB_ROOT/DEBIAN/control"
    cp "$SCRIPT_DIR/deb/DEBIAN/postinst" "$DEB_ROOT/DEBIAN/postinst"
    cp "$SCRIPT_DIR/deb/DEBIAN/prerm" "$DEB_ROOT/DEBIAN/prerm"

    # Set permissions (dpkg-deb requires specific permissions)
    chmod 755 "$DEB_ROOT/DEBIAN/postinst"
    chmod 755 "$DEB_ROOT/DEBIAN/prerm"

    # Build the .deb
    DEB_FILE="$DIST_DIR/${PKG_NAME}_${VERSION}_all.deb"
    dpkg-deb --root-owner-group --build "$DEB_ROOT" "$DEB_FILE"

    echo "   ✅ Built: $DEB_FILE"
    echo "   📏 Size: $(du -h "$DEB_FILE" | cut -f1)"
}

# ══════════════════════════════════════════════════════════════════════
# BUILD .RPM PACKAGE
# ══════════════════════════════════════════════════════════════════════
build_rpm() {
    echo ""
    echo "🔨 Building .rpm package..."

    RPM_BUILD_DIR="$BUILD_DIR/rpmbuild"
    mkdir -p "$RPM_BUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

    # Stage source files for RPM
    SOURCE_DIR="$RPM_BUILD_DIR/SOURCES/app"
    mkdir -p "$SOURCE_DIR"
    cp -a "$STAGE_DIR/"* "$SOURCE_DIR/"

    # Copy spec file
    cp "$SCRIPT_DIR/rpm/spaceblack.spec" "$RPM_BUILD_DIR/SPECS/spaceblack.spec"

    # Build the RPM
    rpmbuild \
        --define "_topdir $RPM_BUILD_DIR" \
        --define "_sourcedir $RPM_BUILD_DIR/SOURCES" \
        -bb "$RPM_BUILD_DIR/SPECS/spaceblack.spec"

    # Move RPM to dist
    RPM_FILE=$(find "$RPM_BUILD_DIR/RPMS" -name "*.rpm" -type f | head -1)
    if [ -n "$RPM_FILE" ]; then
        cp "$RPM_FILE" "$DIST_DIR/"
        RPM_BASENAME=$(basename "$RPM_FILE")
        echo "   ✅ Built: $DIST_DIR/$RPM_BASENAME"
        echo "   📏 Size: $(du -h "$DIST_DIR/$RPM_BASENAME" | cut -f1)"
    fi
}

# ══════════════════════════════════════════════════════════════════════
# RUN BUILDS
# ══════════════════════════════════════════════════════════════════════
DEB_BUILT=false
RPM_BUILT=false

# Build .deb
if command -v dpkg-deb &> /dev/null; then
    build_deb
    DEB_BUILT=true
else
    echo ""
    echo "⚠️  dpkg-deb not found — skipping .deb build"
    echo "   Install on Debian/Ubuntu: sudo apt install dpkg"
    echo "   Install on macOS:         brew install dpkg"
fi

# Build .rpm
if command -v rpmbuild &> /dev/null; then
    build_rpm
    RPM_BUILT=true
else
    echo ""
    echo "⚠️  rpmbuild not found — skipping .rpm build"
    echo "   Install on Fedora/RHEL:   sudo dnf install rpm-build"
    echo "   Install on macOS:         brew install rpm"
fi

# ── Summary ───────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════"
echo "  Build Summary"
echo "════════════════════════════════════════════════════"

if [ "$DEB_BUILT" = true ]; then
    echo "  ✅ .deb package: $DIST_DIR/${PKG_NAME}_${VERSION}_all.deb"
else
    echo "  ⏭️  .deb package: SKIPPED (dpkg-deb not installed)"
fi

if [ "$RPM_BUILT" = true ]; then
    echo "  ✅ .rpm package: $(ls "$DIST_DIR/"*.rpm 2>/dev/null)"
else
    echo "  ⏭️  .rpm package: SKIPPED (rpmbuild not installed)"
fi

echo ""
echo "  Install .deb: sudo dpkg -i $DIST_DIR/${PKG_NAME}_${VERSION}_all.deb"
echo "  Install .rpm: sudo rpm -i $DIST_DIR/${PKG_NAME}-${VERSION}-1.noarch.rpm"
echo "  Then run:     ghost start"
echo "════════════════════════════════════════════════════"
