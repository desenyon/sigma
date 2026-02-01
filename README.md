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
  <img src="https://img.shields.io/badge/version-3.4.0-blue.svg" alt="Version 3.4.0"/>
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/platform-cross--platform-lightgrey.svg" alt="Cross Platform"/>
  <img src="https://img.shields.io/badge/AI-Multi--Provider-purple.svg" alt="Multi-Provider AI"/>
  <img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License"/>
</p>

---

## What is Sigma?

**Sigma isn't just another finance app.** It's a conversational AI agent that thinks like a quant, analyzes like a hedge fund, and speaks like your smartest friend who happens to be a CFA.

## Quick Start

### One Command Install

\`\`\`bash
pip install sigma-terminal
\`\`\`

### Launch Sigma

\`\`\`bash
sigma
\`\`\`

Or alternatively: `python -m sigma`

### First Launch = Automatic Setup

**That's it.** Sigma detects it's your first time and walks you through:

1. **Choose AI Provider** — Google Gemini, OpenAI, Anthropic, Groq, xAI, or Ollama
2. **Enter API Key** — Or use local Ollama (completely free, no key needed!)
3. **Auto-detect Integrations** — Finds Ollama, LEAN, and more
4. **Launch Directly** — Straight into the beautiful terminal UI

Your config persists at \`~/.sigma/\` — **setup never asks again**.

---

## Features

### Multi-Provider AI Engine

Switch between providers on the fly. Use free tiers or bring your own keys.

| Provider                | Models                       | Speed     | Cost           | Tool Calls |
| ----------------------- | ---------------------------- | --------- | -------------- | ---------- |
| **Google Gemini** | gemini-2.5-flash, 2.5-pro    | Fast      | Free tier      | Native     |
| **OpenAI**        | gpt-4o, gpt-4o-mini, o3-mini | Fast      | Paid           | Native     |
| **Anthropic**     | claude-sonnet-4, 3.5-sonnet  | Fast      | Paid           | Native     |
| **Groq**          | llama-3.3-70b                | Very Fast | Free tier      | Native     |
| **xAI**           | grok-2, grok-2-mini          | Fast      | Paid           | Native     |
| **Ollama**        | llama3.2, mistral, phi3      | Local     | **FREE** | Native     |

**Built-in Rate Limiting** — No more API flooding or timeouts.

**Error Codes** — Clear error codes (E1100-E1400) help you quickly diagnose issues.

### Real-Time Market Intelligence

| Tool                            | What It Does                                  |
| ------------------------------- | --------------------------------------------- |
| \`get_stock_quote\`             | Live price, change, volume, market cap        |
| \`technical_analysis\`          | RSI, MACD, Bollinger, MAs, Support/Resistance |
| \`get_financial_statements\`    | Income, balance sheet, cash flow              |
| \`get_analyst_recommendations\` | Price targets, ratings, consensus             |
| \`get_insider_trades\`          | Who's buying, who's selling                   |
| \`get_institutional_holders\`   | Track the smart money                         |
| \`compare_stocks\`              | Multi-stock comparison with metrics           |
| \`get_market_overview\`         | Major indices at a glance                     |
| \`get_sector_performance\`      | Sector rotation analysis                      |

### Data APIs

| Tool                        | Source        | What It Does                         |
| --------------------------- | ------------- | ------------------------------------ |
| \`get_economic_indicators\` | Alpha Vantage | GDP, inflation, unemployment, CPI    |
| \`get_intraday_data\`       | Alpha Vantage | 1min to 60min candles                |
| \`get_market_news\`         | Alpha Vantage | News with sentiment analysis         |
| \`polygon_get_quote\`       | Polygon.io    | Real-time quotes with extended data  |
| \`polygon_get_aggregates\`  | Polygon.io    | Historical bars with custom timespan |
| \`polygon_get_ticker_news\` | Polygon.io    | News articles for specific tickers   |
| \`search_financial_news\`   | Exa           | Search Bloomberg, Reuters, WSJ       |
| \`search_sec_filings\`      | Exa           | 10-K, 10-Q, 8-K filings              |

### Backtesting Engine

| Strategy          | Description             | Use Case           |
| ----------------- | ----------------------- | ------------------ |
| \`sma_crossover\` | 20/50 MA crossover      | Trend following    |
| \`rsi\`           | RSI oversold/overbought | Mean reversion     |
| \`macd\`          | MACD signal crossovers  | Momentum           |
| \`bollinger\`     | Band breakout/bounce    | Volatility         |
| \`momentum\`      | Price momentum          | Trend continuation |
| \`breakout\`      | S/R level breaks        | Breakout trading   |

---

## Commands

### In-App Commands

| Command                     | Description                      |
| --------------------------- | -------------------------------- |
| \`/help\`                   | Comprehensive help with examples |
| \`/clear\`                  | Clear chat history               |
| \`/keys\`                   | Configure API keys (improved!)   |
| \`/models\`                 | Show available models            |
| \`/status\`                 | Current configuration            |
| \`/provider `<name>`\`    | Switch AI provider               |
| \`/model `<name>`\`       | Switch model                     |
| \`/setkey `<p>` `<k>`\` | Set API key for provider         |
| \`/backtest\`               | Show backtesting strategies      |

### Keyboard Shortcuts

| Shortcut   | Action                  |
| ---------- | ----------------------- |
| \`Tab\`    | Autocomplete suggestion |
| \`Ctrl+L\` | Clear chat              |
| \`Ctrl+M\` | Show models             |
| \`Ctrl+H\` | Toggle quick help       |
| \`Esc\`    | Cancel operation        |

---

## Configuration

### Config Location

\`\`\`
~/.sigma/
|-- config.env           # API keys and settings
└── .first_run_complete  # First-run marker
\`\`\`

### Error Codes

| Code Range | Category | Example                 |
| ---------- | -------- | ----------------------- |
| E1000-1099 | General  | E1002: Timeout          |
| E1100-1199 | API Keys | E1101: Invalid API key  |
| E1200-1299 | Provider | E1202: Model not found  |
| E1300-1399 | Data     | E1300: Symbol not found |
| E1400-1499 | Network  | E1400: Connection error |

---

## Changelog

### v3.4.0 (Current)

- [X] **Improved API Key Management** — Beautiful \`/keys\` interface with URLs
- [X] **Polygon.io Integration** — Real-time quotes, aggregates, news
- [X] **xAI Grok Support** — Full support for Grok-2 and Grok-2-mini
- [X] **Error Codes** — Structured error codes (E1000-E1499)
- [X] **Updated Models** — Removed deprecated, added latest versions
- [X] **Enhanced AI** — Maximum helpfulness with proactive insights
- [X] **Modern UI** — Gradient blues, improved styling
- [X] **Cross-Platform** — Works on macOS, Linux, Windows

### v3.3.x

- [X] Auto-setup on first launch
- [X] LEAN auto-detection
- [X] API rate limiting
- [X] Ollama native tool calls
- [X] Alpha Vantage & Exa integration

---

## Acknowledgments

Built with [Textual](https://textual.textualize.io/), [Rich](https://rich.readthedocs.io/), [yfinance](https://github.com/ranaroussi/yfinance), [Plotly](https://plotly.com/python/), LEAN

AI: [Google Gemini](https://ai.google.dev/) • [OpenAI](https://openai.com/) • [Anthropic](https://anthropic.com/) • [Groq](https://groq.com/) • [xAI](https://x.ai/) • [Ollama](https://ollama.ai/)

Data: [Polygon.io](https://polygon.io/) • [Alpha Vantage](https://www.alphavantage.co/) • [Exa](https://exa.ai/)

---

<p align="center">
  <code>σ</code> — Finance Research AI Agent
</p>
