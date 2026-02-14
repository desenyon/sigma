"""Formatting utilities for tool outputs."""
import json
import pandas as pd
from typing import Any, Dict, List, Union

def format_tool_result(result: Any) -> str:
    """Format tool result for display in TUI."""
    if isinstance(result, (dict, list)):
        try:
            # Handle Backtest Results
            if isinstance(result, dict) and "metrics" in result and "strategy" in result:
                metrics = result["metrics"]
                lines = [
                    f"### Backtest Results: {result.get('strategy', 'Unknown Strategy')}",
                    f"**Symbol**: {result.get('symbol', 'N/A')}",
                    "",
                    "| Metric | Value |",
                    "| :--- | :--- |",
                    f"| Total Return | {metrics.get('total_return_pct', 0):.2f}% |",
                    f"| CAGR | {metrics.get('cagr', 0):.2f}% |",
                    f"| Sharpe Ratio | {metrics.get('sharpe_ratio', 0):.2f} |",
                    f"| Max Drawdown | {metrics.get('max_drawdown', 0):.2f}% |",
                    f"| Win Rate | {metrics.get('win_rate', 0):.2f}% |",
                    f"| Trades | {metrics.get('total_trades', 0)} |",
                ]
                return "\n".join(lines)

            # Check for common financial structures
            if isinstance(result, dict) and "price" in result:
                return f"${result['price']}"
            
            if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
                # Maybe a list of quotes or candles
                if "symbol" in result[0] and "price" in result[0]:
                    items = [f"{i['symbol']}: ${i['price']}" for i in result[:3]]
                    if len(result) > 3:
                        items.append(f"... (+{len(result)-3} more)")
                    return ", ".join(items)

            # Default pretty print
            return json.dumps(result, indent=2, default=str)
        except Exception:
            return str(result)
            
    if isinstance(result, pd.DataFrame):
        return result.to_markdown()
        
    return str(result)
