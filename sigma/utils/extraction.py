import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

COMMON_TICKERS = {
    # Ticker map for normalization if needed
    "APPLE": "AAPL",
    "GOOGLE": "GOOGL",
    "MICROSOFT": "MSFT",
    "AMAZON": "AMZN",
    "TESLA": "TSLA",
    "NVIDIA": "NVDA",
    "META": "META",
    "FACEBOOK": "META",
    "NETFLIX": "NFLX",
    "S&P 500": "SPY",
    "SP500": "SPY",
    "S&P": "SPY",
    "NASDAQ": "QQQ",
    "DOW": "DIA",
    "DOW JONES": "DIA",
    "BITCOIN": "BTC-USD",
    "ETHEREUM": "ETH-USD",
}

def extract_tickers(text: str) -> List[str]:
    """Extract and normalize tickers from text."""
    found = []
    
    # Check known names first (case insensitive bounds)
    upper_text = text.upper()
    for name, ticker in COMMON_TICKERS.items():
        # Simple word boundary check
        if re.search(r'\b' + re.escape(name) + r'\b', upper_text):
            found.append(ticker)
            
    # Regex for standard tickers (capitals, 1-5 chars)
    # Exclude common words like I, A, AM, PM, IS, AT, VS, OR, AND...
    # Strict mode: must be uppercase in original text? The prompt implies natural language which might be mixed.
    # But usually users type tickers in caps or "Apple".
    
    # For simplicity, extract probable tickers
    matches = re.findall(r'\b[A-Z]{2,5}\b', text)
    stopwords = {"AND", "OR", "THE", "FOR", "GET", "SET", "NOT", "BUT", "BY", "OF", "AT", "IN", "ON", "TO", "FROM", "VS", "GDP", "CPI", "USD", "YTD", "CEO", "CFO", "SEC", "API", "LLM", "AI"}
    
    for m in matches:
        if m not in stopwords and m not in found:
            found.append(m)
            
    return list(set(found))

def extract_timeframe(text: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Extract timeframe description, start date, end date."""
    
    today = datetime.now()
    
    # "5y", "10 years", "start of 2020"
    
    # Simple regex for periods
    match_years = re.search(r'\b(\d+)\s*y(ears?)?\b', text)
    if match_years:
        years = int(match_years.group(1))
        start_date = (today - timedelta(days=years*365)).strftime("%Y-%m-%d")
        return f"{years}y", start_date, None
        
    match_months = re.search(r'\b(\d+)\s*m(onths?)?\b', text)
    if match_months:
        months = int(match_months.group(1))
        start_date = (today - timedelta(days=months*30)).strftime("%Y-%m-%d")
        return f"{months}m", start_date, None
        
    # "Since 2021"
    match_since = re.search(r'\bsince\s+(\d{4})\b', text)
    if match_since:
        year = int(match_since.group(1))
        return f"since {year}", f"{year}-01-01", None
        
    # "YTD"
    if "YTD" in text.upper():
        start_date = f"{today.year}-01-01"
        return "YTD", start_date, None
        
    return "default", None, None
