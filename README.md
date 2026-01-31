# Sigma

<div align="center">

```
   _____ _                   
  / ___/(_)___ _____ ___  ____ _ 
  \__ \/ / __ `/ __ `__ \/ __ `/ 
 ___/ / / /_/ / / / / / / /_/ /  
/____/_/\__, /_/ /_/ /_/\__,_/   
       /____/                
```

**Finance Research Agent**

Native macOS | Multi-Provider AI | Real-Time Data

---

[Installation](#installation) | [Usage](#usage) | [Commands](#commands) | [Configuration
](#configuration)

---

## Overview

Sigma is an AI-powered Finance Research Agent that runs natively on macOS. Ask questions in natural language, get comprehensive market analysis, charts, and backtests in seconds.

---

## Installation

## Via Brew

```bash
brew tap desenyon/sigma
brew install sigma
# or if you want app (experimental)
brew install --cask sigma
```

### Via pip

```bash
pip install sigma-terminal
sigma --setup
```

### From source

```bash
git clone https://github.com/desenyon/sigma.git
cd sigma
pip install -e .
sigma --setup
```

---

## Usage

### Interactive Mode

```bash
sigma
```

Launch the full terminal interface with:

- Natural language queries with autocomplete
- Real-time market data
- Interactive charts and analysis
- Conversation history

### CLI Mode

```bash
sigma ask "analyze AAPL technicals"
sigma quote AAPL MSFT GOOGL
sigma compare NVDA AMD INTC
sigma backtest TSLA --strategy macd_momentum
sigma chart SPY --period 1y
```

---

## Commands

| Command                     | Description             |
| --------------------------- | ----------------------- |
| `sigma`                   | Launch interactive mode |
| `sigma ask "<query>"`     | Ask a question          |
| `sigma quote <symbols>`   | Get stock quotes        |
| `sigma compare <symbols>` | Compare multiple stocks |
| `sigma backtest <symbol>` | Run a backtest          |
| `sigma chart <symbol>`    | Generate a chart        |
| `sigma --setup`           | Run setup wizard        |
| `sigma --status`          | Show configuration      |
| `sigma --list-models`     | List available models   |

### Interactive Commands

| Command              | Description              |
| -------------------- | ------------------------ |
| `/help`            | Show available commands  |
| `/clear`           | Clear chat history       |
| `/keys`            | Configure API keys       |
| `/models`          | Show available models    |
| `/provider <name>` | Switch AI provider       |
| `/backtest`        | Show backtest strategies |
| `/status`          | Show configuration       |
| `/export`          | Export conversation      |

---

## Features

### AI Providers

| Provider      | Models                                | Notes               |
| ------------- | ------------------------------------- | ------------------- |
| Google Gemini | gemini-2.0-flash, 1.5-pro             | Free tier available |
| OpenAI        | gpt-4o, gpt-4o-mini                   | Best reasoning      |
| Anthropic     | Claude claude-sonnet-4-20250514, Opus | Deep analysis       |
| Groq          | Llama 3.3 70B                         | Ultra-fast          |
| xAI           | Grok 2                                | Real-time knowledge |
| Ollama        | Llama, Mistral, Phi                   | Local, private      |

### Market Data

- Real-time quotes and price data
- Historical OHLCV with adjustments
- Technical indicators (RSI, MACD, Bollinger, MAs)
- Fundamental data and financials
- Analyst recommendations
- Insider and fund activity

### Analysis

- Performance metrics (Sharpe, Sortino, Calmar)
- Risk analysis (VaR, drawdowns, volatility)
- Sector and market overview
- Multi-asset comparison
- Regime detection
- Seasonality patterns

### Backtesting

| Strategy               | Description                  |
| ---------------------- | ---------------------------- |
| `sma_crossover`      | SMA 20/50 crossover          |
| `rsi_mean_reversion` | RSI oversold/overbought      |
| `macd_momentum`      | MACD signal crossover        |
| `bollinger_bands`    | Bollinger band bounce        |
| `dual_momentum`      | Absolute + relative momentum |
| `breakout`           | Price breakout system        |

### Visualization

- Candlestick charts with volume
- Technical overlays
- Performance curves
- Comparison charts

---

## Configuration

Configuration is stored in `~/.sigma/`.

### Environment Variables

```bash
export GOOGLE_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"
```

### Config File

Create `~/.sigma/config.env`:

```
DEFAULT_PROVIDER=google
DEFAULT_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=your-key
```

---

## Keyboard Shortcuts

| Shortcut    | Action             |
| ----------- | ------------------ |
| `Ctrl+L`  | Clear screen       |
| `Ctrl+K`  | Configure API keys |
| `Ctrl+M`  | Show models        |
| `Ctrl+C`  | Exit               |
| `Tab`     | Autocomplete       |
| `Up/Down` | History navigation |

---

## Examples

```bash
# Get a quick stock overview
sigma ask "give me a summary of AAPL"

# Technical analysis
sigma ask "what do the technicals say about NVDA?"

# Compare stocks
sigma ask "compare AAPL MSFT GOOGL performance this year"

# Backtest a strategy
sigma ask "backtest SMA crossover on SPY for 2 years"

# Market overview
sigma ask "how are the markets doing today?"

# Sector analysis
sigma ask "which sectors are performing best?"
```

---

## License

Proprietary - See [LICENSE](LICENSE)

---

<div align="center">

**Sigma v3.2.0 - Finance Research Agent**

</div>
