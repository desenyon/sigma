<h1 align="center">
  <code>σ</code> SIGMA
</h1>

<p align="center">
  <strong>The Terminal-Based Financial Research Agent</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-3.5.0-blue.svg" alt="Version 3.5.0"/>
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python 3.11+"/>
  <img src="https://img.shields.io/badge/license-Proprietary-red.svg" alt="License"/>
  <img src="https://img.shields.io/badge/UI-Textual-purple.svg" alt="UI Framework"/>
</p>

---

## What is Sigma?

Sigma is a financial analysis terminal powered by modern AI. It unifies natural language research, quantitative backtesting, and real-time market data into a single, high-performance CLI application.

Unlike generic chat tools, Sigma is built for finance:

- **Deterministic Tools**: Real APIs for quotes, financials, and news—no hallucinations.
- **Local & Cloud AI**: Route queries to OpenAI, Anthropic, Gemini, or run locally with Ollama.
- **Integrated Backtesting**: First-class support for LEAN engine to test strategies instantly.
- **Privacy First**: Your API keys and strategies stay on your machine.

---

## Installation

### Prerequisites

- Python 3.11+
- [Optional] Docker (for LEAN) or LEAN CLI
- [Optional] Ollama (for local inference)

### One-Command Setup

Sigma includes an intelligent **Setup Agent** that handles the heavy lifting.

```bash
# Clone and install
pip install sigma-terminal

# Launch (triggers Setup Agent on first run)
python -m sigma
```

The Setup Agent will:

1. Detect your OS and Python environment.
2. Install the LEAN backtesting engine (if missing).
3. Install and configure Ollama (if missing).
4. help you add API keys for data providers (Polygon, Alpha Vantage, etc.).

---

## Usage

Sigma is designed for natural language. Just type what you need.

### Market Research

> "Analyze AAPL and compare it with MSFT for the last 5 years"
> "Get me the latest earnings report for NVDA and summarize risks"
> "Show me a chart of SPY vs QQQ YTD"

### Quantitative Backtesting

> "Backtest a simple moving average crossover on BTC-USD from 2020"
> "Run a momentum strategy on TSLA, weekly rebalance"

### Tool & System Control

> "Switch model to local llama3"
> "List all available tools"
> "/backtest AAPL -s sma_cross" (Shortcuts available)

---

## Architecture

Sigma v3.5.0 is built on a modular, event-driven architecture:

| Component                  | Description                                                                                           |
| -------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Core Engine**      | Orchestrates intent parsing, tool routing, and result synthesis.                                      |
| **LLM Router**       | Intelligent routing between OpenAI, Anthropic, Google, and Ollama. Handles rate limits and fallbacks. |
| **Tool Registry**    | A typed system connecting the LLM to 30+ financial data functions.                                    |
| **Backtest Service** | Wraps the LEAN engine to stream logs and results directly to the TUI.                                 |
| **UI (Textual)**     | A multi-pane terminal interface with real-time streaming, trace logs, and plotting.                   |

---

## Configuration

Configuration is stored in `~/.sigma/` and managed automatically. You can also edit it manually:

`~/.sigma/config.json`:

```json
{
  "default_model": "gpt-4o",
  "ollama_url": "http://localhost:11434",
  "data_providers": {
    "polygon": "ENABLED",
    "yfinance": "FALLBACK"
  }
}
```

### Supported Providers

- **AI**: OpenAI, Anthropic (Claude), Google (Gemini), Ollama (Local)
- **Data**: Polygon.io, Alpha Vantage, Financial Modeling Prep, YFinance (Default)

---

## License

Proprietary / Closed Source.
Copyright (c) 2026 Sigma Team. All Rights Reserved.
