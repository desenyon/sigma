#!/bin/bash
# Build script for Sigma

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "========================================"
echo "  Sigma v3.0.0 Build Script"
echo "========================================"
echo ""

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Using Python $PYTHON_VERSION"

# Navigate to project directory
cd "$PROJECT_DIR"

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info sigma/*.egg-info

# Install/upgrade build tools
echo ""
echo "Installing build tools..."
python3 -m pip install --upgrade pip build twine --quiet

# Build the package
echo ""
echo "Building package..."
python3 -m build

# Create macOS app bundle
echo ""
echo "Creating macOS app bundle..."
python3 scripts/create_app.py --output dist

# Create DMG (if create-dmg is available)
if command -v create-dmg &> /dev/null; then
    echo ""
    echo "Creating DMG installer..."
    create-dmg \
        --volname "Sigma v3.0.0" \
        --volicon "dist/Sigma.app/Contents/Resources/AppIcon.icns" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "Sigma.app" 175 175 \
        --hide-extension "Sigma.app" \
        --app-drop-link 425 175 \
        "dist/Sigma-3.0.0.dmg" \
        "dist/Sigma.app" || echo "DMG creation failed (optional)"
fi

echo ""
echo "========================================"
echo "  Build complete!"
echo "========================================"
echo ""
echo "Outputs:"
echo "  - dist/*.whl (Python package)"
echo "  - dist/*.tar.gz (Source distribution)"
echo "  - dist/Sigma.app (macOS application)"
if [ -f "dist/Sigma-3.0.0.dmg" ]; then
    echo "  - dist/Sigma-3.0.0.dmg (Installer)"
fi
echo ""
echo "To install locally:"
echo "  pip install dist/*.whl"
echo ""
echo "To install the app:"
echo "  cp -r dist/Sigma.app /Applications/"
echo ""
