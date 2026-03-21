#!/usr/bin/env python3
"""Verify Textual app wiring and shared UI constants for Sigma v3.7.1."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("SIGMA v3.7.1 - UI VERIFICATION")
print("=" * 60)

print("\n[1] Checking app components...")
try:
    from sigma.app import (
        AssistantMessage,
        SigmaApp,
        SUGGESTIONS,
        SYSTEM_PROMPT,
        ToolMessage,
        UserMessage,
        WELCOME_BANNER,
        __version__,
    )

    print(f"  [ok] App components imported - v{__version__}")
    print(f"  [ok] SUGGESTIONS: {len(SUGGESTIONS)} items")
    print(f"  [ok] SYSTEM_PROMPT length: {len(SYSTEM_PROMPT)} chars")
    assert "3.7.1" in WELCOME_BANNER
except ImportError as e:
    print(f"  [FAIL] Import error: {e}")
    sys.exit(1)

print("\n[2] Checking tool registry...")
try:
    from sigma.tools.registry import TOOL_REGISTRY, ToolDefinition, ToolExecutionResult

    print("  [ok] Tool registry imported")
    print("  [ok] ToolExecutionResult dataclass available")

    stats = TOOL_REGISTRY.get_execution_stats()
    print(f"  [ok] Execution stats: {stats['total']} recorded calls")
except ImportError as e:
    print(f"  [FAIL] Import error: {e}")
    sys.exit(1)

print("\n[3] Checking state management...")
try:
    from sigma.core.state import ConversationState, ConversationManager, Message, MessageRole, ToolCall

    print("  [ok] State management imported")

    state = ConversationState()
    state.add_user_message("test query")
    state.add_assistant_message("test response")

    stats = state.get_summary_stats()
    print(f"  [ok] ConversationState working: {stats['total_messages']} messages")
except ImportError as e:
    print(f"  [FAIL] Import error: {e}")
    sys.exit(1)

print("\n[4] Checking config...")
try:
    from sigma.config import AVAILABLE_MODELS, ErrorCode, SigmaError, __version__ as config_version

    print(f"  [ok] Config imported - v{config_version}")
    print(f"  [ok] Providers: {list(AVAILABLE_MODELS.keys())}")
except ImportError as e:
    print(f"  [FAIL] Import error: {e}")
    sys.exit(1)

print("\n[5] Testing real data fetch (AAPL quote)...")
try:
    from sigma.tools import get_stock_quote

    quote = get_stock_quote("AAPL")
    if "error" not in quote:
        print(f"  [ok] AAPL Quote: ${quote.get('price', 'N/A')}")
        mc = quote.get("market_cap", 0)
        print(f"  [ok] Market Cap: ${mc/1e12:.2f}T" if mc else "  Market Cap: N/A")
    else:
        print(f"  [warn] Error: {quote.get('error')}")
except Exception as e:
    print(f"  [warn] Quote fetch failed: {e}")

print("\n[6] Testing technical analysis...")
try:
    from sigma.tools import technical_analysis

    ta = technical_analysis("SPY", "1mo")
    if "error" not in ta:
        indicators = ta.get("indicators", {})
        print(f"  [ok] SPY RSI: {indicators.get('rsi', 'N/A')}")
        print(f"  [ok] SPY SMA20: {indicators.get('sma_20', 'N/A')}")
    else:
        print(f"  [warn] Error: {ta.get('error')}")
except Exception as e:
    print(f"  [warn] TA failed: {e}")

print("\n[7] Checking Textual widgets...")
ui_checks = {
    "SigmaApp has CSS": hasattr(SigmaApp, "CSS"),
    "UserMessage exists": UserMessage is not None,
    "AssistantMessage exists": AssistantMessage is not None,
    "ToolMessage exists": ToolMessage is not None,
}
for check, passed in ui_checks.items():
    status = "[ok]" if passed else "[FAIL]"
    print(f"  {status} {check}")

print("\n[8] Checking keyboard bindings...")
try:
    bindings = SigmaApp.BINDINGS
    binding_keys = [b.key if hasattr(b, "key") else b[0] for b in bindings]
    for key in ("ctrl+c", "ctrl+l"):
        if key in binding_keys:
            print(f"  [ok] {key} binding registered")
        else:
            print(f"  [FAIL] {key} binding missing")
except Exception as e:
    print(f"  [warn] Could not check bindings: {e}")

print("\n[9] Checking version consistency...")
from sigma.app import __version__ as app_v
from sigma.config import __version__ as cfg_v

print(f"  App version: {app_v}")
print(f"  Config version: {cfg_v}")
version_match = app_v == cfg_v == "3.7.1"
print(f"  [{'ok' if version_match else 'FAIL'}] Versions {'match' if version_match else 'mismatch'}")

print("\n[10] Checking for no emojis in WELCOME_BANNER...")
emoji_pattern = re.compile(
    r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    r"\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF\u2B50\u2713\u2717"
    r"\u2714\u2716\u25CF]"
)
emojis = emoji_pattern.findall(WELCOME_BANNER)
if emojis:
    print(f"  [warn] WELCOME_BANNER contains emoji-like chars: {emojis[:3]}")
else:
    print("  [ok] WELCOME_BANNER - no emojis")

print("\n" + "=" * 60)
print("[OK] UI verification complete")
print("=" * 60)
print("\nLaunch:  python -m sigma")
print("TUI:     Ctrl+C quit, Ctrl+L clear chat")
