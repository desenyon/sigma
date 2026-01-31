"""Financial data tools for Sigma."""

import json
from datetime import datetime, timedelta
from typing import Any, Optional

import yfinance as yf
import pandas as pd
import numpy as np


# ============================================================================
# STOCK DATA TOOLS
# ============================================================================

def get_stock_quote(symbol: str) -> dict:
    """Get current stock quote with key metrics."""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        return {
            "symbol": symbol.upper(),
            "name": info.get("shortName", "N/A"),
            "price": info.get("regularMarketPrice", 0),
            "change": info.get("regularMarketChange", 0),
            "change_percent": info.get("regularMarketChangePercent", 0),
            "open": info.get("regularMarketOpen", 0),
            "high": info.get("regularMarketDayHigh", 0),
            "low": info.get("regularMarketDayLow", 0),
            "volume": info.get("regularMarketVolume", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "52w_high": info.get("fiftyTwoWeekHigh", 0),
            "52w_low": info.get("fiftyTwoWeekLow", 0),
            "avg_volume": info.get("averageVolume", 0),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_stock_history(symbol: str, period: str = "3mo", interval: str = "1d") -> dict:
    """Get historical price data."""
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return {"error": "No data found", "symbol": symbol}
        
        # Calculate basic stats
        returns = hist["Close"].pct_change().dropna()
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "data_points": len(hist),
            "start_date": str(hist.index[0].date()),
            "end_date": str(hist.index[-1].date()),
            "start_price": round(hist["Close"].iloc[0], 2),
            "end_price": round(hist["Close"].iloc[-1], 2),
            "high": round(hist["High"].max(), 2),
            "low": round(hist["Low"].min(), 2),
            "total_return": round((hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100, 2),
            "volatility": round(returns.std() * np.sqrt(252) * 100, 2),
            "avg_volume": int(hist["Volume"].mean()),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_company_info(symbol: str) -> dict:
    """Get detailed company information."""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        return {
            "symbol": symbol.upper(),
            "name": info.get("longName", info.get("shortName", "N/A")),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "country": info.get("country", "N/A"),
            "website": info.get("website", "N/A"),
            "employees": info.get("fullTimeEmployees", "N/A"),
            "description": info.get("longBusinessSummary", "N/A")[:500] + "..." if info.get("longBusinessSummary") else "N/A",
            "market_cap": info.get("marketCap", 0),
            "enterprise_value": info.get("enterpriseValue", 0),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_financial_statements(symbol: str, statement: str = "income") -> dict:
    """Get financial statements (income, balance, cash)."""
    try:
        ticker = yf.Ticker(symbol.upper())
        
        if statement == "income":
            df = ticker.income_stmt
        elif statement == "balance":
            df = ticker.balance_sheet
        elif statement == "cash":
            df = ticker.cashflow
        else:
            return {"error": f"Unknown statement type: {statement}"}
        
        if df.empty:
            return {"error": "No data found", "symbol": symbol}
        
        # Get latest period
        latest = df.iloc[:, 0]
        
        # Convert to dict with formatted numbers
        data = {}
        for idx, val in latest.items():
            if pd.notna(val):
                if abs(val) >= 1e9:
                    data[str(idx)] = f"${val/1e9:.2f}B"
                elif abs(val) >= 1e6:
                    data[str(idx)] = f"${val/1e6:.2f}M"
                else:
                    data[str(idx)] = f"${val:,.0f}"
        
        # Get period from column
        col = df.columns[0]
        if hasattr(col, 'date'):
            period_str = str(col.date())  # type: ignore[union-attr]
        else:
            period_str = str(col)
        
        return {
            "symbol": symbol.upper(),
            "statement_type": statement,
            "period": period_str,
            "data": data
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_analyst_recommendations(symbol: str) -> dict:
    """Get analyst recommendations and price targets."""
    try:
        ticker = yf.Ticker(symbol.upper())
        
        # Get recommendations
        recs = ticker.recommendations
        rec_summary = {}
        if isinstance(recs, pd.DataFrame) and not recs.empty:
            recent = recs.tail(10)
            if "To Grade" in recent.columns:
                rec_summary = recent["To Grade"].value_counts().to_dict()
        
        # Get info for targets
        info = ticker.info
        
        return {
            "symbol": symbol.upper(),
            "recommendation": info.get("recommendationKey", "N/A"),
            "target_high": info.get("targetHighPrice", "N/A"),
            "target_low": info.get("targetLowPrice", "N/A"),
            "target_mean": info.get("targetMeanPrice", "N/A"),
            "target_median": info.get("targetMedianPrice", "N/A"),
            "num_analysts": info.get("numberOfAnalystOpinions", "N/A"),
            "recent_grades": rec_summary
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_insider_trades(symbol: str) -> dict:
    """Get recent insider trading activity."""
    try:
        ticker = yf.Ticker(symbol.upper())
        insiders = ticker.insider_transactions
        
        if insiders is None or insiders.empty:
            return {"symbol": symbol.upper(), "trades": [], "message": "No recent insider trades"}
        
        trades = []
        for _, row in insiders.head(10).iterrows():
            trades.append({
                "date": str(row.get("Start Date", ""))[:10],
                "insider": row.get("Insider", "N/A"),
                "position": row.get("Position", "N/A"),
                "transaction": row.get("Transaction", "N/A"),
                "shares": row.get("Shares", 0),
                "value": row.get("Value", 0),
            })
        
        return {
            "symbol": symbol.upper(),
            "trades": trades
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_institutional_holders(symbol: str) -> dict:
    """Get institutional ownership data."""
    try:
        ticker = yf.Ticker(symbol.upper())
        holders = ticker.institutional_holders
        
        if holders is None or holders.empty:
            return {"symbol": symbol.upper(), "holders": []}
        
        holder_list = []
        for _, row in holders.head(10).iterrows():
            holder_list.append({
                "holder": row.get("Holder", "N/A"),
                "shares": int(row.get("Shares", 0)),
                "date_reported": str(row.get("Date Reported", ""))[:10],
                "pct_held": round(row.get("% Out", 0) * 100, 2) if row.get("% Out") else 0,
                "value": int(row.get("Value", 0)),
            })
        
        return {
            "symbol": symbol.upper(),
            "holders": holder_list
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


# ============================================================================
# TECHNICAL ANALYSIS TOOLS
# ============================================================================

def technical_analysis(symbol: str, period: str = "6mo") -> dict:
    """Perform comprehensive technical analysis."""
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period)
        
        if hist.empty:
            return {"error": "No data found", "symbol": symbol}
        
        close = hist["Close"]
        high = hist["High"]
        low = hist["Low"]
        volume = hist["Volume"]
        
        # Moving averages
        sma_20 = close.rolling(20).mean().iloc[-1]
        sma_50 = close.rolling(50).mean().iloc[-1]
        sma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None
        ema_12 = close.ewm(span=12).mean().iloc[-1]
        ema_26 = close.ewm(span=26).mean().iloc[-1]
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        # MACD
        macd = ema_12 - ema_26
        signal = close.ewm(span=9).mean().iloc[-1]
        
        # Bollinger Bands
        bb_mid = close.rolling(20).mean().iloc[-1]
        bb_std = close.rolling(20).std().iloc[-1]
        bb_upper = bb_mid + (bb_std * 2)
        bb_lower = bb_mid - (bb_std * 2)
        
        # Support/Resistance (simple)
        recent_high = high.tail(20).max()
        recent_low = low.tail(20).min()
        
        # Volume analysis
        avg_vol = volume.mean()
        recent_vol = volume.tail(5).mean()
        vol_trend = "Above Average" if recent_vol > avg_vol else "Below Average"
        
        current_price = close.iloc[-1]
        
        # Generate signals
        signals = []
        if current_price > sma_20:
            signals.append("Above SMA20 (Bullish)")
        else:
            signals.append("Below SMA20 (Bearish)")
        
        if current_price > sma_50:
            signals.append("Above SMA50 (Bullish)")
        else:
            signals.append("Below SMA50 (Bearish)")
        
        if rsi > 70:
            signals.append("RSI Overbought (>70)")
        elif rsi < 30:
            signals.append("RSI Oversold (<30)")
        else:
            signals.append(f"RSI Neutral ({rsi:.1f})")
        
        if macd > signal:
            signals.append("MACD Bullish Crossover")
        else:
            signals.append("MACD Bearish")
        
        return {
            "symbol": symbol.upper(),
            "current_price": round(current_price, 2),
            "indicators": {
                "sma_20": round(sma_20, 2),
                "sma_50": round(sma_50, 2),
                "sma_200": round(sma_200, 2) if sma_200 else "N/A",
                "ema_12": round(ema_12, 2),
                "ema_26": round(ema_26, 2),
                "rsi": round(rsi, 2),
                "macd": round(macd, 4),
                "bb_upper": round(bb_upper, 2),
                "bb_mid": round(bb_mid, 2),
                "bb_lower": round(bb_lower, 2),
            },
            "support_resistance": {
                "resistance": round(recent_high, 2),
                "support": round(recent_low, 2),
            },
            "volume": {
                "average": int(avg_vol),
                "recent": int(recent_vol),
                "trend": vol_trend,
            },
            "signals": signals,
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


# ============================================================================
# COMPARISON & MARKET TOOLS
# ============================================================================

def compare_stocks(symbols: list[str], period: str = "1y") -> dict:
    """Compare multiple stocks."""
    try:
        results = []
        
        for symbol in symbols[:5]:  # Limit to 5
            ticker = yf.Ticker(symbol.upper())
            hist = ticker.history(period=period)
            info = ticker.info
            
            if hist.empty:
                continue
            
            returns = hist["Close"].pct_change().dropna()
            total_return = (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100
            
            results.append({
                "symbol": symbol.upper(),
                "name": info.get("shortName", "N/A"),
                "price": round(hist["Close"].iloc[-1], 2),
                "total_return": round(total_return, 2),
                "volatility": round(returns.std() * np.sqrt(252) * 100, 2),
                "sharpe": round((returns.mean() * 252) / (returns.std() * np.sqrt(252)), 2) if returns.std() > 0 else 0,
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", "N/A"),
            })
        
        # Sort by return
        results.sort(key=lambda x: x["total_return"], reverse=True)
        
        return {
            "period": period,
            "comparison": results,
            "best_performer": results[0]["symbol"] if results else None,
            "worst_performer": results[-1]["symbol"] if results else None,
        }
    except Exception as e:
        return {"error": str(e)}


def get_market_overview() -> dict:
    """Get market overview with major indices."""
    indices = {
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ",
        "^RUT": "Russell 2000",
        "^VIX": "VIX",
    }
    
    results = []
    for symbol, name in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            results.append({
                "symbol": symbol,
                "name": name,
                "price": info.get("regularMarketPrice", 0),
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
            })
        except:
            continue
    
    return {"indices": results, "timestamp": datetime.now().isoformat()}


def get_sector_performance() -> dict:
    """Get sector ETF performance."""
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
    }
    
    results = []
    for symbol, name in sectors.items():
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            results.append({
                "symbol": symbol,
                "sector": name,
                "price": info.get("regularMarketPrice", 0),
                "change_percent": round(info.get("regularMarketChangePercent", 0), 2),
            })
        except:
            continue
    
    # Sort by performance
    results.sort(key=lambda x: x["change_percent"], reverse=True)
    
    return {"sectors": results, "timestamp": datetime.now().isoformat()}


# ============================================================================
# ALPHA VANTAGE TOOLS (Economic Data, Intraday, News)
# ============================================================================

def _get_alpha_vantage_key() -> Optional[str]:
    """Get Alpha Vantage API key from config."""
    try:
        from .config import get_settings
        return get_settings().alpha_vantage_api_key
    except:
        return None


def get_economic_indicators(indicator: str = "GDP") -> dict:
    """Get economic indicators from Alpha Vantage (GDP, inflation, unemployment, etc.)."""
    api_key = _get_alpha_vantage_key()
    if not api_key:
        return {"error": "Alpha Vantage API key not configured. Set ALPHA_VANTAGE_API_KEY in ~/.sigma/config.env"}
    
    import requests
    
    indicator_map = {
        "GDP": "REAL_GDP",
        "INFLATION": "INFLATION",
        "UNEMPLOYMENT": "UNEMPLOYMENT",
        "INTEREST_RATE": "FEDERAL_FUNDS_RATE",
        "CPI": "CPI",
        "RETAIL_SALES": "RETAIL_SALES",
        "NONFARM_PAYROLL": "NONFARM_PAYROLL",
    }
    
    av_indicator = indicator_map.get(indicator.upper(), indicator.upper())
    
    try:
        url = f"https://www.alphavantage.co/query?function={av_indicator}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "Error Message" in data:
            return {"error": data["Error Message"]}
        
        if "data" in data:
            # Return most recent data points
            recent = data["data"][:12]  # Last 12 periods
            return {
                "indicator": indicator.upper(),
                "name": data.get("name", indicator),
                "unit": data.get("unit", ""),
                "data": [{"date": d["date"], "value": d["value"]} for d in recent]
            }
        
        return {"error": "No data returned", "raw": data}
    except Exception as e:
        return {"error": str(e)}


def get_intraday_data(symbol: str, interval: str = "5min") -> dict:
    """Get intraday price data from Alpha Vantage."""
    api_key = _get_alpha_vantage_key()
    if not api_key:
        return {"error": "Alpha Vantage API key not configured. Set ALPHA_VANTAGE_API_KEY in ~/.sigma/config.env"}
    
    import requests
    
    valid_intervals = ["1min", "5min", "15min", "30min", "60min"]
    if interval not in valid_intervals:
        return {"error": f"Invalid interval. Use: {valid_intervals}"}
    
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval={interval}&apikey={api_key}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if "Error Message" in data:
            return {"error": data["Error Message"]}
        
        time_series_key = f"Time Series ({interval})"
        if time_series_key not in data:
            return {"error": "No data returned. Check symbol or API limits.", "raw": data}
        
        # Get last 20 candles
        series = data[time_series_key]
        candles = []
        for timestamp, values in list(series.items())[:20]:
            candles.append({
                "timestamp": timestamp,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"])
            })
        
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "candles": candles
        }
    except Exception as e:
        return {"error": str(e)}


def get_market_news(tickers: str = "", topics: str = "") -> dict:
    """Get market news and sentiment from Alpha Vantage."""
    api_key = _get_alpha_vantage_key()
    if not api_key:
        return {"error": "Alpha Vantage API key not configured. Set ALPHA_VANTAGE_API_KEY in ~/.sigma/config.env"}
    
    import requests
    
    try:
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&apikey={api_key}"
        if tickers:
            url += f"&tickers={tickers}"
        if topics:
            url += f"&topics={topics}"
        
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if "Error Message" in data:
            return {"error": data["Error Message"]}
        
        feed = data.get("feed", [])[:10]  # Get top 10 news items
        
        articles = []
        for item in feed:
            articles.append({
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "time": item.get("time_published", ""),
                "summary": item.get("summary", "")[:300] + "..." if item.get("summary") else "",
                "sentiment": item.get("overall_sentiment_label", ""),
                "sentiment_score": item.get("overall_sentiment_score", 0),
                "tickers": [t["ticker"] for t in item.get("ticker_sentiment", [])[:3]]
            })
        
        return {
            "articles": articles,
            "query": {"tickers": tickers, "topics": topics}
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# EXA SEARCH TOOLS (Financial News, SEC Filings)
# ============================================================================

def _get_exa_key() -> Optional[str]:
    """Get Exa API key from config."""
    try:
        from .config import get_settings
        return get_settings().exa_api_key
    except:
        return None


def search_financial_news(query: str, num_results: int = 5) -> dict:
    """Search for financial news using Exa."""
    api_key = _get_exa_key()
    if not api_key:
        return {"error": "Exa API key not configured. Set EXA_API_KEY in ~/.sigma/config.env"}
    
    import requests
    
    try:
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "num_results": num_results,
            "use_autoprompt": True,
            "type": "neural",
            "include_domains": [
                "reuters.com", "bloomberg.com", "wsj.com", "cnbc.com",
                "marketwatch.com", "ft.com", "seekingalpha.com", "yahoo.com/finance"
            ]
        }
        
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code != 200:
            return {"error": f"Exa API error: {response.status_code}", "details": response.text}
        
        data = response.json()
        
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published": item.get("publishedDate", ""),
                "score": item.get("score", 0)
            })
        
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}


def search_sec_filings(company: str, filing_type: str = "10-K", num_results: int = 3) -> dict:
    """Search for SEC filings using Exa."""
    api_key = _get_exa_key()
    if not api_key:
        return {"error": "Exa API key not configured. Set EXA_API_KEY in ~/.sigma/config.env"}
    
    import requests
    
    try:
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        query = f"{company} {filing_type} SEC filing site:sec.gov"
        
        payload = {
            "query": query,
            "num_results": num_results,
            "use_autoprompt": True,
            "type": "neural",
            "include_domains": ["sec.gov"]
        }
        
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code != 200:
            return {"error": f"Exa API error: {response.status_code}"}
        
        data = response.json()
        
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published": item.get("publishedDate", "")
            })
        
        return {
            "company": company,
            "filing_type": filing_type,
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}


def search_earnings_transcripts(company: str, num_results: int = 3) -> dict:
    """Search for earnings call transcripts using Exa."""
    api_key = _get_exa_key()
    if not api_key:
        return {"error": "Exa API key not configured. Set EXA_API_KEY in ~/.sigma/config.env"}
    
    import requests
    
    try:
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        query = f"{company} earnings call transcript Q4 2025"
        
        payload = {
            "query": query,
            "num_results": num_results,
            "use_autoprompt": True,
            "type": "neural",
            "include_domains": [
                "seekingalpha.com", "fool.com", "reuters.com"
            ]
        }
        
        response = requests.post(
            "https://api.exa.ai/search",
            headers=headers,
            json=payload,
            timeout=15
        )
        
        if response.status_code != 200:
            return {"error": f"Exa API error: {response.status_code}"}
        
        data = response.json()
        
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published": item.get("publishedDate", "")
            })
        
        return {
            "company": company,
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# TOOL DEFINITIONS FOR LLM
# ============================================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_quote",
            "description": "Get current stock quote with price, change, volume, and key metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol (e.g., AAPL, MSFT)"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_history",
            "description": "Get historical price data and returns for a stock",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "description": "Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max", "default": "3mo"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_company_info",
            "description": "Get detailed company information including sector, industry, and description",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_financial_statements",
            "description": "Get financial statements (income statement, balance sheet, or cash flow)",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"},
                    "statement": {"type": "string", "enum": ["income", "balance", "cash"], "description": "Type of statement", "default": "income"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_analyst_recommendations",
            "description": "Get analyst recommendations, price targets, and ratings",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_insider_trades",
            "description": "Get recent insider trading activity",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_institutional_holders",
            "description": "Get institutional ownership and major shareholders",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "technical_analysis",
            "description": "Perform comprehensive technical analysis with indicators (RSI, MACD, Moving Averages, Bollinger Bands)",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "description": "Analysis period", "default": "6mo"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compare_stocks",
            "description": "Compare multiple stocks on returns, volatility, and metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbols": {"type": "array", "items": {"type": "string"}, "description": "List of stock symbols to compare"},
                    "period": {"type": "string", "description": "Comparison period", "default": "1y"}
                },
                "required": ["symbols"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_overview",
            "description": "Get overview of major market indices (S&P 500, Dow, NASDAQ, etc.)",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_sector_performance",
            "description": "Get performance of market sectors",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    # Alpha Vantage tools
    {
        "type": "function",
        "function": {
            "name": "get_economic_indicators",
            "description": "Get economic indicators like GDP, inflation, unemployment, interest rates, CPI",
            "parameters": {
                "type": "object",
                "properties": {
                    "indicator": {"type": "string", "enum": ["GDP", "INFLATION", "UNEMPLOYMENT", "INTEREST_RATE", "CPI", "RETAIL_SALES", "NONFARM_PAYROLL"], "description": "Economic indicator to retrieve"}
                },
                "required": ["indicator"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_intraday_data",
            "description": "Get intraday price data with 1min, 5min, 15min, 30min, or 60min candles",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"},
                    "interval": {"type": "string", "enum": ["1min", "5min", "15min", "30min", "60min"], "description": "Candle interval", "default": "5min"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_market_news",
            "description": "Get market news and sentiment for specific tickers or topics",
            "parameters": {
                "type": "object",
                "properties": {
                    "tickers": {"type": "string", "description": "Comma-separated ticker symbols (e.g., AAPL,MSFT)"},
                    "topics": {"type": "string", "description": "Topics like: earnings, ipo, mergers, technology, finance"}
                },
                "required": []
            }
        }
    },
    # Exa Search tools
    {
        "type": "function",
        "function": {
            "name": "search_financial_news",
            "description": "Search for financial news articles from major sources (Bloomberg, Reuters, WSJ, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for financial news"},
                    "num_results": {"type": "integer", "description": "Number of results (1-10)", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_sec_filings",
            "description": "Search for SEC filings (10-K, 10-Q, 8-K, etc.) for a company",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {"type": "string", "description": "Company name or ticker"},
                    "filing_type": {"type": "string", "enum": ["10-K", "10-Q", "8-K", "S-1", "DEF 14A"], "description": "Type of SEC filing", "default": "10-K"},
                    "num_results": {"type": "integer", "description": "Number of results", "default": 3}
                },
                "required": ["company"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_earnings_transcripts",
            "description": "Search for earnings call transcripts",
            "parameters": {
                "type": "object",
                "properties": {
                    "company": {"type": "string", "description": "Company name or ticker"},
                    "num_results": {"type": "integer", "description": "Number of results", "default": 3}
                },
                "required": ["company"]
            }
        }
    },
]


# Tool executor
TOOL_FUNCTIONS = {
    "get_stock_quote": get_stock_quote,
    "get_stock_history": get_stock_history,
    "get_company_info": get_company_info,
    "get_financial_statements": get_financial_statements,
    "get_analyst_recommendations": get_analyst_recommendations,
    "get_insider_trades": get_insider_trades,
    "get_institutional_holders": get_institutional_holders,
    "technical_analysis": technical_analysis,
    "compare_stocks": compare_stocks,
    "get_market_overview": get_market_overview,
    "get_sector_performance": get_sector_performance,
    # Alpha Vantage
    "get_economic_indicators": get_economic_indicators,
    "get_intraday_data": get_intraday_data,
    "get_market_news": get_market_news,
    # Exa Search
    "search_financial_news": search_financial_news,
    "search_sec_filings": search_sec_filings,
    "search_earnings_transcripts": search_earnings_transcripts,
}


def execute_tool(name: str, args: dict) -> Any:
    """Execute a tool by name."""
    func = TOOL_FUNCTIONS.get(name)
    if func:
        return func(**args)
    return {"error": f"Unknown tool: {name}"}
