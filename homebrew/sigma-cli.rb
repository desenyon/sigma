class SigmaCli < Formula
  include Language::Python::Virtualenv

  desc "Finance Research Agent - AI-powered market analysis CLI"
  homepage "https://github.com/desenyon/sigma"
  url "https://github.com/desenyon/sigma/archive/refs/tags/v3.2.0.tar.gz"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"
  license :cannot_represent  # Proprietary
  head "https://github.com/desenyon/sigma.git", branch: "main"
  depends_on "python@3.12"

  # UI and Console
  resource "textual" do
    url "https://files.pythonhosted.org/packages/source/t/textual/textual-0.47.1.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.1.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  # AI Providers
  resource "openai" do
    url "https://files.pythonhosted.org/packages/source/o/openai/openai-1.12.0.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "anthropic" do
    url "https://files.pythonhosted.org/packages/source/a/anthropic/anthropic-0.18.1.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "google-genai" do
    url "https://files.pythonhosted.org/packages/source/g/google-genai/google-genai-1.0.0.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "groq" do
    url "https://files.pythonhosted.org/packages/source/g/groq/groq-0.4.2.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  # Data and Finance
  resource "yfinance" do
    url "https://files.pythonhosted.org/packages/source/y/yfinance/yfinance-0.2.36.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "pandas" do
    url "https://files.pythonhosted.org/packages/source/p/pandas/pandas-2.2.0.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "numpy" do
    url "https://files.pythonhosted.org/packages/source/n/numpy/numpy-1.26.4.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "scipy" do
    url "https://files.pythonhosted.org/packages/source/s/scipy/scipy-1.12.0.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  # Visualization
  resource "plotly" do
    url "https://files.pythonhosted.org/packages/source/p/plotly/plotly-5.18.0.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "kaleido" do
    url "https://files.pythonhosted.org/packages/source/k/kaleido/kaleido-0.2.1.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  # HTTP and API
  resource "httpx" do
    url "https://files.pythonhosted.org/packages/source/h/httpx/httpx-0.26.0.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "aiohttp" do
    url "https://files.pythonhosted.org/packages/source/a/aiohttp/aiohttp-3.9.3.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.31.0.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  # Configuration
  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/source/p/python-dotenv/python-dotenv-1.0.1.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.6.1.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  resource "pydantic-settings" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic-settings/pydantic-settings-2.1.0.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  # macOS Native
  resource "Pillow" do
    url "https://files.pythonhosted.org/packages/source/p/pillow/pillow-10.2.0.tar.gz"
    sha256 "REPLACE_WITH_ACTUAL_SHA256"
  end

  def install
    virtualenv_install_with_resources
  end

  def caveats
    <<~EOS
      Sigma v3.2.0 - Finance Research Agent

      Configure API keys:
        sigma --setkey google YOUR_API_KEY
        sigma --setkey openai YOUR_API_KEY

      Or run sigma and use the /keys command.

      Quick start:
        sigma                    # Launch interactive mode
        sigma ask "analyze AAPL" # Quick query
        sigma quote AAPL MSFT    # Get quotes
    EOS
  end

  test do
    assert_match "v3.2.0", shell_output("#{bin}/sigma --version")
  end
end
