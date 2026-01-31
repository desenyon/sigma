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

**HTTP & API:**
- httpx >= 0.26.0
- aiohttp >= 3.9.0
- requests >= 2.31.0

**Configuration:**
- python-dotenv >= 1.0.0
- pydantic >= 2.6.0
- pydantic-settings >= 2.1.0

## Publishing to Homebrew

1. Create a GitHub release with the version tag (v3.2.0)
2. Build the app bundle: `python scripts/create_app.py`
3. Create a DMG or ZIP of the app bundle
4. Upload to GitHub releases
5. Update the formula with the new URL and SHA256

```bash
# Calculate SHA256
shasum -a 256 Sigma-3.2.0.dmg
```

## Cask vs Formula

- **Cask** (`sigma.rb`): Installs the native macOS application to /Applications
- **Formula** (`sigma-cli.rb`): Installs the CLI tool to /usr/local/bin

Most users should use the Cask version for the best experience.
