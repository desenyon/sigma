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
# POLYGON.IO TOOLS (Real-time & Historical Market Data)
# ============================================================================

def _get_polygon_key() -> Optional[str]:
    """Get Polygon.io API key from config."""
    try:
        from .config import get_settings
        return get_settings().polygon_api_key
    except:
        return None


def polygon_get_quote(symbol: str) -> dict:
    """Get real-time quote from Polygon.io with additional data."""
    api_key = _get_polygon_key()
    if not api_key:
        return {"error": "Polygon API key not configured. Use /setkey polygon <key>", "fallback": True}
    
    import requests
    
    try:
        symbol = symbol.upper()
        
        # Get previous day's data
        prev_url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apiKey={api_key}"
        prev_response = requests.get(prev_url, timeout=10)
        
        if prev_response.status_code == 403:
            return {"error": "Polygon API key is invalid or expired", "error_code": 1101}
        elif prev_response.status_code == 429:
            return {"error": "Polygon rate limit exceeded", "error_code": 1303}
        elif prev_response.status_code != 200:
            return {"error": f"Polygon API error: {prev_response.status_code}"}
        
        prev_data = prev_response.json()
        
        if prev_data.get("resultsCount", 0) == 0:
            return {"error": f"No data found for {symbol}", "error_code": 1300}
        
        result = prev_data["results"][0]
        
        # Get ticker details
        details_url = f"https://api.polygon.io/v3/reference/tickers/{symbol}?apiKey={api_key}"
        details_response = requests.get(details_url, timeout=10)
        details = {}
        if details_response.status_code == 200:
            details_data = details_response.json()
            if details_data.get("results"):
                details = details_data["results"]
        
        return {
            "symbol": symbol,
            "name": details.get("name", symbol),
            "open": result.get("o", 0),
            "high": result.get("h", 0),
            "low": result.get("l", 0),
            "close": result.get("c", 0),
            "volume": result.get("v", 0),
            "vwap": result.get("vw", 0),
            "timestamp": result.get("t"),
            "transactions": result.get("n", 0),
            "market_cap": details.get("market_cap"),
            "primary_exchange": details.get("primary_exchange"),
            "type": details.get("type"),
            "source": "polygon.io"
        }
    except requests.exceptions.Timeout:
        return {"error": "Request timed out", "error_code": 1002}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection error", "error_code": 1400}
    except Exception as e:
        return {"error": str(e), "error_code": 1000}


def polygon_get_aggregates(symbol: str, timespan: str = "day", multiplier: int = 1, 
                           from_date: str = "", to_date: str = "", limit: int = 120) -> dict:
    """Get historical aggregated bars from Polygon.io."""
    api_key = _get_polygon_key()
    if not api_key:
        return {"error": "Polygon API key not configured. Use /setkey polygon <key>"}
    
    import requests
    
    try:
        symbol = symbol.upper()
        
        # Default date range: last 6 months
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            from_date = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        
        url = (f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/"
               f"{multiplier}/{timespan}/{from_date}/{to_date}"
               f"?adjusted=true&sort=desc&limit={limit}&apiKey={api_key}")
        
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            return {"error": f"Polygon API error: {response.status_code}"}
        
        data = response.json()
        
        if data.get("resultsCount", 0) == 0:
            return {"error": f"No data found for {symbol}"}
        
        results = data["results"]
        
        # Calculate statistics
        closes = [r["c"] for r in results]
        highs = [r["h"] for r in results]
        lows = [r["l"] for r in results]
        volumes = [r["v"] for r in results]
        
        latest = results[0]
        oldest = results[-1]
        
        return {
            "symbol": symbol,
            "timespan": timespan,
            "from": from_date,
            "to": to_date,
            "data_points": len(results),
            "latest_close": latest["c"],
            "oldest_close": oldest["c"],
            "period_return": round((latest["c"] / oldest["c"] - 1) * 100, 2),
            "high": max(highs),
            "low": min(lows),
            "avg_volume": int(sum(volumes) / len(volumes)),
            "total_volume": sum(volumes),
            "source": "polygon.io"
        }
    except Exception as e:
        return {"error": str(e)}


def polygon_get_ticker_news(symbol: str, limit: int = 10) -> dict:
    """Get news articles for a ticker from Polygon.io."""
    api_key = _get_polygon_key()
    if not api_key:
        return {"error": "Polygon API key not configured. Use /setkey polygon <key>"}
    
    import requests
    
    try:
        symbol = symbol.upper()
        url = f"https://api.polygon.io/v2/reference/news?ticker={symbol}&limit={limit}&apiKey={api_key}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {"error": f"Polygon API error: {response.status_code}"}
        
        data = response.json()
        articles = []
        
        for item in data.get("results", []):
            articles.append({
                "title": item.get("title", ""),
                "author": item.get("author", ""),
                "published": item.get("published_utc", ""),
                "article_url": item.get("article_url", ""),
                "tickers": item.get("tickers", []),
                "description": item.get("description", "")[:300] + "..." if item.get("description") else "",
                "keywords": item.get("keywords", [])[:5]
            })
        
        return {
            "symbol": symbol,
            "articles": articles,
            "source": "polygon.io"
        }
    except Exception as e:
        return {"error": str(e)}


def polygon_market_status() -> dict:
    """Get current market status from Polygon.io."""
    api_key = _get_polygon_key()
    if not api_key:
        return {"error": "Polygon API key not configured. Use /setkey polygon <key>"}
    
    import requests
    
    try:
        url = f"https://api.polygon.io/v1/marketstatus/now?apiKey={api_key}"
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return {"error": f"Polygon API error: {response.status_code}"}
        
        data = response.json()
        
        return {
            "market": data.get("market", "unknown"),
            "server_time": data.get("serverTime"),
            "exchanges": data.get("exchanges", {}),
            "currencies": data.get("currencies", {}),
            "source": "polygon.io"
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
# CHART GENERATION TOOLS
# ============================================================================

def generate_stock_chart(symbol: str, period: str = "6mo", chart_type: str = "candlestick", 
                         show_volume: bool = True, show_indicators: bool = True) -> dict:
    """Generate a stock chart and save it to file."""
    try:
        from .charts import create_candlestick_chart, create_line_chart, create_technical_chart
        
        ticker = yf.Ticker(symbol.upper())
        data = ticker.history(period=period)
        
        if data.empty:
            return {"error": f"No data found for {symbol}", "symbol": symbol}
        
        # Generate chart based on type
        if chart_type == "candlestick":
            chart_path = create_candlestick_chart(
                symbol=symbol,
                data=data,
                show_volume=show_volume,
                show_sma=show_indicators
            )
        elif chart_type == "line":
            chart_path = create_line_chart(
                symbol=symbol,
                data=data,
                show_volume=show_volume
            )
        elif chart_type == "technical":
            chart_path = create_technical_chart(
                symbol=symbol,
                data=data,
                indicators=["rsi", "macd"] if show_indicators else []
            )
        else:
            chart_path = create_candlestick_chart(symbol=symbol, data=data)
        
        return {
            "symbol": symbol.upper(),
            "chart_type": chart_type,
            "period": period,
            "chart_path": chart_path,
            "message": f"Chart generated and saved to: {chart_path}",
            "data_points": len(data),
            "start_date": str(data.index[0].date()),
            "end_date": str(data.index[-1].date()),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def generate_comparison_chart(symbols: list, period: str = "1y", normalize: bool = True) -> dict:
    """Generate a comparison chart for multiple stocks."""
    try:
        from .charts import create_comparison_chart
        
        data_dict = {}
        for symbol in symbols:
            ticker = yf.Ticker(symbol.upper())
            data = ticker.history(period=period)
            if not data.empty:
                data_dict[symbol.upper()] = data
        
        if not data_dict:
            return {"error": "No data found for any symbols", "symbols": symbols}
        
        chart_path = create_comparison_chart(
            symbols=[s.upper() for s in symbols],
            data_dict=data_dict,
            normalize=normalize
        )
        
        return {
            "symbols": list(data_dict.keys()),
            "period": period,
            "normalized": normalize,
            "chart_path": chart_path,
            "message": f"Comparison chart saved to: {chart_path}"
        }
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# ADVANCED ANALYSIS TOOLS
# ============================================================================

def get_valuation_metrics(symbol: str) -> dict:
    """Get comprehensive valuation metrics for a stock."""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        # Calculate valuation ratios
        pe_ratio = info.get("trailingPE", None)
        forward_pe = info.get("forwardPE", None)
        peg_ratio = info.get("pegRatio", None)
        pb_ratio = info.get("priceToBook", None)
        ps_ratio = info.get("priceToSalesTrailing12Months", None)
        ev_ebitda = info.get("enterpriseToEbitda", None)
        ev_revenue = info.get("enterpriseToRevenue", None)
        
        # Get growth metrics
        earnings_growth = info.get("earningsGrowth", None)
        revenue_growth = info.get("revenueGrowth", None)
        
        # Get profitability
        profit_margin = info.get("profitMargins", None)
        operating_margin = info.get("operatingMargins", None)
        roe = info.get("returnOnEquity", None)
        roa = info.get("returnOnAssets", None)
        
        # Determine valuation assessment
        assessment = "FAIR"
        if pe_ratio and forward_pe:
            if pe_ratio > 30 and forward_pe > 25:
                assessment = "EXPENSIVE"
            elif pe_ratio < 15 and forward_pe < 12:
                assessment = "CHEAP"
        
        return {
            "symbol": symbol.upper(),
            "name": info.get("shortName", symbol),
            "valuation": {
                "pe_ratio": round(pe_ratio, 2) if pe_ratio else "N/A",
                "forward_pe": round(forward_pe, 2) if forward_pe else "N/A",
                "peg_ratio": round(peg_ratio, 2) if peg_ratio else "N/A",
                "price_to_book": round(pb_ratio, 2) if pb_ratio else "N/A",
                "price_to_sales": round(ps_ratio, 2) if ps_ratio else "N/A",
                "ev_to_ebitda": round(ev_ebitda, 2) if ev_ebitda else "N/A",
                "ev_to_revenue": round(ev_revenue, 2) if ev_revenue else "N/A",
            },
            "growth": {
                "earnings_growth": f"{earnings_growth*100:.1f}%" if earnings_growth else "N/A",
                "revenue_growth": f"{revenue_growth*100:.1f}%" if revenue_growth else "N/A",
            },
            "profitability": {
                "profit_margin": f"{profit_margin*100:.1f}%" if profit_margin else "N/A",
                "operating_margin": f"{operating_margin*100:.1f}%" if operating_margin else "N/A",
                "return_on_equity": f"{roe*100:.1f}%" if roe else "N/A",
                "return_on_assets": f"{roa*100:.1f}%" if roa else "N/A",
            },
            "assessment": assessment,
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_risk_metrics(symbol: str, period: str = "1y") -> dict:
    """Calculate comprehensive risk metrics for a stock."""
    try:
        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(period=period)
        
        if hist.empty or len(hist) < 30:
            return {"error": "Insufficient data for risk analysis", "symbol": symbol}
        
        # Calculate daily returns
        returns = hist["Close"].pct_change().dropna()
        
        # Basic risk metrics
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Value at Risk (VaR) - 95% confidence
        var_95 = np.percentile(returns, 5) * 100
        
        # Conditional VaR (Expected Shortfall)
        cvar_95 = returns[returns <= np.percentile(returns, 5)].mean() * 100
        
        # Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # Sharpe Ratio (assuming 0% risk-free rate)
        sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252))
        
        # Sortino Ratio
        negative_returns = returns[returns < 0]
        downside_std = negative_returns.std() * np.sqrt(252)
        sortino = (returns.mean() * 252) / downside_std if downside_std > 0 else 0
        
        # Beta calculation vs SPY
        try:
            spy = yf.Ticker("SPY")
            spy_hist = spy.history(period=period)
            spy_returns = spy_hist["Close"].pct_change().dropna()
            
            # Align dates
            common_dates = returns.index.intersection(spy_returns.index)
            if len(common_dates) > 30:
                stock_r = returns.loc[common_dates]
                spy_r = spy_returns.loc[common_dates]
                
                covariance = np.cov(stock_r, spy_r)[0, 1]
                spy_variance = np.var(spy_r)
                beta = covariance / spy_variance if spy_variance > 0 else 1.0
                
                # Alpha (annualized)
                alpha = (returns.mean() * 252) - (beta * spy_returns.mean() * 252)
            else:
                beta = 1.0
                alpha = 0
        except:
            beta = 1.0
            alpha = 0
        
        # Risk assessment
        risk_level = "MODERATE"
        if volatility > 40 or abs(max_drawdown) > 30:
            risk_level = "HIGH"
        elif volatility < 20 and abs(max_drawdown) < 15:
            risk_level = "LOW"
        
        return {
            "symbol": symbol.upper(),
            "period": period,
            "volatility": {
                "annualized": f"{volatility:.2f}%",
                "daily": f"{returns.std()*100:.3f}%",
            },
            "drawdown": {
                "max_drawdown": f"{max_drawdown:.2f}%",
                "current_drawdown": f"{drawdown.iloc[-1]*100:.2f}%",
            },
            "value_at_risk": {
                "var_95": f"{var_95:.2f}%",
                "cvar_95": f"{cvar_95:.2f}%",
            },
            "ratios": {
                "sharpe": f"{sharpe:.2f}",
                "sortino": f"{sortino:.2f}",
                "beta": f"{beta:.2f}",
                "alpha": f"{alpha*100:.2f}%",
            },
            "risk_level": risk_level,
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_earnings_analysis(symbol: str) -> dict:
    """Get detailed earnings analysis including surprises and estimates."""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        # Get earnings dates and history
        earnings_dates = ticker.earnings_dates
        earnings_history = ticker.earnings_history if hasattr(ticker, 'earnings_history') else None
        
        # Build earnings data
        upcoming = None
        if earnings_dates is not None and not earnings_dates.empty:
            future_dates = earnings_dates[earnings_dates.index > pd.Timestamp.now()]
            if not future_dates.empty:
                next_date = future_dates.index[0]
                upcoming = {
                    "date": str(next_date.date()) if hasattr(next_date, 'date') else str(next_date)[:10],
                    "eps_estimate": future_dates.iloc[0].get("EPS Estimate", "N/A"),
                    "revenue_estimate": future_dates.iloc[0].get("Revenue Estimate", "N/A"),
                }
        
        # Get quarterly earnings
        quarterly_earnings = []
        if hasattr(ticker, 'quarterly_earnings') and ticker.quarterly_earnings is not None:
            qe = ticker.quarterly_earnings
            if not qe.empty:
                for date, row in qe.tail(4).iterrows():
                    quarterly_earnings.append({
                        "quarter": str(date),
                        "revenue": row.get("Revenue", "N/A"),
                        "earnings": row.get("Earnings", "N/A"),
                    })
        
        return {
            "symbol": symbol.upper(),
            "name": info.get("shortName", symbol),
            "eps_trailing": info.get("trailingEps", "N/A"),
            "eps_forward": info.get("forwardEps", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "upcoming_earnings": upcoming,
            "quarterly_history": quarterly_earnings,
            "earnings_growth": f"{info.get('earningsGrowth', 0)*100:.1f}%" if info.get('earningsGrowth') else "N/A",
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_dividend_analysis(symbol: str) -> dict:
    """Get comprehensive dividend analysis."""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        # Get dividend data
        div_rate = info.get("dividendRate", 0)
        div_yield = info.get("dividendYield", 0)
        payout_ratio = info.get("payoutRatio", 0)
        ex_div_date = info.get("exDividendDate")
        
        # Get dividend history
        dividends = ticker.dividends
        div_history = []
        if dividends is not None and not dividends.empty:
            for dt, amount in dividends.tail(8).items():
                date_str = str(dt.date()) if hasattr(dt, 'date') else str(dt)[:10]  # type: ignore[union-attr]
                div_history.append({
                    "date": date_str,
                    "amount": f"${amount:.4f}",
                })
        
        # Calculate dividend growth
        if len(dividends) >= 8:
            recent_divs = dividends.tail(4).sum()
            older_divs = dividends.tail(8).head(4).sum()
            div_growth = ((recent_divs / older_divs) - 1) * 100 if older_divs > 0 else 0
        else:
            div_growth = None
        
        return {
            "symbol": symbol.upper(),
            "name": info.get("shortName", symbol),
            "dividend_rate": f"${div_rate:.2f}" if div_rate else "N/A",
            "dividend_yield": f"{div_yield*100:.2f}%" if div_yield else "N/A",
            "payout_ratio": f"{payout_ratio*100:.1f}%" if payout_ratio else "N/A",
            "ex_dividend_date": str(datetime.fromtimestamp(ex_div_date).date()) if ex_div_date else "N/A",
            "annual_dividend": f"${div_rate:.2f}" if div_rate else "N/A",
            "dividend_growth_yoy": f"{div_growth:.1f}%" if div_growth else "N/A",
            "history": div_history,
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_options_summary(symbol: str) -> dict:
    """Get options chain summary with key metrics."""
    try:
        ticker = yf.Ticker(symbol.upper())
        
        # Get expiration dates
        expirations = ticker.options
        if not expirations:
            return {"error": "No options available", "symbol": symbol}
        
        # Get nearest expiration
        nearest_exp = expirations[0]
        opt_chain = ticker.option_chain(nearest_exp)
        
        calls = opt_chain.calls
        puts = opt_chain.puts
        
        # Calculate put/call ratio
        total_call_volume = calls["volume"].sum() if "volume" in calls else 0
        total_put_volume = puts["volume"].sum() if "volume" in puts else 0
        pc_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else 0
        
        # Get ATM options
        current_price = ticker.info.get("regularMarketPrice", 0)
        
        atm_call = calls.iloc[(calls["strike"] - current_price).abs().argsort()[:1]]
        atm_put = puts.iloc[(puts["strike"] - current_price).abs().argsort()[:1]]
        
        # Implied volatility
        atm_call_iv = atm_call["impliedVolatility"].values[0] if not atm_call.empty else 0
        atm_put_iv = atm_put["impliedVolatility"].values[0] if not atm_put.empty else 0
        avg_iv = (atm_call_iv + atm_put_iv) / 2
        
        return {
            "symbol": symbol.upper(),
            "current_price": f"${current_price:.2f}",
            "expirations_available": len(expirations),
            "nearest_expiration": nearest_exp,
            "put_call_ratio": f"{pc_ratio:.2f}",
            "implied_volatility": f"{avg_iv*100:.1f}%",
            "call_volume": int(total_call_volume) if total_call_volume else 0,
            "put_volume": int(total_put_volume) if total_put_volume else 0,
            "atm_call": {
                "strike": float(atm_call["strike"].values[0]) if not atm_call.empty else 0,
                "bid": float(atm_call["bid"].values[0]) if not atm_call.empty else 0,
                "ask": float(atm_call["ask"].values[0]) if not atm_call.empty else 0,
                "iv": f"{atm_call_iv*100:.1f}%",
            },
            "atm_put": {
                "strike": float(atm_put["strike"].values[0]) if not atm_put.empty else 0,
                "bid": float(atm_put["bid"].values[0]) if not atm_put.empty else 0,
                "ask": float(atm_put["ask"].values[0]) if not atm_put.empty else 0,
                "iv": f"{atm_put_iv*100:.1f}%",
            },
            "sentiment": "BEARISH" if pc_ratio > 1.2 else ("BULLISH" if pc_ratio < 0.7 else "NEUTRAL"),
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_peer_comparison(symbol: str) -> dict:
    """Compare a stock with its industry peers."""
    try:
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        
        # Get sector and find peers
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        
        # Define peer groups by industry
        tech_peers = ["AAPL", "MSFT", "GOOGL", "META", "AMZN"]
        semi_peers = ["NVDA", "AMD", "INTC", "AVGO", "QCOM"]
        finance_peers = ["JPM", "BAC", "GS", "MS", "C"]
        healthcare_peers = ["JNJ", "PFE", "UNH", "MRK", "ABBV"]
        
        # Select peer group
        symbol_upper = symbol.upper()
        if symbol_upper in tech_peers or "Technology" in sector:
            peers = [p for p in tech_peers if p != symbol_upper][:4]
        elif symbol_upper in semi_peers or "Semiconductor" in industry:
            peers = [p for p in semi_peers if p != symbol_upper][:4]
        elif symbol_upper in finance_peers or "Financial" in sector:
            peers = [p for p in finance_peers if p != symbol_upper][:4]
        elif symbol_upper in healthcare_peers or "Healthcare" in sector:
            peers = [p for p in healthcare_peers if p != symbol_upper][:4]
        else:
            peers = []
        
        # Get metrics for target and peers
        all_symbols = [symbol_upper] + peers
        comparison = []
        
        for sym in all_symbols:
            try:
                t = yf.Ticker(sym)
                i = t.info
                comparison.append({
                    "symbol": sym,
                    "name": i.get("shortName", sym),
                    "price": i.get("regularMarketPrice", 0),
                    "market_cap": i.get("marketCap", 0),
                    "pe_ratio": round(i.get("trailingPE", 0), 2) if i.get("trailingPE") else "N/A",
                    "pb_ratio": round(i.get("priceToBook", 0), 2) if i.get("priceToBook") else "N/A",
                    "dividend_yield": f"{i.get('dividendYield', 0)*100:.2f}%" if i.get("dividendYield") else "N/A",
                    "profit_margin": f"{i.get('profitMargins', 0)*100:.1f}%" if i.get("profitMargins") else "N/A",
                })
            except:
                continue
        
        return {
            "target": symbol.upper(),
            "sector": sector,
            "industry": industry,
            "peer_count": len(peers),
            "comparison": comparison,
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


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
                    "period": {"type": "string", "description": "Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max", "default": "3mo"},
                    "interval": {"type": "string", "description": "Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo", "default": "1d"}
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
    # Polygon.io tools (enhanced market data)
    {
        "type": "function",
        "function": {
            "name": "polygon_get_quote",
            "description": "Get real-time stock quote with extended data from Polygon.io (requires API key)",
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
            "name": "polygon_get_aggregates",
            "description": "Get historical price aggregates/bars from Polygon.io with custom timespan",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"},
                    "timespan": {"type": "string", "enum": ["minute", "hour", "day", "week", "month"], "description": "Size of time window", "default": "day"},
                    "multiplier": {"type": "integer", "description": "Size multiplier for timespan", "default": 1},
                    "from_date": {"type": "string", "description": "Start date (YYYY-MM-DD)", "default": ""},
                    "to_date": {"type": "string", "description": "End date (YYYY-MM-DD)", "default": ""},
                    "limit": {"type": "integer", "description": "Number of results", "default": 120}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "polygon_get_ticker_news",
            "description": "Get recent news articles for a stock from Polygon.io",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"},
                    "limit": {"type": "integer", "description": "Number of articles", "default": 10}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "polygon_market_status",
            "description": "Get current market status (open/closed) from Polygon.io",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    # Chart generation tools
    {
        "type": "function",
        "function": {
            "name": "generate_stock_chart",
            "description": "Generate a stock price chart (candlestick, line, or technical) with optional indicators. Returns file path where chart is saved.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol (e.g., AAPL, NVDA)"},
                    "period": {"type": "string", "description": "Time period: 1mo, 3mo, 6mo, 1y, 2y, 5y", "default": "6mo"},
                    "chart_type": {"type": "string", "enum": ["candlestick", "line", "technical"], "description": "Type of chart", "default": "candlestick"},
                    "show_volume": {"type": "boolean", "description": "Show volume bars", "default": True},
                    "show_indicators": {"type": "boolean", "description": "Show moving averages/indicators", "default": True}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_comparison_chart",
            "description": "Generate a comparison chart showing multiple stocks' performance over time",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbols": {"type": "array", "items": {"type": "string"}, "description": "List of stock symbols to compare"},
                    "period": {"type": "string", "description": "Time period for comparison", "default": "1y"},
                    "normalize": {"type": "boolean", "description": "Normalize to percentage returns", "default": True}
                },
                "required": ["symbols"]
            }
        }
    },
    # Advanced analysis tools
    {
        "type": "function",
        "function": {
            "name": "get_valuation_metrics",
            "description": "Get comprehensive valuation metrics (P/E, P/B, PEG, EV/EBITDA) with assessment",
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
            "name": "get_risk_metrics",
            "description": "Calculate risk metrics: volatility, VaR, max drawdown, Sharpe, Sortino, Beta, Alpha",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"},
                    "period": {"type": "string", "description": "Analysis period (1y, 2y, 5y)", "default": "1y"}
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_earnings_analysis",
            "description": "Get earnings analysis: EPS, upcoming dates, quarterly history, growth",
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
            "name": "get_dividend_analysis",
            "description": "Get dividend analysis: yield, payout ratio, ex-date, dividend history and growth",
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
            "name": "get_options_summary",
            "description": "Get options chain summary: put/call ratio, implied volatility, ATM options",
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
            "name": "get_peer_comparison",
            "description": "Compare a stock with its industry peers on key metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock ticker symbol"}
                },
                "required": ["symbol"]
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
    # Polygon.io
    "polygon_get_quote": polygon_get_quote,
    "polygon_get_aggregates": polygon_get_aggregates,
    "polygon_get_ticker_news": polygon_get_ticker_news,
    "polygon_market_status": polygon_market_status,
    # Chart generation
    "generate_stock_chart": generate_stock_chart,
    "generate_comparison_chart": generate_comparison_chart,
    # Advanced analysis
    "get_valuation_metrics": get_valuation_metrics,
    "get_risk_metrics": get_risk_metrics,
    "get_earnings_analysis": get_earnings_analysis,
    "get_dividend_analysis": get_dividend_analysis,
    "get_options_summary": get_options_summary,
    "get_peer_comparison": get_peer_comparison,
}


def execute_tool(name: str, args: dict) -> Any:
    """Execute a tool by name with error handling."""
    func = TOOL_FUNCTIONS.get(name)
    if func:
        try:
            return func(**args)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}", "error_code": 1000}
    return {"error": f"Unknown tool: {name}", "error_code": 1001}
