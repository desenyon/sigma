#!/bin/bash
# Build script for Sigma

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "========================================"
echo "  Sigma v3.4.0 Build Script"
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
