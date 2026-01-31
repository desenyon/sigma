# σ Sigma

**Financial Research Agent**

Sigma is an autonomous AI-powered financial research agent that provides institutional-grade market analysis. It combines multiple LLM providers with real-time market data to deliver comprehensive stock analysis, portfolio insights, and actionable investment research.

## Features

- **Real-Time Market Data** via yfinance

  - Stock quotes, historical prices, financial statements
  - Analyst recommendations, insider trading, institutional holdings
  - Options chains, dividends, earnings calendars
  - Sector performance, market indices, market movers
- **18+ Financial Tools**

  - `get_stock_quote` - Real-time price and key metrics
  - `get_company_info` - Business description, financials
  - `get_financial_statements` - Income, balance sheet, cash flow
  - `get_analyst_recommendations` - Ratings and price targets
  - `get_insider_trades` - Recent insider activity
  - `get_institutional_holders` - Top institutional owners
  - `get_options_chain` - Calls and puts data
  - `get_dividends` - Dividend history and yield
  - `technical_analysis` - RSI, MACD, moving averages
  - `compare_stocks` - Multi-stock comparison
  - `get_market_movers` - Top gainers/losers
  - `get_sector_performance` - Sector ETF performance
  - And more...
- **Multiple LLM Providers**

  - OpenAI (GPT-4o)
  - Anthropic (Claude)
  - Google (Gemini)
  - Groq (Llama)
  - xAI (Grok)
  - Ollama (local models)
- **Clean Terminal UI**

  - Minimal, Claude Code-inspired interface
  - Real-time tool execution display
  - Markdown-formatted responses with tables

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/sigma.git
cd sigma

# Install dependencies
pip install -e .

# Set up your API keys
cp .env.example .env
# Edit .env with your API keys
```

## Configuration

Create a `.env` file with your API keys:

```bash
# LLM Providers (at least one required)
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
GROQ_API_KEY=your-groq-api-key
XAI_API_KEY=your-xai-api-key

# Optional: Financial data APIs (for additional data sources)
FMP_API_KEY=your-fmp-api-key
POLYGON_API_KEY=your-polygon-api-key
```

## Usage

### Interactive Mode

```bash
sigma
```

```
  σ Sigma Financial Research Agent

  Provider: google │ Model: gemini-2.0-flash
  Type /help for commands, /quit to exit

  > Analyze NVDA stock

  → get_stock_quote(NVDA) ✓ 245ms
  → get_company_info(NVDA) ✓ 312ms
  → get_analyst_recommendations(NVDA) ✓ 187ms
  → technical_analysis(NVDA) ✓ 423ms

  Called 4 tools in 1.2s

  ## NVIDIA (NVDA) Analysis

  **Current Price:** $191.13
  **Market Cap:** $4.67T
  ...
```

### Commands

- `/provider <name>` - Switch LLM provider (openai, anthropic, google, groq, ollama)
- `/model <name>` - Set model name
- `/clear` - Clear conversation history
- `/status` - Show current configuration
- `/help` - Show help
- `/quit` - Exit

### Example Queries

```
> What is the current price of AAPL?
> Compare MSFT, GOOGL, and AMZN on valuation metrics
> Give me a comprehensive analysis of Tesla
> What are the top market gainers today?
> Technical analysis on SPY
> Show me insider trades for NVDA
> What's the options chain for AAPL?
```

## Python API

```python
import asyncio
from sigma import SigmaAgent, LLMProvider

async def main():
    # Create agent
    agent = SigmaAgent(provider=LLMProvider.GOOGLE)
  
    # Run analysis
    result = await agent.run("Analyze AAPL stock")
    print(result)
  
    # Get execution stats
    stats = agent.get_stats()
    print(f"Tools called: {stats['tools_called']}")

asyncio.run(main())
```

## Architecture

```
sigma/
├── core/
│   ├── agent.py      # Main agent logic
│   ├── config.py     # Configuration management
│   ├── llm.py        # LLM provider implementations
│   └── models.py     # Data models
├── tools/
│   └── financial.py  # Financial data tools (yfinance)
├── ui/
│   └── __init__.py   # UI components
└── app.py            # CLI application
```

## Requirements

- Python 3.10+
- httpx
- pydantic
- pydantic-settings
- rich
- yfinance
- pandas
- numpy

## License

Check File

---

*Sigma - Institutional-grade financial research at your fingertips.*
