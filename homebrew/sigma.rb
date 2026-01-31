cask "sigma" do
  version "3.2.0"
  sha256 "505706a205e1555bf11f80c8e12d073f41e73a7379536546859ff63e3517dac8" # Replace with actual SHA256 when publishing

  url "https://github.com/desenyon/sigma/releases/download/v#{version}/Sigma-#{version}.dmg"
  name "Sigma"
  desc "Finance Research Agent - AI-powered market analysis"
  homepage "https://github.com/desenyon/sigma"

  # Requires Python 3.11+
  depends_on formula: "python@3.12"

  app "Sigma.app"

  # Install Python dependencies
  postflight do
    system_command "/opt/homebrew/bin/python3",
                   args: ["-m", "pip", "install", "--quiet", "sigma-terminal"],
                   sudo: false
  end

  zap trash: [
    "~/.sigma",
    "~/Library/Application Support/Sigma",
    "~/Library/Caches/Sigma",
    "~/Library/Preferences/com.sigma.app.plist",
  ]

  caveats <<~EOS
    Sigma requires API keys for AI providers. Configure them with:
      sigma --setkey google YOUR_API_KEY
      sigma --setkey openai YOUR_API_KEY

    Or launch the app and use /keys command.
  EOS
end
