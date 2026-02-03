from typing import Any, Dict
from .registry import TOOL_REGISTRY, ToolDefinition
from .library import TOOLS, TOOL_FUNCTIONS

def register_legacy_tools():
    """Import tools from the legacy library defined in library.py"""
    
    # Map from TOOLS list (which has schema) to TOOL_FUNCTIONS (which has implementation)
    
    for tool_def in TOOLS:
        if tool_def["type"] != "function": continue
        
        func_def = tool_def["function"]
        name = func_def["name"]
        description = func_def.get("description", "")
        parameters = func_def.get("parameters", {})
        
        func = TOOL_FUNCTIONS.get(name)
        if not func:
            continue
            
        # Determine provider based on name prefix or guess
        provider = "yfinance"
        if name.startswith("polygon"): provider = "polygon"
        if name.startswith("alpha"): provider = "alpha_vantage" 
        # etc...
        
        # Register manually to bypass decorator
        TOOL_REGISTRY._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=parameters,
            func=func,
            provider=provider
        )

# Run registration
register_legacy_tools()
