"""Financial tools for real market data."""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Optional, Union
import time

import httpx
import pandas as pd


# Tool registry
_tools: dict[str, dict[str, Any]] = {}


def tool(name: str, description: str, parameters: dict[str, Any]):
    """Register a tool."""
    def decorator(func):
        _tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "function": func,
        }
        return func
    return decorator


def get_all_tools() -> list[dict[str, Any]]:
    """Get all tool definitions."""
    return [
        {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}
        for t in _tools.values()
    ]


async def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Execute a tool."""
    if name not in _tools:
        return {"error": f"Tool not found: {name}"}
    
    try:
        func = _tools[name]["function"]
        if asyncio.iscoroutinefunction(func):
            return await func(**arguments)
        return func(**arguments)
    except Exception as e:
        return {"error": str(e)}


def _format_date(val: Any) -> str:
    """Safely format a date value to string."""
    if hasattr(val, 'strftime'):
        return val.strftime("%Y-%m-%d")
    elif isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%d")
    return str(val)


def _is_dataframe(obj: Any) -> bool:
    """Check if object is a DataFrame."""
    return isinstance(obj, pd.DataFrame)


# ============================================================================
# MARKET DATA TOOLS (yfinance)
# ============================================================================

@tool(
    name="get_stock_quote",
    description="Get real-time stock quote with price, volume, market cap, P/E ratio, and other key metrics",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol (e.g., AAPL, GOOGL)"}
        },
        "required": ["symbol"]
    }
)
def get_stock_quote(symbol: str) -> dict[str, Any]:
    """Get stock quote using yfinance."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    info = ticker.info
    
    if not info or "regularMarketPrice" not in info:
        # Try fast_info
        try:
            fast = ticker.fast_info
            return {
                "symbol": symbol.upper(),
                "price": fast.get("lastPrice", fast.get("regularMarketPrice")),
                "previous_close": fast.get("previousClose"),
                "market_cap": fast.get("marketCap"),
                "error": None
            }
        except:
            return {"error": f"Could not fetch quote for {symbol}"}
    
    return {
        "symbol": symbol.upper(),
        "name": info.get("shortName", info.get("longName", "")),
        "price": info.get("regularMarketPrice", info.get("currentPrice")),
        "previous_close": info.get("previousClose"),
        "open": info.get("regularMarketOpen"),
        "day_high": info.get("regularMarketDayHigh"),
        "day_low": info.get("regularMarketDayLow"),
        "volume": info.get("regularMarketVolume"),
        "avg_volume": info.get("averageVolume"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "eps": info.get("trailingEps"),
        "dividend_yield": info.get("dividendYield"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow"),
        "50_day_avg": info.get("fiftyDayAverage"),
        "200_day_avg": info.get("twoHundredDayAverage"),
        "beta": info.get("beta"),
        "currency": info.get("currency", "USD"),
    }


@tool(
    name="get_stock_history",
    description="Get historical price data for a stock",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "period": {"type": "string", "description": "Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max", "default": "1mo"},
            "interval": {"type": "string", "description": "Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo", "default": "1d"}
        },
        "required": ["symbol"]
    }
)
def get_stock_history(symbol: str, period: str = "1mo", interval: str = "1d") -> dict[str, Any]:
    """Get historical stock data."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    hist = ticker.history(period=period, interval=interval)
    
    if hist.empty:
        return {"error": f"No history for {symbol}"}
    
    records = []
    for date, row in hist.iterrows():
        records.append({
            "date": _format_date(date),
            "open": round(row["Open"], 2) if row["Open"] else None,
            "high": round(row["High"], 2) if row["High"] else None,
            "low": round(row["Low"], 2) if row["Low"] else None,
            "close": round(row["Close"], 2) if row["Close"] else None,
            "volume": int(row["Volume"]) if row["Volume"] else None,
        })
    
    # Calculate returns
    if len(records) > 1:
        start_price = records[0]["close"]
        end_price = records[-1]["close"]
        if start_price and end_price:
            total_return = ((end_price - start_price) / start_price) * 100
        else:
            total_return = None
    else:
        total_return = None
    
    return {
        "symbol": symbol.upper(),
        "period": period,
        "interval": interval,
        "data_points": len(records),
        "start_date": records[0]["date"] if records else None,
        "end_date": records[-1]["date"] if records else None,
        "total_return_pct": round(total_return, 2) if total_return else None,
        "history": records[-20:],  # Last 20 for brevity
    }


@tool(
    name="get_company_info",
    description="Get detailed company information including business description, sector, industry, and key statistics",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        },
        "required": ["symbol"]
    }
)
def get_company_info(symbol: str) -> dict[str, Any]:
    """Get company information."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    info = ticker.info
    
    if not info:
        return {"error": f"Could not fetch info for {symbol}"}
    
    return {
        "symbol": symbol.upper(),
        "name": info.get("shortName", info.get("longName", "")),
        "description": info.get("longBusinessSummary", ""),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "website": info.get("website"),
        "country": info.get("country"),
        "employees": info.get("fullTimeEmployees"),
        "market_cap": info.get("marketCap"),
        "enterprise_value": info.get("enterpriseValue"),
        "revenue": info.get("totalRevenue"),
        "gross_profit": info.get("grossProfits"),
        "ebitda": info.get("ebitda"),
        "net_income": info.get("netIncomeToCommon"),
        "profit_margin": info.get("profitMargins"),
        "operating_margin": info.get("operatingMargins"),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        "debt_to_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "quick_ratio": info.get("quickRatio"),
        "free_cash_flow": info.get("freeCashflow"),
    }


@tool(
    name="get_financial_statements",
    description="Get income statement, balance sheet, and cash flow statement data",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "statement": {"type": "string", "description": "Statement type: income, balance, cashflow", "default": "income"},
            "period": {"type": "string", "description": "Period: annual or quarterly", "default": "annual"}
        },
        "required": ["symbol"]
    }
)
def get_financial_statements(symbol: str, statement: str = "income", period: str = "annual") -> dict[str, Any]:
    """Get financial statements."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    
    if statement == "income":
        df = ticker.income_stmt if period == "annual" else ticker.quarterly_income_stmt
    elif statement == "balance":
        df = ticker.balance_sheet if period == "annual" else ticker.quarterly_balance_sheet
    elif statement == "cashflow":
        df = ticker.cashflow if period == "annual" else ticker.quarterly_cashflow
    else:
        return {"error": f"Invalid statement type: {statement}"}
    
    if df is None or df.empty:
        return {"error": f"No {statement} statement for {symbol}"}
    
    # Convert to dict
    data = {}
    for col in df.columns[:4]:  # Last 4 periods
        period_key = _format_date(col)
        data[period_key] = {}
        for idx, val in df[col].items():
            if val is not None and not (isinstance(val, float) and val != val):  # Check for NaN
                data[period_key][str(idx)] = float(val) if isinstance(val, (int, float)) else val
    
    return {
        "symbol": symbol.upper(),
        "statement_type": statement,
        "period": period,
        "data": data,
    }


@tool(
    name="get_analyst_recommendations",
    description="Get analyst recommendations and price targets",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        },
        "required": ["symbol"]
    }
)
def get_analyst_recommendations(symbol: str) -> dict[str, Any]:
    """Get analyst recommendations."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    
    # Get recommendations
    recs = ticker.recommendations
    info = ticker.info
    
    result: dict[str, Any] = {
        "symbol": symbol.upper(),
        "recommendation": info.get("recommendationKey"),
        "mean_rating": info.get("recommendationMean"),
        "num_analysts": info.get("numberOfAnalystOpinions"),
        "target_high": info.get("targetHighPrice"),
        "target_low": info.get("targetLowPrice"),
        "target_mean": info.get("targetMeanPrice"),
        "target_median": info.get("targetMedianPrice"),
        "current_price": info.get("regularMarketPrice"),
    }
    
    # Add upside/downside
    if result.get("target_mean") and result.get("current_price"):
        upside = ((result["target_mean"] - result["current_price"]) / result["current_price"]) * 100
        result["upside_pct"] = round(upside, 2)
    
    # Recent recommendations
    if recs is not None and _is_dataframe(recs):
        recs_df: pd.DataFrame = recs  # type: ignore
        if not recs_df.empty:
            recent = recs_df.tail(10).to_dict("records")
            result["recent_recommendations"] = recent
    
    return result


@tool(
    name="get_insider_trades",
    description="Get recent insider trading activity",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        },
        "required": ["symbol"]
    }
)
def get_insider_trades(symbol: str) -> dict[str, Any]:
    """Get insider trades."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    insiders = ticker.insider_transactions
    
    if insiders is None or insiders.empty:
        return {"symbol": symbol.upper(), "trades": [], "message": "No insider trades found"}
    
    trades = []
    for _, row in insiders.head(20).iterrows():
        trade = {}
        for col in insiders.columns:
            val = row[col]
            if hasattr(val, 'strftime'):
                trade[col] = val.strftime("%Y-%m-%d")
            elif val is None or (isinstance(val, float) and val != val):
                trade[col] = None
            else:
                trade[col] = val
        trades.append(trade)
    
    return {
        "symbol": symbol.upper(),
        "total_trades": len(insiders),
        "trades": trades,
    }


@tool(
    name="get_institutional_holders",
    description="Get institutional ownership data",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        },
        "required": ["symbol"]
    }
)
def get_institutional_holders(symbol: str) -> dict[str, Any]:
    """Get institutional holders."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    holders = ticker.institutional_holders
    
    if holders is None or holders.empty:
        return {"symbol": symbol.upper(), "holders": [], "message": "No institutional holders found"}
    
    holder_list = []
    for _, row in holders.iterrows():
        holder = {}
        for col in holders.columns:
            val = row[col]
            if hasattr(val, 'strftime'):
                holder[col] = val.strftime("%Y-%m-%d")
            elif val is None or (isinstance(val, float) and val != val):
                holder[col] = None
            else:
                holder[col] = val
        holder_list.append(holder)
    
    return {
        "symbol": symbol.upper(),
        "holders": holder_list,
    }


@tool(
    name="get_earnings_calendar",
    description="Get earnings history and upcoming earnings dates",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        },
        "required": ["symbol"]
    }
)
def get_earnings_calendar(symbol: str) -> dict[str, Any]:
    """Get earnings data."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    earnings = ticker.earnings_history
    calendar = ticker.calendar
    
    result: dict[str, Any] = {"symbol": symbol.upper()}
    
    if earnings is not None and _is_dataframe(earnings) and not earnings.empty:
        history = []
        for _, row in earnings.iterrows():
            entry = {}
            for col in earnings.columns:
                val = row[col]
                if hasattr(val, 'strftime'):
                    entry[col] = _format_date(val)
                elif val is None or (isinstance(val, float) and val != val):
                    entry[col] = None
                else:
                    entry[col] = val
            history.append(entry)
        result["earnings_history"] = history
    
    if calendar is not None:
        try:
            if isinstance(calendar, dict):
                result["calendar"] = calendar
            elif hasattr(calendar, 'to_dict'):
                # DataFrame calendar
                raw_dict = dict(calendar.to_dict())  # type: ignore[union-attr]
                result["calendar"] = {str(k): str(v) if v is not None else None for k, v in raw_dict.items()}
            else:
                result["calendar"] = str(calendar)
        except Exception:
            result["calendar"] = str(calendar)
    
    return result


@tool(
    name="get_options_chain",
    description="Get options chain data including calls and puts",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "expiration": {"type": "string", "description": "Expiration date (YYYY-MM-DD) or 'next' for nearest expiration"}
        },
        "required": ["symbol"]
    }
)
def get_options_chain(symbol: str, expiration: Optional[str] = None) -> dict[str, Any]:
    """Get options chain."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    expirations = ticker.options
    
    if not expirations:
        return {"error": f"No options available for {symbol}"}
    
    # Use first expiration if not specified
    exp_date = expiration if expiration and expiration != "next" else expirations[0]
    
    if exp_date not in expirations:
        return {"error": f"Invalid expiration. Available: {expirations[:5]}"}
    
    chain = ticker.option_chain(exp_date)
    
    def process_options(df, limit=10):
        options = []
        for _, row in df.head(limit).iterrows():
            opt = {}
            for col in df.columns:
                val = row[col]
                if val is None or (isinstance(val, float) and val != val):
                    opt[col] = None
                elif isinstance(val, (int, float)):
                    opt[col] = round(float(val), 4)
                else:
                    opt[col] = val
            options.append(opt)
        return options
    
    return {
        "symbol": symbol.upper(),
        "expiration": exp_date,
        "available_expirations": list(expirations[:10]),
        "calls": process_options(chain.calls),
        "puts": process_options(chain.puts),
    }


@tool(
    name="get_dividends",
    description="Get dividend history and yield information",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        },
        "required": ["symbol"]
    }
)
def get_dividends(symbol: str) -> dict[str, Any]:
    """Get dividend data."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    dividends = ticker.dividends
    info = ticker.info
    
    result: dict[str, Any] = {
        "symbol": symbol.upper(),
        "dividend_yield": info.get("dividendYield"),
        "dividend_rate": info.get("dividendRate"),
        "payout_ratio": info.get("payoutRatio"),
        "ex_dividend_date": info.get("exDividendDate"),
    }
    
    if dividends is not None and not dividends.empty:
        history = []
        for date, amount in dividends.tail(20).items():
            history.append({
                "date": _format_date(date),
                "amount": round(amount, 4)
            })
        result["history"] = history
        result["total_dividends_1y"] = round(dividends.tail(4).sum(), 4)
    
    return result


@tool(
    name="compare_stocks",
    description="Compare multiple stocks on key metrics",
    parameters={
        "type": "object",
        "properties": {
            "symbols": {"type": "array", "items": {"type": "string"}, "description": "List of stock symbols to compare"}
        },
        "required": ["symbols"]
    }
)
def compare_stocks(symbols: list[str]) -> dict[str, Any]:
    """Compare multiple stocks."""
    import yfinance as yf
    
    comparisons = []
    for symbol in symbols[:10]:  # Limit to 10
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        if info:
            comparisons.append({
                "symbol": symbol.upper(),
                "name": info.get("shortName"),
                "price": info.get("regularMarketPrice"),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "ps_ratio": info.get("priceToSalesTrailing12Months"),
                "pb_ratio": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "profit_margin": info.get("profitMargins"),
                "roe": info.get("returnOnEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "52w_change": info.get("52WeekChange"),
            })
    
    return {
        "comparison": comparisons,
        "symbols_compared": len(comparisons),
    }


@tool(
    name="get_market_movers",
    description="Get top market gainers and losers",
    parameters={
        "type": "object",
        "properties": {
            "category": {"type": "string", "description": "Category: gainers, losers, or active", "default": "gainers"}
        },
        "required": []
    }
)
async def get_market_movers(category: str = "gainers") -> dict[str, Any]:
    """Get market movers."""
    import yfinance as yf
    
    # Major indices and popular stocks to check
    symbols = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
        "JPM", "JNJ", "V", "UNH", "HD", "PG", "MA", "DIS", "PYPL", "NFLX",
        "ADBE", "CRM", "INTC", "AMD", "CSCO", "PFE", "MRK", "ABT", "TMO",
        "NKE", "COST", "WMT", "XOM", "CVX", "BA", "CAT", "GS", "MS"
    ]
    
    movers = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if info and info.get("regularMarketPrice") and info.get("previousClose"):
                price = info["regularMarketPrice"]
                prev = info["previousClose"]
                change = price - prev
                change_pct = (change / prev) * 100
                movers.append({
                    "symbol": symbol,
                    "name": info.get("shortName"),
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": info.get("regularMarketVolume"),
                })
        except:
            continue
    
    if category == "gainers":
        movers.sort(key=lambda x: x["change_pct"], reverse=True)
    elif category == "losers":
        movers.sort(key=lambda x: x["change_pct"])
    else:  # active
        movers.sort(key=lambda x: x.get("volume", 0) or 0, reverse=True)
    
    return {
        "category": category,
        "movers": movers[:15],
    }


@tool(
    name="get_sector_performance",
    description="Get sector ETF performance",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_sector_performance() -> dict[str, Any]:
    """Get sector performance via ETFs."""
    import yfinance as yf
    
    sectors = {
        "XLK": "Technology",
        "XLF": "Financials",
        "XLV": "Healthcare",
        "XLE": "Energy",
        "XLI": "Industrials",
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLU": "Utilities",
        "XLB": "Materials",
        "XLRE": "Real Estate",
        "XLC": "Communication Services",
    }
    
    performance = []
    for symbol, name in sectors.items():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if info and info.get("regularMarketPrice") and info.get("previousClose"):
                price = info["regularMarketPrice"]
                prev = info["previousClose"]
                change_pct = ((price - prev) / prev) * 100
                performance.append({
                    "sector": name,
                    "etf": symbol,
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                    "52w_change": info.get("52WeekChange"),
                })
        except:
            continue
    
    performance.sort(key=lambda x: x["change_pct"], reverse=True)
    
    return {
        "sectors": performance,
        "best_sector": performance[0]["sector"] if performance else None,
        "worst_sector": performance[-1]["sector"] if performance else None,
    }


@tool(
    name="get_market_indices",
    description="Get major market indices",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def get_market_indices() -> dict[str, Any]:
    """Get market indices."""
    import yfinance as yf
    
    indices = {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ",
        "^RUT": "Russell 2000",
        "^VIX": "VIX",
        "^TNX": "10Y Treasury",
        "GC=F": "Gold",
        "CL=F": "Crude Oil",
        "BTC-USD": "Bitcoin",
    }
    
    data = []
    for symbol, name in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if info:
                price = info.get("regularMarketPrice", info.get("previousClose"))
                prev = info.get("previousClose")
                if price and prev:
                    change_pct = ((price - prev) / prev) * 100
                else:
                    change_pct = None
                data.append({
                    "name": name,
                    "symbol": symbol,
                    "price": round(price, 2) if price else None,
                    "change_pct": round(change_pct, 2) if change_pct else None,
                })
        except:
            continue
    
    return {"indices": data}


@tool(
    name="calculate_portfolio_metrics",
    description="Calculate portfolio metrics given holdings",
    parameters={
        "type": "object",
        "properties": {
            "holdings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "shares": {"type": "number"},
                        "cost_basis": {"type": "number"}
                    }
                },
                "description": "List of holdings with symbol, shares, and cost basis"
            }
        },
        "required": ["holdings"]
    }
)
def calculate_portfolio_metrics(holdings: list[dict]) -> dict[str, Any]:
    """Calculate portfolio metrics."""
    import yfinance as yf
    
    results = []
    total_value = 0
    total_cost = 0
    
    for holding in holdings:
        symbol = holding["symbol"]
        shares = holding["shares"]
        cost_basis = holding.get("cost_basis", 0)
        
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        if info and info.get("regularMarketPrice"):
            price = info["regularMarketPrice"]
            value = price * shares
            cost = cost_basis * shares if cost_basis else 0
            gain = value - cost if cost else None
            gain_pct = ((value - cost) / cost * 100) if cost else None
            
            results.append({
                "symbol": symbol.upper(),
                "shares": shares,
                "price": round(price, 2),
                "value": round(value, 2),
                "cost_basis": cost_basis,
                "total_cost": round(cost, 2),
                "gain": round(gain, 2) if gain else None,
                "gain_pct": round(gain_pct, 2) if gain_pct else None,
            })
            
            total_value += value
            total_cost += cost
    
    total_gain = total_value - total_cost if total_cost else None
    total_gain_pct = ((total_value - total_cost) / total_cost * 100) if total_cost else None
    
    # Calculate weights
    for r in results:
        r["weight_pct"] = round((r["value"] / total_value * 100), 2) if total_value else 0
    
    return {
        "holdings": results,
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_gain": round(total_gain, 2) if total_gain else None,
        "total_gain_pct": round(total_gain_pct, 2) if total_gain_pct else None,
    }


@tool(
    name="search_stocks",
    description="Search for stocks by company name or symbol",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query (company name or symbol)"}
        },
        "required": ["query"]
    }
)
async def search_stocks(query: str) -> dict[str, Any]:
    """Search for stocks."""
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10&newsCount=0"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        data = resp.json()
    
    results = []
    for quote in data.get("quotes", []):
        if quote.get("quoteType") == "EQUITY":
            results.append({
                "symbol": quote.get("symbol"),
                "name": quote.get("shortname") or quote.get("longname"),
                "exchange": quote.get("exchange"),
                "type": quote.get("typeDisp"),
            })
    
    return {"results": results, "query": query}


@tool(
    name="get_stock_news",
    description="Get recent news for a stock",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        },
        "required": ["symbol"]
    }
)
def get_stock_news(symbol: str) -> dict[str, Any]:
    """Get stock news."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    news = ticker.news
    
    if not news:
        return {"symbol": symbol.upper(), "news": [], "message": "No news found"}
    
    articles = []
    for item in news[:10]:
        articles.append({
            "title": item.get("title"),
            "publisher": item.get("publisher"),
            "link": item.get("link"),
            "published": datetime.fromtimestamp(item.get("providerPublishTime", 0)).isoformat() if item.get("providerPublishTime") else None,
            "type": item.get("type"),
        })
    
    return {
        "symbol": symbol.upper(),
        "news": articles,
    }


@tool(
    name="technical_analysis",
    description="Perform basic technical analysis on a stock",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        },
        "required": ["symbol"]
    }
)
def technical_analysis(symbol: str) -> dict[str, Any]:
    """Perform technical analysis."""
    import yfinance as yf
    import numpy as np
    
    ticker = yf.Ticker(symbol.upper())
    hist = ticker.history(period="6mo")
    
    if hist.empty:
        return {"error": f"No data for {symbol}"}
    
    close = hist["Close"]
    
    # Moving averages
    sma_20 = close.rolling(window=20).mean().iloc[-1]
    sma_50 = close.rolling(window=50).mean().iloc[-1]
    sma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None
    
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    
    # MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    
    current_price = close.iloc[-1]
    
    # Signals
    signals = []
    if current_price > sma_20:
        signals.append("Above SMA20 (bullish)")
    else:
        signals.append("Below SMA20 (bearish)")
    
    if current_price > sma_50:
        signals.append("Above SMA50 (bullish)")
    else:
        signals.append("Below SMA50 (bearish)")
    
    if rsi > 70:
        signals.append("RSI > 70 (overbought)")
    elif rsi < 30:
        signals.append("RSI < 30 (oversold)")
    else:
        signals.append(f"RSI neutral ({round(rsi, 1)})")
    
    if macd.iloc[-1] > signal.iloc[-1]:
        signals.append("MACD above signal (bullish)")
    else:
        signals.append("MACD below signal (bearish)")
    
    return {
        "symbol": symbol.upper(),
        "price": round(current_price, 2),
        "sma_20": round(sma_20, 2),
        "sma_50": round(sma_50, 2),
        "sma_200": round(sma_200, 2) if sma_200 else None,
        "rsi": round(rsi, 2),
        "macd": round(macd.iloc[-1], 4),
        "macd_signal": round(signal.iloc[-1], 4),
        "signals": signals,
        "support": round(hist["Low"].tail(20).min(), 2),
        "resistance": round(hist["High"].tail(20).max(), 2),
    }


# ============================================================================
# CHART TOOLS
# ============================================================================

@tool(
    name="generate_price_chart",
    description="Generate a beautiful ASCII price chart in the terminal for a stock",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "period": {"type": "string", "description": "Time period: 1mo, 3mo, 6mo, 1y, 2y", "default": "3mo"},
            "chart_type": {"type": "string", "description": "Chart type: line, candle, bar, area", "default": "line"},
            "show_volume": {"type": "boolean", "description": "Show volume subplot", "default": True}
        },
        "required": ["symbol"]
    }
)
def generate_price_chart(symbol: str, period: str = "3mo", chart_type: str = "line", show_volume: bool = True) -> dict[str, Any]:
    """Generate a price chart."""
    from sigma.tools.charts import create_price_chart
    
    chart = create_price_chart(symbol, period, chart_type, show_volume)
    return {
        "symbol": symbol.upper(),
        "period": period,
        "chart_type": chart_type,
        "chart": chart,
        "display_as_chart": True,  # Flag for UI to render properly
    }


@tool(
    name="generate_comparison_chart",
    description="Generate a comparison chart for multiple stocks showing percentage change",
    parameters={
        "type": "object",
        "properties": {
            "symbols": {"type": "array", "items": {"type": "string"}, "description": "List of stock symbols to compare"},
            "period": {"type": "string", "description": "Time period", "default": "3mo"}
        },
        "required": ["symbols"]
    }
)
def generate_comparison_chart(symbols: list[str], period: str = "3mo") -> dict[str, Any]:
    """Generate a comparison chart."""
    from sigma.tools.charts import create_comparison_chart
    
    chart = create_comparison_chart(symbols, period)
    return {
        "symbols": [s.upper() for s in symbols],
        "period": period,
        "chart": chart,
        "display_as_chart": True,
    }


@tool(
    name="generate_rsi_chart",
    description="Generate a price chart with RSI indicator showing overbought/oversold levels",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "period": {"type": "string", "description": "Time period", "default": "3mo"}
        },
        "required": ["symbol"]
    }
)
def generate_rsi_chart(symbol: str, period: str = "3mo") -> dict[str, Any]:
    """Generate RSI chart."""
    from sigma.tools.charts import create_rsi_chart
    
    chart = create_rsi_chart(symbol, period)
    return {
        "symbol": symbol.upper(),
        "period": period,
        "chart": chart,
        "display_as_chart": True,
    }


@tool(
    name="generate_sector_chart",
    description="Generate a sector performance chart showing daily changes for all major sectors",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def generate_sector_chart() -> dict[str, Any]:
    """Generate sector chart."""
    from sigma.tools.charts import create_sector_chart
    
    chart = create_sector_chart()
    return {
        "chart": chart,
        "display_as_chart": True,
    }


# ============================================================================
# BACKTEST TOOLS
# ============================================================================

@tool(
    name="list_backtest_strategies",
    description="List all available backtesting strategies with descriptions",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_backtest_strategies() -> dict[str, Any]:
    """List available strategies."""
    from sigma.tools.backtest import get_available_strategies
    
    strategies = get_available_strategies()
    return {
        "strategies": strategies,
        "count": len(strategies),
    }


@tool(
    name="generate_backtest",
    description="Generate a LEAN engine compatible backtest algorithm for a trading strategy",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "strategy": {"type": "string", "description": "Strategy type: sma_crossover, rsi_mean_reversion, macd_momentum, bollinger_bands, dual_momentum, breakout"},
            "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)", "default": None},
            "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)", "default": None},
            "initial_capital": {"type": "number", "description": "Starting capital", "default": 100000},
            "params": {"type": "object", "description": "Strategy-specific parameters (optional)"}
        },
        "required": ["symbol", "strategy"]
    }
)
def generate_backtest(
    symbol: str,
    strategy: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    initial_capital: float = 100000,
    params: Optional[dict] = None,
) -> dict[str, Any]:
    """Generate a backtest algorithm."""
    from sigma.tools.backtest import generate_lean_algorithm
    
    result = generate_lean_algorithm(
        symbol=symbol,
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        params=params,
    )
    return result


@tool(
    name="generate_custom_backtest",
    description="Generate a custom backtest algorithm with user-specified entry/exit conditions",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "entry_conditions": {"type": "array", "items": {"type": "string"}, "description": "List of entry conditions (e.g., 'RSI below 30', 'Price above SMA 50')"},
            "exit_conditions": {"type": "array", "items": {"type": "string"}, "description": "List of exit conditions"},
            "indicators": {"type": "array", "items": {"type": "string"}, "description": "Indicators to use: sma, ema, rsi, macd, bb, atr, adx"},
            "initial_capital": {"type": "number", "description": "Starting capital", "default": 100000}
        },
        "required": ["symbol", "entry_conditions", "exit_conditions", "indicators"]
    }
)
def generate_custom_backtest(
    symbol: str,
    entry_conditions: list[str],
    exit_conditions: list[str],
    indicators: list[str],
    initial_capital: float = 100000,
) -> dict[str, Any]:
    """Generate custom backtest."""
    from sigma.tools.backtest import generate_custom_algorithm
    
    return generate_custom_algorithm(
        symbol=symbol,
        entry_conditions=entry_conditions,
        exit_conditions=exit_conditions,
        indicators=indicators,
        initial_capital=initial_capital,
    )


@tool(
    name="run_backtest",
    description="Run a full backtest using LEAN CLI. Installs LEAN if needed, generates algorithm, and runs backtest.",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "strategy": {
                "type": "string",
                "description": "Strategy: sma_crossover, rsi_mean_reversion, macd_momentum, bollinger_bands, dual_momentum, breakout",
                "default": "sma_crossover"
            },
            "initial_capital": {"type": "number", "description": "Starting capital", "default": 100000}
        },
        "required": ["symbol"]
    }
)
def run_backtest_tool(
    symbol: str,
    strategy: str = "sma_crossover",
    initial_capital: float = 100000,
) -> dict[str, Any]:
    """Run a full backtest with LEAN."""
    from sigma.tools.backtest import run_backtest
    
    return run_backtest(
        symbol=symbol,
        strategy=strategy,
        initial_capital=initial_capital,
    )


@tool(
    name="check_lean_status",
    description="Check if LEAN CLI is installed and provide setup instructions",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def check_lean_status_tool() -> dict[str, Any]:
    """Check LEAN installation status."""
    from sigma.tools.backtest import check_lean_status
    
    return check_lean_status()


# ============================================================================
# PREDICTION TOOLS
# ============================================================================

@tool(
    name="price_forecast",
    description="Generate price predictions using multiple technical models",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"},
            "horizon": {"type": "string", "description": "Forecast horizon: 1w, 1m, 3m, 6m", "default": "1m"}
        },
        "required": ["symbol"]
    }
)
def price_forecast(symbol: str, horizon: str = "1m") -> dict[str, Any]:
    """Generate price predictions."""
    import yfinance as yf
    import numpy as np
    
    ticker = yf.Ticker(symbol.upper())
    hist = ticker.history(period="1y")
    
    if hist.empty:
        return {"error": f"No data for {symbol}"}
    
    # Convert to numpy array explicitly
    close = np.array(hist["Close"].values, dtype=float)
    current_price = float(close[-1])
    
    # Map horizon to days
    horizon_days = {"1w": 5, "1m": 21, "3m": 63, "6m": 126}.get(horizon, 21)
    
    # Multiple prediction methods
    predictions = {}
    
    # 1. Simple Moving Average Projection
    sma_20 = float(np.mean(close[-20:]))
    sma_50 = float(np.mean(close[-50:])) if len(close) >= 50 else sma_20
    sma_trend = (sma_20 - sma_50) / sma_50 if sma_50 else 0
    sma_prediction = current_price * (1 + sma_trend * (horizon_days / 20))
    predictions["sma_trend"] = round(sma_prediction, 2)
    
    # 2. Linear Regression
    x = np.arange(len(close))
    coeffs = np.polyfit(x, close, 1)
    lr_prediction = float(coeffs[0]) * (len(close) + horizon_days) + float(coeffs[1])
    predictions["linear_regression"] = round(lr_prediction, 2)
    
    # 3. Volatility-adjusted (Monte Carlo simple)
    daily_returns = np.diff(close) / close[:-1]
    avg_return = float(np.mean(daily_returns))
    std_return = float(np.std(daily_returns))
    
    # Expected value with drift
    mc_prediction = current_price * (1 + avg_return * horizon_days)
    predictions["monte_carlo_expected"] = round(mc_prediction, 2)
    
    # Confidence interval (1 std)
    upper = current_price * np.exp((avg_return - 0.5 * std_return**2) * horizon_days + std_return * np.sqrt(horizon_days) * 1.96)
    lower = current_price * np.exp((avg_return - 0.5 * std_return**2) * horizon_days - std_return * np.sqrt(horizon_days) * 1.96)
    
    # 4. Mean reversion to SMA 200
    sma_200 = float(np.mean(close[-200:])) if len(close) >= 200 else sma_50
    mean_rev_prediction = current_price + (sma_200 - current_price) * 0.3  # 30% reversion
    predictions["mean_reversion"] = round(mean_rev_prediction, 2)
    
    # Consensus
    consensus = float(np.mean(list(predictions.values())))
    
    # Analyst targets for comparison
    info = ticker.info
    analyst_target = info.get("targetMeanPrice")
    
    return {
        "symbol": symbol.upper(),
        "current_price": round(current_price, 2),
        "horizon": horizon,
        "horizon_days": horizon_days,
        "predictions": predictions,
        "consensus_prediction": round(consensus, 2),
        "confidence_interval": {
            "lower_95": round(lower, 2),
            "upper_95": round(upper, 2),
        },
        "analyst_target": analyst_target,
        "volatility": {
            "daily": round(std_return * 100, 2),
            "annualized": round(std_return * np.sqrt(252) * 100, 2),
        },
        "disclaimer": "Predictions are based on historical patterns and should not be considered financial advice."
    }


@tool(
    name="sentiment_analysis",
    description="Analyze market sentiment for a stock based on various signals",
    parameters={
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Stock ticker symbol"}
        },
        "required": ["symbol"]
    }
)
def sentiment_analysis(symbol: str) -> dict[str, Any]:
    """Analyze sentiment from multiple sources."""
    import yfinance as yf
    
    ticker = yf.Ticker(symbol.upper())
    info = ticker.info
    hist = ticker.history(period="3mo")
    
    if hist.empty:
        return {"error": f"No data for {symbol}"}
    
    signals = []
    score = 0
    
    # 1. Analyst sentiment
    rec = info.get("recommendationKey", "").lower()
    if "strong buy" in rec or rec == "buy":
        signals.append(("Analyst Rating", rec.upper(), "bullish", 2))
        score += 2
    elif "hold" in rec:
        signals.append(("Analyst Rating", rec.upper(), "neutral", 0))
    elif "sell" in rec:
        signals.append(("Analyst Rating", rec.upper(), "bearish", -2))
        score -= 2
    
    # 2. Price vs 52-week range
    high_52 = info.get("fiftyTwoWeekHigh", 0)
    low_52 = info.get("fiftyTwoWeekLow", 0)
    price = info.get("regularMarketPrice", 0)
    
    if high_52 and low_52 and price:
        position = (price - low_52) / (high_52 - low_52) if high_52 != low_52 else 0.5
        if position > 0.8:
            signals.append(("52-Week Position", f"{position*100:.0f}%", "overbought", -1))
            score -= 1
        elif position < 0.2:
            signals.append(("52-Week Position", f"{position*100:.0f}%", "oversold", 1))
            score += 1
        else:
            signals.append(("52-Week Position", f"{position*100:.0f}%", "neutral", 0))
    
    # 3. RSI
    close = hist["Close"].values
    if len(close) > 14:
        deltas = [close[i] - close[i-1] for i in range(1, len(close))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[-14:]) / 14
        avg_loss = sum(losses[-14:]) / 14
        if avg_loss > 0:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 100
        
        if rsi > 70:
            signals.append(("RSI", f"{rsi:.1f}", "overbought", -1))
            score -= 1
        elif rsi < 30:
            signals.append(("RSI", f"{rsi:.1f}", "oversold", 1))
            score += 1
        else:
            signals.append(("RSI", f"{rsi:.1f}", "neutral", 0))
    
    # 4. Moving average trend
    sma_50 = sum(close[-50:]) / 50 if len(close) >= 50 else None
    sma_200 = sum(close[-200:]) / 200 if len(close) >= 200 else None
    
    if sma_50 and sma_200:
        if sma_50 > sma_200:
            signals.append(("Golden Cross", "SMA50 > SMA200", "bullish", 1))
            score += 1
        else:
            signals.append(("Death Cross", "SMA50 < SMA200", "bearish", -1))
            score -= 1
    
    # 5. Volume trend
    avg_vol = info.get("averageVolume", 0)
    curr_vol = info.get("regularMarketVolume", 0)
    
    if avg_vol and curr_vol:
        vol_ratio = curr_vol / avg_vol
        if vol_ratio > 1.5:
            signals.append(("Volume Surge", f"{vol_ratio:.1f}x avg", "high_interest", 0))
    
    # 6. Insider activity
    try:
        insiders = ticker.insider_transactions
        if insiders is not None and not insiders.empty:
            buys = insiders[insiders["Shares"].fillna(0) > 0].shape[0]
            sells = insiders[insiders["Shares"].fillna(0) < 0].shape[0]
            if buys > sells * 2:
                signals.append(("Insider Activity", f"{buys} buys vs {sells} sells", "bullish", 1))
                score += 1
            elif sells > buys * 2:
                signals.append(("Insider Activity", f"{sells} sells vs {buys} buys", "bearish", -1))
                score -= 1
    except:
        pass
    
    # Overall sentiment
    if score >= 3:
        overall = "STRONGLY BULLISH"
    elif score >= 1:
        overall = "BULLISH"
    elif score <= -3:
        overall = "STRONGLY BEARISH"
    elif score <= -1:
        overall = "BEARISH"
    else:
        overall = "NEUTRAL"
    
    return {
        "symbol": symbol.upper(),
        "overall_sentiment": overall,
        "sentiment_score": score,
        "max_score": 5,
        "min_score": -5,
        "signals": [{"indicator": s[0], "value": s[1], "signal": s[2], "score": s[3]} for s in signals],
    }
