#!/bin/bash
# Sigma Build & Distribution Script
# Usage: ./scripts/build.sh

set -e

echo "========================================"
echo "  Sigma Build Script"
echo "========================================"
echo

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get version from pyproject.toml
VERSION=$(grep 'version = ' pyproject.toml | head -1 | cut -d'"' -f2)
echo -e "${BLUE}Building Sigma v${VERSION}${NC}"
echo

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info/

# Install build dependencies
echo "Installing build dependencies..."
pip install build twine --quiet

# Build the package
echo "Building package..."
python -m build

echo
echo -e "${GREEN}Build complete!${NC}"
echo
echo "Files created:"
ls -la dist/

# Calculate SHA256
echo
echo "SHA256 checksums (for Homebrew formula):"
for f in dist/*; do
    echo "  $(shasum -a 256 "$f" | cut -d' ' -f1)  $(basename "$f")"
done

echo
echo "========================================"
echo "  Next Steps"
echo "========================================"
echo
echo "1. Test locally:"
echo "   pip install dist/sigma_terminal-${VERSION}-py3-none-any.whl"
echo
echo "2. Upload to PyPI:"
echo "   twine upload dist/*"
echo
echo "3. Update Homebrew formula with SHA256 above"
echo
