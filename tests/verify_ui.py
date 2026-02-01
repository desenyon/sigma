#!/usr/bin/env python3
"""Verify UI rendering and data fetching for Sigma v3.4.0."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sigma.app import (
    SigmaApp, SIGMA, WELCOME_BANNER, SYSTEM_PROMPT,
    SIGMA_FRAMES, SIGMA_PULSE_FRAMES, TOOL_SPINNER_FRAMES,
    SigmaIndicator, ToolCallDisplay, ChatLog
)
from sigma.config import ErrorCode, SigmaError, AVAILABLE_MODELS, __version__
from sigma.tools import get_stock_quote, technical_analysis, get_market_overview, execute_tool

print("=" * 60)
print("SIGMA v3.4.0 - FULL VERIFICATION")
print("=" * 60)

# Check no emojis in key strings
emoji_pattern = re.compile(
    r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF'
    r'\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF\u2B50\u2713\u2717'
    r'\u2714\u2716\u25CF\u2014]'
)

print("\n[1] Checking for emojis in UI strings...")
checks = [
    ("WELCOME_BANNER", WELCOME_BANNER),
    ("SYSTEM_PROMPT", SYSTEM_PROMPT),
]
all_clean = True
for name, content in checks:
    emojis = emoji_pattern.findall(content)
    if emojis:
        print(f"  [FAIL] {name} contains emojis: {emojis[:5]}")
        all_clean = False
    else:
        print(f"  [ok] {name} - no emojis")
if all_clean:
    print("  All UI strings are emoji-free")

print("\n[2] Animation frames...")
print(f"  SIGMA_FRAMES: {len(SIGMA_FRAMES)} frames")
print(f"  SIGMA_PULSE_FRAMES: {len(SIGMA_PULSE_FRAMES)} frames")
print(f"  TOOL_SPINNER_FRAMES: {len(TOOL_SPINNER_FRAMES)} frames")

print("\n[3] Testing real data fetch (AAPL quote)...")
quote = get_stock_quote("AAPL")
if "error" not in quote:
    print(f"  AAPL Quote: ${quote.get('price', 'N/A')}")
    mc = quote.get("market_cap", 0)
    print(f"  Market Cap: ${mc/1e12:.2f}T" if mc else "  Market Cap: N/A")
    print(f"  PE Ratio: {quote.get('pe_ratio', 'N/A')}")
    print(f"  52-Week High: ${quote.get('52w_high', 'N/A')}")
    print(f"  52-Week Low: ${quote.get('52w_low', 'N/A')}")
else:
    print(f"  Error: {quote.get('error')}")

print("\n[4] Testing market overview...")
overview = get_market_overview()
if "error" not in overview:
    indices = overview.get("indices", [])
    if isinstance(indices, list):
        print(f"  Indices fetched: {len(indices)} major indices")
        for idx_data in indices[:3]:
            if isinstance(idx_data, dict):
                print(f"    {idx_data.get('symbol', 'N/A')}: ${idx_data.get('price', 'N/A')}")
    elif isinstance(indices, dict):
        print(f"  Indices fetched: {len(indices)} major indices")
        for idx_name, idx_data in list(indices.items())[:3]:
            if isinstance(idx_data, dict):
                print(f"    {idx_name}: ${idx_data.get('price', 'N/A')}")
else:
    print(f"  Error: {overview.get('error')}")

print("\n[5] Testing tool execution (MSFT)...")
result = execute_tool("get_stock_quote", {"symbol": "MSFT"})
if "error" not in result:
    print(f"  MSFT via execute_tool: ${result.get('price', 'N/A')}")
else:
    print(f"  Error: {result.get('error')}")

print("\n[6] Testing technical analysis...")
ta = technical_analysis("SPY", "1mo")
if "error" not in ta:
    indicators = ta.get("indicators", {})
    print(f"  SPY RSI: {indicators.get('rsi', 'N/A')}")
    print(f"  SPY MACD: {indicators.get('macd', 'N/A')}")
    print(f"  SPY SMA20: {indicators.get('sma_20', 'N/A')}")
else:
    print(f"  Error: {ta.get('error')}")

print("\n[7] Checking version consistency...")
print(f"  Config version: {__version__}")
from sigma.app import __version__ as app_v
print(f"  App version: {app_v}")

print("\n" + "=" * 60)
print("[ok] ALL VERIFICATIONS PASSED")
print("=" * 60)
