
"""Alpha Vantage tool for Sigma."""

import os
import httpx
from typing import Dict, Any, Optional
from .registry import TOOL_REGISTRY

ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"

@TOOL_REGISTRY.register(
    name="get_alpha_vantage_data",
    description="Fetch data from Alpha Vantage (TIME_SERIES_DAILY, OVERVIEW, SENTIMENT, EARNINGS).",
    provider="alpha_vantage"
)
async def get_alpha_vantage_data(function: str, symbol: str, interval: str = "daily") -> Dict[str, Any]:
    """
    Fetch data from Alpha Vantage.
    
    Args:
        function: API function (e.g. TIME_SERIES_DAILY, OVERVIEW, NEWS_SENTIMENT, EARNINGS)
        symbol: Stock symbol (e.g. AAPL)
        interval: Interval for time series (optional)
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return {"error": "ALPHA_VANTAGE_API_KEY not found in environment variables."}

    params = {
        "function": function,
        "symbol": symbol,
        "apikey": api_key
    }
    
    if function == "TIME_SERIES_INTRADAY":
        params["interval"] = interval
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(ALPHA_VANTAGE_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data:
                return {"error": data["Error Message"]}
            if "Note" in data:
                return {"warning": "API limit reached or other note", "data": data}
                
            return data
        except Exception as e:
            return {"error": str(e)}
