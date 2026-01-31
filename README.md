<h1 align="center">
  <code>σ</code> SIGMA
</h1>

<p align="center">
  <strong>The AI-Powered Finance Research Agent</strong>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#commands">Commands</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#roadmap">Roadmap</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.3.1-blue.svg" alt="Version 3.3.1"/>
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/platform-macOS-lightgrey.svg" alt="macOS"/>
  <img src="https://img.shields.io/badge/AI-Multi--Provider-purple.svg" alt="Multi-Provider AI"/>
  <img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License"/>
</p>

---

## What is Sigma?

**Sigma isn't just another finance app.** It's a conversational AI agent that thinks like a quant, analyzes like a hedge fund, and speaks like your smartest friend who happens to be a CFA.

## Quick Start

### One Command Install

```bash
pip install sigma-terminal
```

### First Launch = Automatic Setup

```bash
python -m sigma
```

**That's it.** Sigma detects it's your first time and walks you through:

1. **Choose AI Provider** — Google Gemini, OpenAI, Anthropic, Groq, xAI, or Ollama
2. **Enter API Key** — Or use local Ollama (completely free, no key needed!)
3. **Auto-detect Integrations** — Finds Ollama, LEAN, and more
4. **Launch Directly** — Straight into the beautiful terminal UI

Your config persists at `~/.sigma/` — **setup never asks again**.

---

## Features

### Multi-Provider AI Engine

Switch between providers on the fly. Use free tiers or bring your own keys.

| Provider                | Models                    | Speed     | Cost                | Tool Calls |
| ----------------------- | ------------------------- | --------- | ------------------- | ---------- |
| **Google Gemini** | gemini-2.0-flash, 1.5-pro | Fast      | Free tier           | Native     |
| **OpenAI**        | gpt-4o, o1-preview        | Fast      | Paid                | Native     |
| **Anthropic**     | claude-sonnet-4, opus     | Fast      | Paid                | Native     |
| **Groq**          | llama-3.3-70b             | Very Fast | Free tier           | Native     |
| **xAI**           | grok-2                    | Fast      | Paid                | Native     |
| **Ollama**        | llama3.2, mistral, phi3   | Local     | **100% FREE** | Native     |

**Built-in Rate Limiting** — No more API flooding or timeouts. Sigma intelligently manages request rates per provider.

### Real-Time Market Intelligence

Every tool is a function call. The AI decides what to use.

| Tool                            | What It Does                                  |
| ------------------------------- | --------------------------------------------- |
| `get_stock_quote`             | Live price, change, volume, market cap        |
| `technical_analysis`          | RSI, MACD, Bollinger, MAs, Support/Resistance |
| `get_financial_statements`    | Income, balance sheet, cash flow              |
| `get_analyst_recommendations` | Price targets, ratings, consensus             |
| `get_insider_trades`          | Who's buying, who's selling                   |
| `get_institutional_holders`   | Track the smart money                         |
| `compare_stocks`              | Multi-stock comparison with metrics           |
| `get_market_overview`         | Major indices at a glance                     |
| `get_sector_performance`      | Sector rotation analysis                      |

### Data APIs

| Tool                           | Source        | What It Does                            |
| ------------------------------ | ------------- | --------------------------------------- |
| `get_economic_indicators`    | Alpha Vantage | GDP, inflation, unemployment, CPI, etc. |
| `get_intraday_data`          | Alpha Vantage | 1min to 60min candles                   |
| `get_market_news`            | Alpha Vantage | News with sentiment analysis            |
| `search_financial_news`      | Exa           | Search Bloomberg, Reuters, WSJ          |
| `search_sec_filings`         | Exa           | 10-K, 10-Q, 8-K filings                 |
| `search_earnings_transcripts`| Exa           | Earnings call transcripts               |

**Alpha Vantage** — Built-in free API key included. Works out of the box.

**Exa Search** — Optional. Get your key at https://exa.ai and configure during setup.

### Backtesting Engine

Test strategies before risking capital:

| Strategy          | Description             | Use Case           |
| ----------------- | ----------------------- | ------------------ |
| `sma_crossover` | 20/50 MA crossover      | Trend following    |
| `rsi`           | RSI oversold/overbought | Mean reversion     |
| `macd`          | MACD signal crossovers  | Momentum           |
| `bollinger`     | Band breakout/bounce    | Volatility         |
| `momentum`      | Price momentum          | Trend continuation |
| `breakout`      | S/R level breaks        | Breakout trading   |

```bash
# Via CLI
sigma backtest AAPL --strategy sma_crossover --period 2y

# Via chat
You: "Backtest RSI strategy on SPY for the last year"
```

### LEAN Integration (Auto-Detected!)

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

### Beautiful Terminal UI

- **Animated Tool Calls** — Watch `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏` spin as tools execute
- **Live Ticker Detection** — Type `AAPL` and see `$AAPL` highlighted instantly
- **Smart Autocomplete** — Tab to complete commands and tickers
- **Pulsing σ Indicator** — Subtle animation shows Sigma is thinking
- **Rich Responses** — Markdown tables, formatting, structure

---

## Commands

### In-App Commands

| Command              | Description                      |
| -------------------- | -------------------------------- |
| `/help`            | Comprehensive help with examples |
| `/clear`           | Clear chat history               |
| `/keys`            | Configure API keys               |
| `/models`          | Show available models            |
| `/status`          | Current configuration            |
| `/provider <name>` | Switch AI provider               |
| `/model <name>`    | Switch model                     |
| `/backtest`        | Show backtesting strategies      |
| `/tickers`         | Popular tickers by category      |

### Keyboard Shortcuts

| Shortcut   | Action                  |
| ---------- | ----------------------- |
| `Tab`    | Autocomplete suggestion |
| `Ctrl+L` | Clear chat              |
| `Ctrl+M` | Show models             |
| `Ctrl+H` | Toggle quick help       |
| `Ctrl+P` | Command palette         |
| `Esc`    | Cancel operation        |

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

## Natural Language Examples

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

## Configuration

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

## Roadmap

### v3.3.1 (Current)

- [X] Auto-setup on first launch
- [X] LEAN auto-detection with install option
- [X] API rate limiting (no more timeouts!)
- [X] Ollama native tool call support
- [X] Enhanced ticker recognition
- [X] Animated tool call display
- [X] Pulsing indicator
- [X] Smart autocomplete
- [X] Comprehensive help system
- [X] Alpha Vantage integration (economic data, intraday, news)
- [X] Exa Search integration (financial news, SEC filings, earnings transcripts)

### v3.4.0 (Next)

- [ ] Portfolio tracking & management
- [ ] Watchlists with price alerts
- [ ] Options flow analysis
- [ ] Earnings calendar integration
- [ ] Multi-ticker comparison charts
- [ ] Export to CSV/PDF

### v4.0.0 (Future)

- [ ] Full LEAN backtesting integration
- [ ] Paper trading mode
- [ ] Custom strategy builder (visual)
- [ ] Discord/Slack notifications
- [ ] REST API for external integrations
- [ ] Multi-user support

---

## Acknowledgments

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

## License

Proprietary. All rights reserved.

---

<p align="center">
  <strong>Built by humans who got tired of slow, clunky finance tools.</strong>
</p>

<p align="center">
  <code>σ</code> — Because your portfolio deserves an AI that actually works.
</p>

<p align="center">
  <sub>Star this repo if Sigma saved you time!</sub>
</p>
