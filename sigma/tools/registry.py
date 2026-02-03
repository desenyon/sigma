from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel
import inspect

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    func: Callable
    enabled: bool = True
    provider: str = "internal" # yfinance, polygon, etc.

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, provider: str = "internal"):
        def decorator(func):
            # Extract schema from type hints (simplified)
            # In a real impl, utilize pydantic.TypeAdapter or similar if args are models.
            # Here we assume simple args or we use a manual schema if provided?
            # For now, let's keep it simple: no schema auto-extraction in this snippet 
            # unless we implement a Schema generator.
            # But the prompt says "typed tool registry... input_schema (pydantic)".
            
            # minimal schema generation
            sig = inspect.signature(func)
            params = {}
            required = []
            for pname, p in sig.parameters.items():
                if pname == "self": continue
                p_type = "string"
                if p.annotation == int: p_type = "integer"
                if p.annotation == float: p_type = "number"
                if p.annotation == bool: p_type = "boolean"
                
                params[pname] = {"type": p_type}
                if p.default == inspect.Parameter.empty:
                    required.append(pname)
            
            schema = {
                "type": "object",
                "properties": params,
                "required": required
            }
            
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                input_schema=schema,
                func=func,
                provider=provider
            )
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return [t for t in self._tools.values() if t.enabled]

    def to_llm_format(self) -> List[Dict[str, Any]]:
        tools_list = []
        for t in self.list_tools():
            # Clone schema to avoid mutating original
            import copy
            schema = copy.deepcopy(t.input_schema)
            
            # Inject thought parameter for Gemini/HackClub compatibility
            # Some providers like Gemini via proxies require a "thought" field in tool calls
            if "properties" in schema:
                schema["properties"]["thought_signature"] = {
                    "type": "string", 
                    "description": "Internal reasoning for why this tool is being called. MUST be provided."
                }
                # Force model to use it
                if "required" in schema and isinstance(schema["required"], list):
                    schema["required"].append("thought_signature")
                else:
                    schema["required"] = ["thought_signature"]
                
            tools_list.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": schema
                }
            })
        return tools_list

    async def execute(self, name: str, args: Dict[str, Any]) -> Any:
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool {name} not found")
        
        # Remove provider-specific fields if present
        args.pop("thought", None)
        args.pop("thought_signature", None)
        
        if inspect.iscoroutinefunction(tool.func):
            return await tool.func(**args)
        else:
            return tool.func(**args)

TOOL_REGISTRY = ToolRegistry()
