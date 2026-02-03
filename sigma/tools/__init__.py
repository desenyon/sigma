from .registry import TOOL_REGISTRY, ToolDefinition
from .adapter import register_legacy_tools
from .library import *

# Ensure legacy tools are registered
register_legacy_tools()

# Expose execute_tool for backward compatibility if needed, using the registry
def execute_tool(name: str, args: dict):
    # Registry doesn't have sync execute exposed directly? 
    # But library functions are sync.
    # Check definition.
    tool = TOOL_REGISTRY.get_tool(name)
    if tool:
        try:
            return tool.func(**args)
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Tool not found"}

# Helpers
def get_tools_for_llm():
    return TOOL_REGISTRY.to_llm_format()
