from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from .intent import IntentParser
from ..utils.extraction import extract_tickers, extract_timeframe

class Request(BaseModel):
    action: str
    tickers: List[str]
    timeframe: str
    output_mode: str = "report" # report, memo, quant, summary, etc.
    original_query: str
    is_command: bool = False
    details: Dict[str, Any] = {}

class CommandRouter:
    def __init__(self):
        self.intent_parser = IntentParser()
        
    def parse(self, query: str) -> Request:
        stripped = query.strip()
        
        # Explicit commands
        if stripped.startswith("/"):
            parts = stripped.split(maxsplit=1)
            cmd = parts[0][1:].lower() # remove /
            args = parts[1] if len(parts) > 1 else ""
            
            # Map commands to standard request structures
            if cmd == "backtest":
                 tickers = extract_tickers(args)
                 return Request(
                     action="backtest",
                     tickers=tickers,
                     timeframe="default",
                     output_mode="quant",
                     original_query=query,
                     is_command=True
                 )
            elif cmd == "chart":
                 tickers = extract_tickers(args)
                 return Request(
                     action="chart",
                     tickers=tickers,
                     timeframe="default",
                     output_mode="chart",
                     original_query=query,
                     is_command=True
                 )
            elif cmd == "model":
                 # Handled by UI/Engine specifically to switch model?
                 return Request(
                     action="config_model",
                     tickers=[],
                     timeframe="",
                     output_mode="system",
                     original_query=query,
                     is_command=True,
                     details={"model": args.strip()}
                 )
            elif cmd == "setup":
                 return Request(action="setup", tickers=[], timeframe="", output_mode="system", original_query=query, is_command=True)
                 
        # Natural Language
        tickers = extract_tickers(query)
        tf_desc, start, end = extract_timeframe(query)
        
        # Simple heuristic for output mode
        output_mode = "report"
        if "memo" in query.lower(): output_mode = "memo"
        if "summary" in query.lower(): output_mode = "summary"
        if "backtest" in query.lower() or "quant" in query.lower(): output_mode = "quant"
        
        # Use existing IntentParser for heavier lifting if needed
        # But Request object normalizes it for Engine
        # Here we just do extraction logic
        
        # Intent parser might give us plan, but we want a unified Request struct first?
        # Actually Engine uses IntentParser.
        # Let's wrap IntentParsing into "action" determination.
        
        plan = self.intent_parser.parse(query)
        action = plan.deliverable if plan else "analysis"
        
        return Request(
            action=action,
            tickers=tickers,
            timeframe=tf_desc,
            output_mode=output_mode,
            original_query=query,
            is_command=False,
            details={"plan": plan}
        )
