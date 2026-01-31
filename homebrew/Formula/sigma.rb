# Homebrew Formula for Sigma
# 
# To use this formula:
# 1. Create a GitHub repo called 'homebrew-sigma'
# 2. Put this file in Formula/sigma.rb
# 3. Host your wheel file somewhere (GitHub releases, S3, etc)
# 4. Update the url and sha256 below
# 5. Users install with: brew tap yourusername/sigma && brew install sigma

class Sigma < Formula
  include Language::Python::Virtualenv

  desc "Institutional-Grade Financial Research Agent"
  homepage "https://github.com/desenyon/sigma"
  url "https://github.com/desenyon/sigma/releases/download/v2.0.0/sigma_terminal-2.0.0-py3-none-any.whl"
  sha256 "UPDATE_WITH_ACTUAL_SHA256"
  license :cannot_represent  # Proprietary
  
  depends_on "python@3.12"

  # Core dependencies
  resource "httpx" do
    url "https://files.pythonhosted.org/packages/source/h/httpx/httpx-0.27.0.tar.gz"
    sha256 "a0cb88a46f32dc874e04ee956e4c2764aba2aa228f650b06788ba6bda2962ab5"
  end

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.0.tar.gz"
    sha256 "5cb5f8d2b2f2ce6a2e0ca6e1a5b5b2f6d2e0ca6e1a5b5b2f6d2e0ca6e1a5b5b2f"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.6.0.tar.gz"
    sha256 "UPDATE_SHA"
  end

  resource "yfinance" do
    url "https://files.pythonhosted.org/packages/source/y/yfinance/yfinance-0.2.40.tar.gz"
    sha256 "UPDATE_SHA"
  end

  # Add all other dependencies similarly...

  def install
    virtualenv_install_with_resources

    # Create wrapper script
    (bin/"sigma").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/bin/python" -m sigma "$@"
    EOS
  end

  def post_install
    # Run setup wizard on first install
    system bin/"sigma", "--setup"
  end

  def caveats
    <<~EOS
      Sigma has been installed!

      To get started:
        sigma

      To configure API keys:
        sigma --setup

      For help:
        sigma --help

      Documentation: https://github.com/desenyon/sigma/wiki
    EOS
  end

  test do
    assert_match "Sigma", shell_output("#{bin}/sigma --version")
  end
end
