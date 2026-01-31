# Simpler Homebrew Formula using pipx
# This is the recommended approach - much easier to maintain

class Sigma < Formula
  desc "Institutional-Grade Financial Research Agent"
  homepage "https://github.com/desenyon/sigma"
  url "https://files.pythonhosted.org/packages/source/s/sigma-terminal/sigma_terminal-2.0.0.tar.gz"
  sha256 "UPDATE_WITH_SHA256_FROM_PYPI"
  license :cannot_represent  # Proprietary

  depends_on "pipx"
  depends_on "python@3.12"

  def install
    # Install using pipx into formula prefix
    system "pipx", "install", "sigma-terminal==#{version}",
           "--pip-args=--no-cache-dir"
    
    # Link the binary
    bin.install_symlink Dir["#{HOMEBREW_PREFIX}/bin/sigma"]
  end

  def post_install
    ohai "Running Sigma setup wizard..."
    system bin/"sigma", "--setup"
  end

  def caveats
    <<~EOS
      
      ███████╗██╗ ██████╗ ███╗   ███╗ █████╗ 
      ██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗
      ███████╗██║██║  ███╗██╔████╔██║███████║
      ╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║
      ███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
      ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝

      Sigma has been installed successfully!

      Get started:
        sigma                 Launch Sigma
        sigma --setup         Configure API keys
        sigma --help          Show help

      Quick examples:
        sigma "Analyze NVDA"
        sigma "Compare AAPL MSFT GOOGL"

    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/sigma --version")
  end
end
