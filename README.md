<p align="center">
  <img src="https://img.shields.io/badge/σ-SIGMA-blue?style=for-the-badge&labelColor=0a0a0f&color=3b82f6" alt="Sigma" height="60"/>
</p>

<h1 align="center">
  <code>σ</code> SIGMA
</h1>

<p align="center">
  <strong>The AI-Powered Finance Research Agent That Actually Gets It Done</strong>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-commands">Commands</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.3.0-blue.svg" alt="Version 3.3.0"/>
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="macOS"/>
  <img src="https://img.shields.io/badge/AI-Multi--Provider-purple.svg" alt="Multi-Provider AI"/>
  <img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License"/>
</p>

<br/>

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ███████╗██╗ ██████╗ ███╗   ███╗ █████╗                                     ║
║   ██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗                                    ║
║   ███████╗██║██║  ███╗██╔████╔██║███████║     Finance Research Agent         ║
║   ╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║     v3.3.0 | Native macOS          ║
║   ███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║                                    ║
║   ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝                                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 🎯 What is Sigma?

**Sigma isn't just another finance app.** It's a conversational AI agent that thinks like a quant, analyzes like a hedge fund, and speaks like your smartest friend who happens to be a CFA.

```
You: "Should I buy NVDA?"

σ: Let me analyze that...
   ⠋ get_stock_quote executing...
   ✓ get_stock_quote complete
   ⠹ technical_analysis executing...
   ✓ technical_analysis complete
   ⠸ get_analyst_recommendations executing...
   ✓ get_analyst_recommendations complete

┌─────────────────────────────────────────────────────────────────────┐
│ σ Sigma                                                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📊 NVDA Analysis | Current: $875.32 (+2.4%)                       │
│                                                                     │
│  TECHNICAL SIGNALS:                                                 │
│  • RSI: 67.2 (approaching overbought)                              │
│  • MACD: Bullish crossover 3 days ago                              │
│  • Above 20/50/200 SMA ✓                                           │
│                                                                     │
│  FUNDAMENTALS:                                                      │
│  • P/E: 65.2 (premium to sector)                                   │
│  • Revenue Growth: +122% YoY                                        │
│  • AI/Data Center: 83% of revenue                                   │
│                                                                     │
│  ANALYST CONSENSUS: Strong Buy (45 analysts)                        │
│  Price Target: $950 (median) | Range: $620-$1,200                  │
│                                                                     │
│  ⚡ VERDICT: BUY on pullbacks to $820-850 support                   │
│  Risk: High volatility, valuation stretched                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start

### One Command Install

```bash
pip install sigma-terminal
```

### First Launch = Automatic Setup

```bash
sigma
```

**That's it.** Sigma detects it's your first time and walks you through:

1. **🤖 Choose AI Provider** — Google Gemini, OpenAI, Anthropic, Groq, xAI, or Ollama
2. **🔑 Enter API Key** — Or use local Ollama (completely free, no key needed!)
3. **🔍 Auto-detect Integrations** — Finds Ollama, LEAN, and more
4. **🚀 Launch Directly** — Straight into the beautiful terminal UI

Your config persists at `~/.sigma/` — **setup never asks again**.

---

## 🚀 Features

### 🤖 Multi-Provider AI Engine

Switch between providers on the fly. Use free tiers or bring your own keys.

| Provider | Models | Speed | Cost | Tool Calls |
|----------|--------|-------|------|------------|
| **Google Gemini** | gemini-2.0-flash, 1.5-pro | ⚡⚡⚡ | Free tier | ✓ Native |
| **OpenAI** | gpt-4o, o1-preview | ⚡⚡ | Paid | ✓ Native |
| **Anthropic** | claude-sonnet-4, opus | ⚡⚡ | Paid | ✓ Native |
| **Groq** | llama-3.3-70b | ⚡⚡⚡⚡ | Free tier | ✓ Native |
| **xAI** | grok-2 | ⚡⚡ | Paid | ✓ Native |
| **Ollama** | llama3.2, mistral, phi3 | ⚡ | **100% FREE** | ✓ Native |

**🛡️ Built-in Rate Limiting** — No more API flooding or timeouts. Sigma intelligently manages request rates per provider.

### 📊 Real-Time Market Intelligence

Every tool is a function call. The AI decides what to use.

| Tool | What It Does |
|------|--------------|
| `get_stock_quote` | Live price, change, volume, market cap |
| `technical_analysis` | RSI, MACD, Bollinger, MAs, Support/Resistance |
| `get_financial_statements` | Income, balance sheet, cash flow |
| `get_analyst_recommendations` | Price targets, ratings, consensus |
| `get_insider_trades` | Who's buying, who's selling |
| `get_institutional_holders` | Track the smart money |
| `compare_stocks` | Multi-stock comparison with metrics |
| `get_market_overview` | Major indices at a glance |
| `get_sector_performance` | Sector rotation analysis |

### 📈 Backtesting Engine

Test strategies before risking capital:

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `sma_crossover` | 20/50 MA crossover | Trend following |
| `rsi` | RSI oversold/overbought | Mean reversion |
| `macd` | MACD signal crossovers | Momentum |
| `bollinger` | Band breakout/bounce | Volatility |
| `momentum` | Price momentum | Trend continuation |
| `breakout` | S/R level breaks | Breakout trading |

```bash
# Via CLI
sigma backtest AAPL --strategy sma_crossover --period 2y

# Via chat
You: "Backtest RSI strategy on SPY for the last year"
```

### 🔧 LEAN Integration (Auto-Detected!)

Sigma automatically finds your LEAN/QuantConnect installation:

```
✓ LEAN/QuantConnect detected!
  CLI: /usr/local/bin/lean
  Directory: /Users/you/Lean

Enable LEAN integration? [y/n] (y): y
σ LEAN integration enabled
```

**Don't have LEAN?** Sigma offers to install it for you:

```
! LEAN/QuantConnect not detected
Would you like to [install/manual/skip] (skip): install

σ Installing LEAN CLI via pip...
✓ LEAN CLI installed successfully!
```

### 🎨 Beautiful Terminal UI

- **Animated Tool Calls** — Watch `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏` spin as tools execute
- **Live Ticker Detection** — Type `AAPL` and see `$AAPL` highlighted instantly
- **Smart Autocomplete** — Tab to complete commands and tickers
- **Pulsing σ Indicator** — Subtle animation shows Sigma is thinking
- **Rich Responses** — Markdown tables, formatting, structure

---

## 💻 Commands

### In-App Commands

| Command | Description |
|---------|-------------|
| `/help` | Comprehensive help with examples |
| `/clear` | Clear chat history |
| `/keys` | Configure API keys |
| `/models` | Show available models |
| `/status` | Current configuration |
| `/provider <name>` | Switch AI provider |
| `/model <name>` | Switch model |
| `/backtest` | Show backtesting strategies |
| `/tickers` | Popular tickers by category |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Tab` | Autocomplete suggestion |
| `Ctrl+L` | Clear chat |
| `Ctrl+M` | Show models |
| `Ctrl+H` | Toggle quick help |
| `Ctrl+P` | Command palette |
| `Esc` | Cancel operation |

### CLI Commands

```bash
# Launch interactive mode
sigma

# Quick queries (no UI)
sigma ask "analyze AAPL"
sigma quote AAPL MSFT NVDA
sigma compare AAPL MSFT GOOGL

# Backtesting
sigma backtest AAPL --strategy sma_crossover --period 2y

# Configuration
sigma --setup           # Re-run setup wizard
sigma --status          # Show current config
sigma --setkey google YOUR_API_KEY
sigma --provider ollama
sigma --model llama3.2
sigma --list-models     # Show all available models
```

---

## 🧠 Natural Language Examples

Sigma understands you. Just talk to it:

**Analysis**
```
"What's happening with AAPL today?"
"Give me a full breakdown of NVDA"
"Is TSLA overvalued right now?"
```

**Comparison**
```
"Compare NVDA, AMD, and INTC"
"Which is better: GOOGL or META?"
"Show me the Magnificent 7 stocks side by side"
```

**Technical**
```
"Technical analysis of QQQ"
"What are the support and resistance levels for SPY?"
"Is AAPL overbought?"
```

**Fundamentals**
```
"What's the P/E ratio of MSFT?"
"Show me AMZN's revenue growth"
"Income statement for GOOGL"
```

**Activity**
```
"Who are the biggest institutional holders of AAPL?"
"Any insider trading at TSLA?"
"What are analysts saying about META?"
```

**Market**
```
"How's the market doing?"
"Which sectors are hot right now?"
"Give me a market overview"
```

**Backtesting**
```
"Backtest SMA crossover on SPY"
"Run RSI strategy on AAPL for 2 years"
"Test momentum strategy on QQQ"
```

---

## 🏗️ Architecture

```
sigma/
├── app.py          # Textual TUI application
│                   # - ToolCallDisplay (animated spinners)
│                   # - SigmaIndicator (pulsing σ)
│                   # - TickerHighlight (real-time detection)
│                   # - ChatLog (rich formatting)
│
├── cli.py          # CLI entry point
│                   # - First-run detection
│                   # - Auto-launch setup → interactive
│                   # - Subcommands (ask, quote, backtest)
│
├── config.py       # Settings & persistence
│                   # - detect_lean_installation()
│                   # - detect_ollama()
│                   # - install_lean_cli_sync()
│                   # - ~/.sigma/config.env
│
├── setup.py        # First-run setup wizard
│                   # - Provider selection
│                   # - API key configuration
│                   # - Integration auto-detection
│                   # - LEAN download option
│
├── llm.py          # Multi-provider AI clients
│                   # - RateLimiter (per-provider)
│                   # - GoogleLLM, OpenAILLM, AnthropicLLM
│                   # - GroqLLM, OllamaLLM (with tool calls!)
│
├── tools.py        # Financial data tools
│                   # - 11 tool functions
│                   # - OpenAI-compatible schema
│                   # - yfinance data source
│
├── backtest.py     # Backtesting engine
│                   # - 6 built-in strategies
│                   # - Performance metrics
│                   # - Risk analysis
│
└── analytics/      # Advanced analytics (v4.0)
```

### Key Design Decisions

| Decision | Why |
|----------|-----|
| **Provider Abstraction** | All LLMs implement `BaseLLM.generate()` — easy to add new providers |
| **Tool System** | OpenAI-compatible function calling works across all providers |
| **Rate Limiting** | Per-provider `RateLimiter` prevents API flooding automatically |
| **Config Persistence** | Simple env file at `~/.sigma/config.env` — human readable |
| **First-Run Detection** | Marker file `.first_run_complete` ensures smooth onboarding |
| **Textual TUI** | Modern Python TUI framework with async support |

---

## 🔧 Configuration

### Config Location

```
~/.sigma/
├── config.env           # API keys and settings
└── .first_run_complete  # First-run marker
```

### Config File Format

```bash
# ~/.sigma/config.env

# API Keys
GOOGLE_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=gsk_...
XAI_API_KEY=xai-...

# Defaults
DEFAULT_PROVIDER=google
DEFAULT_MODEL=gemini-2.0-flash

# Integrations
OLLAMA_HOST=http://localhost:11434
LEAN_ENABLED=true
LEAN_CLI_PATH=/usr/local/bin/lean
LEAN_DIRECTORY=/Users/you/Lean

# Data
OUTPUT_DIR=/Users/you/Documents/Sigma
CACHE_ENABLED=true
```

---

## 🗺️ Roadmap

### ✅ v3.3.0 (Current)
- [x] Auto-setup on first launch
- [x] LEAN auto-detection with install option
- [x] API rate limiting (no more timeouts!)
- [x] Ollama native tool call support
- [x] Enhanced ticker recognition
- [x] Animated tool call display
- [x] Pulsing σ indicator
- [x] Smart autocomplete
- [x] Comprehensive help system

### 🔜 v3.4.0 (Next)
- [ ] Portfolio tracking & management
- [ ] Watchlists with price alerts
- [ ] Options flow analysis
- [ ] Earnings calendar integration
- [ ] Multi-ticker comparison charts
- [ ] Export to CSV/PDF

### 🔮 v4.0.0 (Future)
- [ ] Full LEAN backtesting integration
- [ ] Paper trading mode
- [ ] Custom strategy builder (visual)
- [ ] Discord/Slack notifications
- [ ] REST API for external integrations
- [ ] Multi-user support

---

## 🛠️ Development

### Prerequisites

- Python 3.11+
- macOS (for native app bundle)

### Setup

```bash
# Clone
git clone https://github.com/yourusername/sigma.git
cd sigma

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run
python -m sigma
```

### Build macOS App Bundle

```bash
./scripts/build.sh

# Outputs:
# - dist/sigma_terminal-3.3.0-py3-none-any.whl
# - dist/Sigma.app (drag to /Applications)
```

### Project Structure

```bash
sigma/
├── pyproject.toml    # Package configuration
├── README.md         # You are here
├── LICENSE           # Proprietary license
├── scripts/
│   ├── build.sh      # Build script
│   └── create_app.py # macOS app bundle creator
└── sigma/
    ├── __init__.py   # Package exports
    ├── __main__.py   # Entry point
    └── ...           # Core modules
```

---

## 🙏 Acknowledgments

Built with:
- [Textual](https://textual.textualize.io/) — Beautiful TUIs in Python
- [Rich](https://rich.readthedocs.io/) — Rich text formatting
- [yfinance](https://github.com/ranaroussi/yfinance) — Yahoo Finance data
- [Plotly](https://plotly.com/python/) — Interactive charts
- [Pydantic](https://docs.pydantic.dev/) — Data validation

AI Providers:
- [Google Gemini](https://ai.google.dev/)
- [OpenAI](https://openai.com/)
- [Anthropic](https://anthropic.com/)
- [Groq](https://groq.com/)
- [xAI](https://x.ai/)
- [Ollama](https://ollama.ai/)

---

## 📜 License

Proprietary. All rights reserved.

---

<p align="center">
  <strong>Built with 🧠 by humans who got tired of slow, clunky finance tools.</strong>
</p>

<p align="center">
  <code>σ</code> — Because your portfolio deserves an AI that actually works.
</p>

<p align="center">
  <sub>Star ⭐ this repo if Sigma saved you time!</sub>
</p>
