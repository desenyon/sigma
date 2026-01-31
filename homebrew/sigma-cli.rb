class SigmaCli < Formula
  include Language::Python::Virtualenv

  desc "Finance Research Agent - AI-powered market analysis CLI"
  homepage "https://github.com/desenyon/sigma"
  url "https://github.com/desenyon/sigma/archive/refs/tags/v3.2.0.tar.gz"
  sha256 "202d6e8bf76a5b355179298ccc0de18dbc375a7c91531e1cf4e0dbef68862bf7"
  license :cannot_represent  # Proprietary
  head "https://github.com/desenyon/sigma.git", branch: "main"
  depends_on "python@3.12"

  # UI and Console
  resource "textual" do
    url "https://files.pythonhosted.org/packages/source/t/textual/textual-0.47.1.tar.gz"
    sha256 "4b82e317884bb1092f693f474c319ceb068b5a0b128b121f1aa53a2d48b4b80c"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.1.tar.gz"
    sha256 "9be308cb1fe2f1f57d67ce99e95af38a1e2bc71ad9813b0e247cf7ffbcc3a432"
  end

  # AI Providers
  resource "openai" do
    url "https://files.pythonhosted.org/packages/source/o/openai/openai-1.12.0.tar.gz"
    sha256 "99c5d257d09ea6533d689d1cc77caa0ac679fa21efef8893d8b0832a86877f1b"
  end

  resource "anthropic" do
    url "https://files.pythonhosted.org/packages/source/a/anthropic/anthropic-0.18.1.tar.gz"
    sha256 "f5d1caafd43f6cc933a79753a93531605095f040a384f6a900c3de9c3fb6694e"
  end

  resource "google-genai" do
    url "https://files.pythonhosted.org/packages/source/g/google-genai/google-genai-1.0.0.tar.gz"
    sha256 "15712abb808f891a14eafc9edf21b8cf92ea952f627dd0e2e939657efd234acd"
  end

  resource "groq" do
    url "https://files.pythonhosted.org/packages/source/g/groq/groq-0.4.2.tar.gz"
    sha256 "42e8b0abd0f2b2da024b9a747d28960d62951a5364f078e1537c9fceeca8259d"
  end

  # Data and Finance
  resource "yfinance" do
    url "https://files.pythonhosted.org/packages/source/y/yfinance/yfinance-0.2.36.tar.gz"
    sha256 "5367c0538cf57bb0dd393ca24866cda1ab5d4aba47e375e549760652a4a19fc2"
  end

  resource "pandas" do
    url "https://files.pythonhosted.org/packages/source/p/pandas/pandas-2.2.0.tar.gz"
    sha256 "30b83f7c3eb217fb4d1b494a57a2fda5444f17834f5df2de6b2ffff68dc3c8e2"
  end

  resource "numpy" do
    url "https://files.pythonhosted.org/packages/source/n/numpy/numpy-1.26.4.tar.gz"
    sha256 "2a02aba9ed12e4ac4eb3ea9421c420301a0c6460d9830d74a9df87efa4912010"
  end

  resource "scipy" do
    url "https://files.pythonhosted.org/packages/source/s/scipy/scipy-1.12.0.tar.gz"
    sha256 "4bf5abab8a36d20193c698b0f1fc282c1d083c94723902c447e5d2f1780936a3"
  end

  # Visualization
  resource "plotly" do
    url "https://files.pythonhosted.org/packages/source/p/plotly/plotly-5.18.0.tar.gz"
    sha256 "360a31e6fbb49d12b007036eb6929521343d6bee2236f8459915821baefa2cbb"
  end

  resource "kaleido" do
    url "https://files.pythonhosted.org/packages/source/k/kaleido/kaleido-0.2.1.tar.gz"
    sha256 "ca6f73e7ff00aaebf2843f73f1d3bacde1930ef5041093fe76b83a15785049a7"
  end

  resource "plotext" do
    url "https://files.pythonhosted.org/packages/source/p/plotext/plotext-5.2.8.tar.gz"
    sha256 "319a287baabeb8576a711995f973a2eba631c887aa6b0f33ab016f12c50ffebe"
  end

  # HTTP and API
  resource "httpx" do
    url "https://files.pythonhosted.org/packages/source/h/httpx/httpx-0.26.0.tar.gz"
    sha256 "451b55c30d5185ea6b23c2c793abf9bb237d2a7dfb901ced6ff69ad37ec1dfaf"
  end

  resource "aiohttp" do
    url "https://files.pythonhosted.org/packages/source/a/aiohttp/aiohttp-3.9.3.tar.gz"
    sha256 "90842933e5d1ff760fae6caca4b2b3edba53ba8f4b71e95dacf2818a2aca06f7"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.31.0.tar.gz"
    sha256 "942c5a758f98d790eaed1a29cb6eefc7ffb0d1cf7af05c3d2791656dbd6ad1e1"
  end

  # Configuration
  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/source/p/python-dotenv/python-dotenv-1.0.1.tar.gz"
    sha256 "e324ee90a023d808f1959c46bcbc04446a10ced277783dc6ee09987c37ec10ca"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.6.1.tar.gz"
    sha256 "4fd5c182a2488dc63e6d32737ff19937888001e2a6d86e94b3f233104a5d1fa9"
  end

  resource "pydantic-settings" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic-settings/pydantic-settings-2.1.0.tar.gz"
    sha256 "26b1492e0a24755626ac5e6d715e9077ab7ad4fb5f19a8b7ed7011d52f36141c"
  end

  # macOS Native
  resource "Pillow" do
    url "https://files.pythonhosted.org/packages/source/p/pillow/pillow-10.2.0.tar.gz"
    sha256 "e87f0b2c78157e12d7686b27d63c070fd65d994e8ddae6f328e0dcf4a0cd007e"
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
