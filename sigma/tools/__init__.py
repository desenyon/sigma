from sigma.config import ErrorCode

from .adapter import register_legacy_tools
from .library import *
from .library import _get_polygon_key
from .registry import TOOL_REGISTRY, ToolDefinition, filter_args_for_tool

# Ensure legacy tools are registered
register_legacy_tools()


def execute_tool(name: str, args: dict):
    """Synchronous tool execution with stable error shape for CLI and tests."""
    tool = TOOL_REGISTRY.get_tool(name)
    if tool:
        try:
            return tool.func(**filter_args_for_tool(tool.func, args))
        except Exception as e:
            return {
                "error": str(e),
                "error_code": int(ErrorCode.REQUEST_FAILED),
            }
    return {
        "error": "Tool not found",
        "error_code": int(ErrorCode.UNKNOWN_ERROR),
    }

# Helpers
def get_tools_for_llm():
    return TOOL_REGISTRY.to_llm_format()
