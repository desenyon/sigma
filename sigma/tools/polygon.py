
"""Polygon.io tool for Sigma."""

import os
import httpx
from typing import Dict, Any, List, Optional
from .registry import TOOL_REGISTRY

POLYGON_BASE_URL = "https://api.polygon.io"

@TOOL_REGISTRY.register(
    name="get_polygon_aggregates",
    description="Fetch aggregate bars (candles) for a stock.",
    provider="polygon"
)
async def get_polygon_aggregates(
    ticker: str,
    multiplier: int = 1,
    timespan: str = "day",
    from_date: str = "",
    to_date: str = "",
    adjusted: bool = True
) -> Dict[str, Any]:
    """
    Get aggregate bars for a stock.
    
    Args:
        ticker: The ticker symbol (e.g. AAPL)
        multiplier: The size of the timespan multiplier (e.g. 1)
        timespan: The size of the time window (minute, hour, day, week, month, quarter, year)
        from_date: The start of the aggregate time window (YYYY-MM-DD)
        to_date: The end of the aggregate time window (YYYY-MM-DD)
        adjusted: Whether to return adjusted results (default: true)
    """
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        return {"error": "POLYGON_API_KEY not found in environment variables."}

    # Default dates if not provided
    from datetime import datetime, timedelta
    if not to_date:
        to_date = datetime.now().strftime("%Y-%m-%d")
    if not from_date:
        from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    url = f"{POLYGON_BASE_URL}/v2/aggs/ticker/{ticker.upper()}/range/{multiplier}/{timespan}/{from_date}/{to_date}"
    
    params = {
        "adjusted": str(adjusted).lower(),
        "apiKey": api_key,
        "limit": 50000
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

@TOOL_REGISTRY.register(
    name="get_polygon_news",
    description="Fetch ticker news from Polygon.io.",
    provider="polygon"
)
async def get_polygon_news(
    ticker: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get news articles for a ticker.
    
    Args:
        ticker: The ticker symbol (e.g. AAPL)
        limit: Number of results (default: 10)
    """
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        return {"error": "POLYGON_API_KEY not found in environment variables."}

    url = f"{POLYGON_BASE_URL}/v2/reference/news"
    
    params = {
        "ticker": ticker.upper(),
        "limit": limit,
        "apiKey": api_key
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

@TOOL_REGISTRY.register(
    name="get_polygon_snapshot",
    description="Get current snapshot (price, change, etc.) for a ticker.",
    provider="polygon"
)
async def get_polygon_snapshot(ticker: str) -> Dict[str, Any]:
    """
    Get a snapshot of a single ticker.
    
    Args:
        ticker: The ticker symbol (e.g. AAPL)
    """
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        return {"error": "POLYGON_API_KEY not found in environment variables."}

    url = f"{POLYGON_BASE_URL}/v2/snapshot/locale/us/markets/stocks/tickers/{ticker.upper()}"
    
    params = {
        "apiKey": api_key
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
