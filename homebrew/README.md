# Homebrew Formula for Sigma

This directory contains the Homebrew formula for installing Sigma v3.2.0.

## Installation

### From GitHub (recommended)

```bash
# Tap the repository
brew tap yourusername/sigma

# Install Sigma
brew install --cask sigma
```

### Local Development

```bash
# Install from local formula
brew install --cask ./homebrew/sigma.rb
```

## Formula Files

- `sigma.rb` - Main Homebrew cask formula (native macOS app)
- `sigma-cli.rb` - CLI-only formula (installs as `sigma` command)

## Dependencies

The formula includes all required dependencies:

**UI & Console:**
- textual >= 0.47.0
- rich >= 13.7.0

**AI Providers:**
- openai >= 1.12.0
- anthropic >= 0.18.0
- google-genai >= 1.0.0
- groq >= 0.4.0

**Data & Finance:**
- yfinance >= 0.2.36
- pandas >= 2.2.0
- numpy >= 1.26.0
- scipy >= 1.12.0

**Visualization:**
- plotly >= 5.18.0
- kaleido >= 0.2.1
- plotext >= 5.2.8

**HTTP & API:**
- httpx >= 0.26.0
- aiohttp >= 3.9.0
- requests >= 2.31.0

**Configuration:**
- python-dotenv >= 1.0.0
- pydantic >= 2.6.0
- pydantic-settings >= 2.1.0

## Publishing to Homebrew

### Prerequisites

- GitHub account with repository access
- Homebrew installed locally
- Python 3.11+ with dependencies installed

### Step 1: Prepare the Release

```bash
# Ensure all tests pass
python -m pytest tests/

# Verify the package builds correctly
pip install build
python -m build

# Confirm version in pyproject.toml matches your release
grep version pyproject.toml
```

### Step 2: Create a GitHub Release

```bash
# Tag the release
git tag -a v3.2.0 -m "Sigma v3.2.0 - Finance Research Agent"

# Push the tag
git push origin v3.2.0
```

Then on GitHub:
1. Go to **Releases** > **Draft a new release**
2. Select the tag `v3.2.0`
3. Title: `Sigma v3.2.0`
4. Add release notes
5. Publish the release

### Step 3: Build the macOS App (for Cask)

```bash
# Build the app bundle
python scripts/create_app.py

# Create a DMG
hdiutil create -volname "Sigma" -srcfolder dist/Sigma.app -ov -format UDZO Sigma-3.2.0.dmg

# Or create a ZIP
cd dist && zip -r ../Sigma-3.2.0.zip Sigma.app && cd ..
```

### Step 4: Calculate SHA256 Hashes

```bash
# For DMG
shasum -a 256 Sigma-3.2.0.dmg

# For the source tarball (from GitHub)
curl -sL https://github.com/desenyon/sigma/archive/refs/tags/v3.2.0.tar.gz | shasum -a 256
```

### Step 5: Upload Assets to GitHub Release

1. Go to your release on GitHub
2. Click **Edit**
3. Upload `Sigma-3.2.0.dmg` or `Sigma-3.2.0.zip`
4. Save the release

### Step 6: Update Formula Files

Update the SHA256 hashes in both formula files:

**sigma.rb** (Cask):
```ruby
sha256 "YOUR_DMG_SHA256_HERE"
```

**sigma-cli.rb** (Formula):
Replace all `REPLACE_WITH_ACTUAL_SHA256` placeholders with actual hashes.

```bash
# Get SHA256 for each Python package
pip download PACKAGE_NAME --no-deps -d /tmp/pkg
shasum -a 256 /tmp/pkg/*.tar.gz
```

### Step 7: Create Your Homebrew Tap

```bash
# Create a new repo named homebrew-sigma on GitHub
# Clone it locally
git clone https://github.com/yourusername/homebrew-sigma.git
cd homebrew-sigma

# Copy formula files
cp /path/to/sigma/homebrew/sigma.rb Casks/
cp /path/to/sigma/homebrew/sigma-cli.rb Formula/

# Commit and push
git add .
git commit -m "Add Sigma v3.2.0 formulas"
git push origin main
```

### Step 8: Test the Installation

```bash
# Tap your repository
brew tap yourusername/sigma

# Test cask installation
brew install --cask sigma

# Or test formula installation
brew install sigma-cli

# Verify installation
sigma --version
```

### Step 9: Submit to Homebrew Core (Optional)

For wider distribution, submit a PR to homebrew-core:

```bash
# Fork homebrew-core on GitHub
brew tap homebrew/core
cd $(brew --repository homebrew/core)

# Create a branch
git checkout -b sigma-cli

# Add your formula
cp /path/to/sigma/homebrew/sigma-cli.rb Formula/s/

# Test locally
brew install --build-from-source ./Formula/s/sigma-cli.rb
brew test sigma-cli
brew audit --strict sigma-cli

# Commit and push
git add Formula/s/sigma-cli.rb
git commit -m "sigma-cli 3.2.0 (new formula)"
git push origin sigma-cli
```

Then open a PR on GitHub to `homebrew/homebrew-core`.

## Cask vs Formula

- **Cask** (`sigma.rb`): Installs the native macOS application to /Applications
- **Formula** (`sigma-cli.rb`): Installs the CLI tool to /usr/local/bin

Most users should use the Cask version for the best experience.

## Troubleshooting

### Installation fails with dependency errors

```bash
# Update Homebrew
brew update

# Reinstall Python
brew reinstall python@3.12

# Try again
brew install --cask sigma
```

### SHA256 mismatch

Re-download and recalculate the hash:

```bash
curl -sL URL_HERE -o /tmp/download
shasum -a 256 /tmp/download
```

### Formula audit warnings

```bash
brew audit --strict --online sigma-cli
```

Fix any issues reported before submitting to homebrew-core.
