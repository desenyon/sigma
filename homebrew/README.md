# Sigma Homebrew Distribution Guide

## Overview

Sigma is distributed as a **closed-source** binary via Homebrew. The source code is not public, but anyone can install and use Sigma.

## Distribution Methods

### Option 1: Private Homebrew Tap (Recommended)

Create your own Homebrew tap repository (can be private) and host pre-built binaries.

#### Steps:

1. **Build the package:**
   ```bash
   cd /Users/naitikgupta/Projects/sigma
   python -m build
   ```

2. **Create a GitHub repo for your tap:**
   - Create repo: `homebrew-sigma` (can be private)
   - Structure:
     ```
     homebrew-sigma/
     ├── Formula/
     │   └── sigma.rb
     └── README.md
     ```

3. **Host your binary:**
   - Use GitHub Releases, AWS S3, or any file hosting
   - Upload the wheel file from `dist/`

4. **Users install with:**
   ```bash
   brew tap yourusername/sigma
   brew install sigma
   ```

### Option 2: PyPI Distribution (Simpler)

Distribute via PyPI (Python Package Index). The package is installable via pip, and you can create a Homebrew formula that wraps pip.

#### Steps:

1. **Upload to PyPI:**
   ```bash
   python -m build
   twine upload dist/*
   ```

2. **Users install with:**
   ```bash
   pip install sigma-terminal
   # or via pipx for isolation
   pipx install sigma-terminal
   ```

## Current Formula

The formula in `sigma.rb` is ready to use. Update the URL and SHA256 when you release.

## Protecting Your Code

Since you want closed-source distribution:

1. **Don't publish to public GitHub**
2. **Use obfuscation** (optional): Tools like PyArmor can obfuscate Python
3. **Binary distribution**: Consider PyInstaller to create a single executable
4. **License enforcement**: The proprietary license in pyproject.toml covers legal protection

## Quick Commands

```bash
# Build distribution
python -m build

# Test locally
pip install dist/sigma_terminal-2.0.0-py3-none-any.whl

# Upload to PyPI (when ready)
twine upload dist/*

# Create single executable (optional)
pip install pyinstaller
pyinstaller --onefile --name sigma sigma/app.py
```

## Homebrew Tap Setup

1. Create GitHub repo: `yourusername/homebrew-sigma`
2. Copy `Formula/sigma.rb` to that repo
3. Update the URL and sha256 in the formula
4. Users can then: `brew tap yourusername/sigma && brew install sigma`
