#!/bin/bash
# Build script for Sigma

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
RELEASE_VERSION="3.7.2"

echo "========================================"
echo "  Sigma v${RELEASE_VERSION} Build Script"
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

# Build: prefer uv (avoids PEP 668 "externally managed" failures on many macOS Pythons)
echo ""
if command -v uv &> /dev/null; then
    echo "Building with uv..."
    uv build
    echo ""
    echo "Creating macOS app bundle..."
    uv run python scripts/create_app.py --output dist
else
    echo "Installing build tools..."
    python3 -m pip install --upgrade pip build twine --quiet
    echo ""
    echo "Building package..."
    python3 -m build
    echo ""
    echo "Creating macOS app bundle..."
    python3 scripts/create_app.py --output dist
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
echo ""
echo "To install locally:"
echo "  pip install dist/*.whl"
echo ""
echo "To install the app:"
echo "  cp -r dist/Sigma.app /Applications/"
echo ""
echo "Tip: install uv (https://github.com/astral-sh/uv) for reliable builds on PEP 668 systems."
echo ""
