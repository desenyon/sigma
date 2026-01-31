# Publishing Sigma to Homebrew

Complete guide to distribute Sigma via Homebrew using GitHub Releases.

---

## Prerequisites

- GitHub account
- Homebrew installed locally for testing
- Your sigma repo (can be private or public)

---

## Step 1: Build the Package

```bash
cd /Users/naitikgupta/Projects/sigma

# Clean and rebuild
rm -rf dist/ build/
source .venv/bin/activate
python -m build

# You should now have:
# dist/sigma_terminal-2.0.0-py3-none-any.whl
# dist/sigma_terminal-2.0.0.tar.gz
```

---

## Step 2: Create GitHub Release

### Via GitHub Web UI:

1. Go to your repo: `https://github.com/desenyon/sigma`
2. Click **Releases** → **Create a new release**
3. Click **Choose a tag** → Type `v2.0.0` → **Create new tag**
4. **Release title**: `Sigma v2.0.0`
5. **Description**:
   ```
   Sigma v2.0.0 - Institutional-Grade Financial Research Agent
   
   Features:
   - Multi-LLM support (OpenAI, Anthropic, Google, Groq, Ollama)
   - Real-time market data and analysis
   - Terminal charts with candlesticks
   - Comprehensive backtesting with LEAN integration
   - Setup wizard for easy configuration
   
   Install via Homebrew:
   brew tap desenyon/sigma
   brew install sigma
   ```
6. **Attach files**: Drag and drop these files:
   - `dist/sigma_terminal-2.0.0-py3-none-any.whl`
   - `dist/sigma_terminal-2.0.0.tar.gz`
7. Click **Publish release**

### Via GitHub CLI:

```bash
# Install gh if needed: brew install gh

# Create release with assets
gh release create v2.0.0 \
  dist/sigma_terminal-2.0.0-py3-none-any.whl \
  dist/sigma_terminal-2.0.0.tar.gz \
  --title "Sigma v2.0.0" \
  --notes "Institutional-Grade Financial Research Agent"
```

---

## Step 3: Get SHA256 Hashes

After creating the release, get the hashes:

```bash
# Get wheel hash (this is what Homebrew will download)
curl -sL "https://github.com/desenyon/sigma/releases/download/v2.0.0/sigma_terminal-2.0.0-py3-none-any.whl" | shasum -a 256

# Save this hash! You'll need it for the formula.
# Example output: 286e8b31e9bf962785bcfe6ccd9b1eb88c67d70971167f90d3c3d89717980181
```

---

## Step 4: Create Homebrew Tap Repository

1. Go to GitHub → **New repository**
2. **Name**: `homebrew-sigma` (MUST start with `homebrew-`)
3. **Visibility**: Public (recommended) or Private
4. **Initialize**: Add a README
5. Click **Create repository**

Then clone it:

```bash
cd ~/Projects
git clone https://github.com/desenyon/homebrew-sigma.git
cd homebrew-sigma
mkdir -p Formula
```

---

## Step 5: Create the Formula

Create `Formula/sigma.rb`:

```ruby
class Sigma < Formula
  include Language::Python::Virtualenv

  desc "Institutional-Grade Financial Research Agent"
  homepage "https://github.com/desenyon/sigma"
  url "https://github.com/desenyon/sigma/releases/download/v2.0.0/sigma_terminal-2.0.0.tar.gz"
  sha256 "PASTE_YOUR_TARBALL_SHA256_HERE"
  license :cannot_represent

  depends_on "python@3.12"

  resource "annotated-types" do
    url "https://files.pythonhosted.org/packages/ee/67/531ea369ba64dcff5ec9c3402f9f51bf748cec26dde048a2f973a4eea7f5/annotated_types-0.7.0.tar.gz"
    sha256 "aff07c09a53a08bc8cfccb9c85b05f1aa9a2a6f23728d790723543408344ce89"
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/a5/32/8f6669fc4798494966bf446c8c4a162e0b5d893dff088afddf76414f70e1/certifi-2024.12.14.tar.gz"
    sha256 "b650d30f370c2b724812bee08008be0c4163b163ddaec3f2546c1caf65f191db"
  end

  resource "charset-normalizer" do
    url "https://files.pythonhosted.org/packages/16/b0/572805e227f01586461c80e0fd25d65a2115599cc9dad142fee4b747c357/charset_normalizer-3.4.1.tar.gz"
    sha256 "44251f18cd68a75b56585dd00dae26183e102cd5e0f9f1466e6df5da2ed64ea3"
  end

  resource "httpcore" do
    url "https://files.pythonhosted.org/packages/6a/41/d7d0a89eb493922c37d343b607bc1b5da7f5be7e383571c1c2c8e88b3998/httpcore-1.0.7.tar.gz"
    sha256 "8551cb62a169ec7162ac7be8d4817d561f60e08eaa485234898414bb5a8a0b4c"
  end

  resource "httpx" do
    url "https://files.pythonhosted.org/packages/78/82/08f8c936781f67d9e6b9eeb8a0c8b4e406136ea4c3d1f89a5db71d42e0e6/httpx-0.27.2.tar.gz"
    sha256 "f7c2be1d2f3c3c3160d441802406b206c2b76f5947b11115e6df10c6c65e66c2"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/f1/70/7703c29685631f5a7590aa73f1f1d3fa9a380e654b86af429e0934a32f7d/idna-3.10.tar.gz"
    sha256 "12f65c9b470abda6dc35cf8e63cc574b1c52b11df2c86030af0ac09b01b13ea9"
  end

  resource "numpy" do
    url "https://files.pythonhosted.org/packages/65/6e/09db70a523a96d25e115e71cc56a6f9031e7b8cd166c1ac8438307c14058/numpy-1.26.4.tar.gz"
    sha256 "2a02aba9ed12e4ac4eb3ea9421c420301a0c6460d9830d74a9df87bd05890c51"
  end

  resource "pandas" do
    url "https://files.pythonhosted.org/packages/9c/d6/9f8571dc2cba0e3cc7e8cd7c730c618c83e0934e726237232a7cb3b16f40/pandas-2.2.3.tar.gz"
    sha256 "4f18ba62b61d7e192368b84517265a99b4d7ee8912f8708660fb4a366cc82667"
  end

  resource "plotext" do
    url "https://files.pythonhosted.org/packages/fc/ab/ba1a5529ce3ce7c4dde4da599a65770a8ea548be60d4db2e14fee6477ce8/plotext-5.3.2.tar.gz"
    sha256 "988b18958c3ff3524bd7a5a6b997464692761307f60e23a9dfd3838fcf38ea75"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/a0/84/cc87cc65845ba6abe7cf6c8c9e715f5e3df4350d3b5d403c02a2faae0519/pydantic-2.10.6.tar.gz"
    sha256 "2dda86950d22872538f1dcfd64eb98e37b332c865b1b681c44a932da59d49448"
  end

  resource "pydantic-core" do
    url "https://files.pythonhosted.org/packages/fc/01/f3e5ac5e7c25833db5eb555f7b7ab24cd6f8c322d3a3ad2d67a952dc0abc/pydantic_core-2.27.2.tar.gz"
    sha256 "eb026e5a4c1fee05726072337ff51d1efb6f59090b7da90d30ea58625b1ffb39"
  end

  resource "pydantic-settings" do
    url "https://files.pythonhosted.org/packages/73/7b/c58a586cd7d9ac66d2ee4ba60ca2d241e55cdf4d48ee3755a86afe2dc540/pydantic_settings-2.7.1.tar.gz"
    sha256 "f44d9e117624a88762533988d31ba32a0d37cf51733392218b64e243f02eeeee"
  end

  resource "python-dateutil" do
    url "https://files.pythonhosted.org/packages/66/c0/0c8b6ad9f17a802ee498c46e004a0eb49bc148f2fd230864601a86dcf6db/python-dateutil-2.9.0.post0.tar.gz"
    sha256 "37dd54208da7e1cd875388217d5e00ebd4179249f90fb72437e91a35459a0ad3"
  end

  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/bc/57/e84d88dfe0aec03b7a2d4327012c1627571b18e997a2632e45ec1d925a37/python_dotenv-1.0.1.tar.gz"
    sha256 "e324ee90a023d808f1959c46bcbc04446a10ced277783dc6ee09987c37ec10ca"
  end

  resource "pytz" do
    url "https://files.pythonhosted.org/packages/5f/57/df1c9157c8d5a05117e455d66fd7cf6dbc46974f832b1058ed4856785d8a/pytz-2024.2.tar.gz"
    sha256 "2aa355083c50a0f93fa581709deac0c9ad65cca8a9e9beac660adcbd493c798a"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/ab/3a/0316b28d0761c6734d6bc14e770d85506c986c85ffb239e688eebd9b0571/rich-13.9.4.tar.gz"
    sha256 "439594978a49a09530cff7ebc4b5c7103ef57c5a1b8303c667a9e0e2cf7b20e3"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/71/39/171f1c67cd00715f190ba0b100d606d440a28c93c7714febeca8b79af85e/six-1.16.0.tar.gz"
    sha256 "1e61c37477a1626458e36f7b1d82aa5c9b094fa4802892072e49de9c60c4c926"
  end

  resource "sniffio" do
    url "https://files.pythonhosted.org/packages/a2/87/a6771e1546d97e7e041b6ae58d80074f81b7d5121207425c964ddf5cfdbd/sniffio-1.3.1.tar.gz"
    sha256 "f4324edc670a0f49750a81b895f35c3adb843cca46f0530f79fc1babb23789dc"
  end

  resource "typing-extensions" do
    url "https://files.pythonhosted.org/packages/df/db/f35a00659bc03fec321ba8bce9420de607a1d37f8342eee1863174c69557/typing_extensions-4.12.2.tar.gz"
    sha256 "1a7ead55c7e559dd4dee8856e3a88b41225abfe1ce8df57b7c13915fe121ffb8"
  end

  resource "tzdata" do
    url "https://files.pythonhosted.org/packages/e1/34/943888654477a574a86a98e9896bae89c7aa15078ec29f490fef2f1e5384/tzdata-2024.2.tar.gz"
    sha256 "7d85cc416e9382e69095b7bdf4afd9e3880418a2413feec7069d533d6b4e31cc"
  end

  resource "yfinance" do
    url "https://files.pythonhosted.org/packages/45/4d/56280b662e40549e1d567fdb794c65dcfd897d87674d08354762fb65bb09/yfinance-0.2.50.tar.gz"
    sha256 "bde710f89e0261986fb0250ee925d6f09f32458d1f022a789ff4a19907e85029"
  end

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      Sigma v2.0.0 - Institutional-Grade Financial Research Agent

      Get started:
        sigma --setup     # Configure API keys (first time)
        sigma             # Launch Sigma

      Get a FREE API key:
        Google Gemini: https://aistudio.google.com/apikey

      Documentation: https://github.com/desenyon/sigma
    EOS
  end

  test do
    assert_match "2.0.0", shell_output("#{bin}/sigma --version")
  end
end
```

---

## Step 6: Get the Tarball SHA256

After uploading to GitHub Releases:

```bash
curl -sL "https://github.com/desenyon/sigma/releases/download/v2.0.0/sigma_terminal-2.0.0.tar.gz" | shasum -a 256
```

**Update the formula** with this hash in the `sha256` line.

---

## Step 7: Push the Tap

```bash
cd ~/Projects/homebrew-sigma
git add .
git commit -m "Add sigma formula v2.0.0"
git push origin main
```

---

## Step 8: Test Installation

```bash
# Remove any old tap
brew untap desenyon/sigma 2>/dev/null

# Add your tap
brew tap desenyon/sigma

# Install
brew install sigma

# Run setup wizard
sigma --setup

# Launch
sigma
```

---

## Updating for New Releases

When releasing a new version:

### 1. Build new version
```bash
# Update version in pyproject.toml and sigma/__init__.py
# Then rebuild
python -m build
```

### 2. Create new release
```bash
gh release create v2.1.0 \
  dist/sigma_terminal-2.1.0-py3-none-any.whl \
  dist/sigma_terminal-2.1.0.tar.gz \
  --title "Sigma v2.1.0"
```

### 3. Get new hash
```bash
curl -sL "https://github.com/desenyon/sigma/releases/download/v2.1.0/sigma_terminal-2.1.0.tar.gz" | shasum -a 256
```

### 4. Update formula
Edit `Formula/sigma.rb`:
- Update `url` to new version
- Update `sha256` with new hash

### 5. Push
```bash
cd ~/Projects/homebrew-sigma
git commit -am "Update sigma to v2.1.0"
git push
```

### 6. Users upgrade
```bash
brew update && brew upgrade sigma
```

---

## Troubleshooting

### "SHA256 mismatch" error
- Re-download the file and recalculate the hash
- Make sure you're using the correct URL

### "Resource not found" error  
- Check if your repo is public
- If private, users need `HOMEBREW_GITHUB_API_TOKEN` set

### "No such file" error
- Make sure you attached the files to the GitHub release
- Check the download URL is correct

### Testing formula locally
```bash
brew install --build-from-source ./Formula/sigma.rb
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Build package | `python -m build` |
| Create release | `gh release create v2.0.0 dist/*` |
| Get SHA256 | `curl -sL <url> \| shasum -a 256` |
| Add tap | `brew tap desenyon/sigma` |
| Install | `brew install sigma` |
| Upgrade | `brew upgrade sigma` |
| Uninstall | `brew uninstall sigma` |
| Remove tap | `brew untap desenyon/sigma` |
