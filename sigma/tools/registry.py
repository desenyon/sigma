"""Typed tool registry with execution metrics and progress tracking."""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel
import inspect
import asyncio
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """Result of a tool execution with timing metrics."""
    name: str
    success: bool
    duration_ms: float
    result: Any
    error: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ToolDefinition(BaseModel):
    """Definition of a registered tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    func: Callable
    enabled: bool = True
    provider: str = "internal"
    
    class Config:
        arbitrary_types_allowed = True


class ToolRegistry:
    """Registry for tools with execution tracking and batch support."""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._execution_history: List[ToolExecutionResult] = []
        self._max_history = 100
        self._progress_callback: Optional[Callable] = None

    def register(self, name: str, description: str, provider: str = "internal"):
        """Decorator to register a tool function."""
        def decorator(func):
            sig = inspect.signature(func)
            params = {}
            required = []
            
            for pname, p in sig.parameters.items():
                if pname == "self":
                    continue
                    
                p_type = "string"
                p_desc = ""
                
                if p.annotation == int:
                    p_type = "integer"
                elif p.annotation == float:
                    p_type = "number"
                elif p.annotation == bool:
                    p_type = "boolean"
                elif hasattr(p.annotation, "__origin__"):
                    if p.annotation.__origin__ == list:
                        p_type = "array"
                
                params[pname] = {"type": p_type}
                if p_desc:
                    params[pname]["description"] = p_desc
                    
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
        """Get a tool definition by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """List all enabled tools."""
        return [t for t in self._tools.values() if t.enabled]
    
    def get_tool_names(self) -> List[str]:
        """Get names of all enabled tools."""
        return [t.name for t in self.list_tools()]

    def to_llm_format(self) -> List[Dict[str, Any]]:
        """Convert tools to LLM-compatible format with thought signature."""
        tools_list = []
        for t in self.list_tools():
            import copy
            schema = copy.deepcopy(t.input_schema)
            
            if "properties" in schema:
                schema["properties"]["thought_signature"] = {
                    "type": "string", 
                    "description": "Internal reasoning for why this tool is being called. MUST be provided."
                }
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
        """Execute a tool and track metrics."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool {name} not found")
        
        clean_args = {k: v for k, v in args.items() 
                      if k not in ("thought", "thought_signature")}
        
        start_time = time.time()
        error = None
        result = None
        
        try:
            if inspect.iscoroutinefunction(tool.func):
                result = await tool.func(**clean_args)
            else:
                result = await asyncio.to_thread(tool.func, **clean_args)
        except Exception as e:
            error = str(e)
            logger.error(f"Tool {name} failed: {e}")
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            execution = ToolExecutionResult(
                name=name,
                success=error is None,
                duration_ms=duration_ms,
                result=result if error is None else None,
                error=error,
                args=clean_args
            )
            self._record_execution(execution)
            
        return result
    
    async def execute_batch(
        self, 
        calls: List[Dict[str, Any]], 
        on_progress: Optional[Callable[[str, bool, float], None]] = None
    ) -> List[ToolExecutionResult]:
        """Execute multiple tool calls in parallel with progress tracking.
        
        Args:
            calls: List of dicts with 'name' and 'args' keys
            on_progress: Optional callback(tool_name, success, duration_ms) for each completion
            
        Returns:
            List of ToolExecutionResult in the same order as input calls
        """
        
        async def execute_one(call: Dict[str, Any]) -> ToolExecutionResult:
            name = call["name"]
            args = call.get("args", {})
            start_time = time.time()
            
            try:
                result = await self.execute(name, args)
                duration_ms = (time.time() - start_time) * 1000
                
                execution = ToolExecutionResult(
                    name=name,
                    success=True,
                    duration_ms=duration_ms,
                    result=result,
                    args=args
                )
                
                if on_progress:
                    try:
                        on_progress(name, True, duration_ms)
                    except Exception:
                        pass
                        
                return execution
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                execution = ToolExecutionResult(
                    name=name,
                    success=False,
                    duration_ms=duration_ms,
                    result=None,
                    error=str(e),
                    args=args
                )
                
                if on_progress:
                    try:
                        on_progress(name, False, duration_ms)
                    except Exception:
                        pass
                        
                return execution
        
        results = await asyncio.gather(*[execute_one(c) for c in calls])
        return list(results)
    
    async def execute_with_retry(
        self, 
        name: str, 
        args: Dict[str, Any],
        max_retries: int = 2,
        retry_delay: float = 0.5
    ) -> Any:
        """Execute a tool with automatic retry on failure."""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.execute(name, args)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    logger.info(f"Retrying {name} (attempt {attempt + 2}/{max_retries + 1})")
                    
        raise last_error
    
    def _record_execution(self, execution: ToolExecutionResult):
        """Record an execution in history."""
        self._execution_history.append(execution)
        
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        if not self._execution_history:
            return {"total": 0, "success_rate": 0, "avg_duration_ms": 0}
            
        total = len(self._execution_history)
        successes = sum(1 for e in self._execution_history if e.success)
        avg_duration = sum(e.duration_ms for e in self._execution_history) / total
        
        by_tool: Dict[str, Dict[str, Any]] = {}
        for e in self._execution_history:
            if e.name not in by_tool:
                by_tool[e.name] = {"calls": 0, "successes": 0, "total_ms": 0}
            by_tool[e.name]["calls"] += 1
            by_tool[e.name]["total_ms"] += e.duration_ms
            if e.success:
                by_tool[e.name]["successes"] += 1
        
        for name, stats in by_tool.items():
            stats["success_rate"] = stats["successes"] / stats["calls"] if stats["calls"] else 0
            stats["avg_ms"] = stats["total_ms"] / stats["calls"] if stats["calls"] else 0
        
        return {
            "total": total,
            "success_rate": successes / total if total else 0,
            "avg_duration_ms": avg_duration,
            "by_tool": by_tool
        }
    
    def get_recent_executions(self, limit: int = 10) -> List[ToolExecutionResult]:
        """Get recent execution history."""
        return self._execution_history[-limit:]
    
    def clear_history(self):
        """Clear execution history."""
        self._execution_history = []


TOOL_REGISTRY = ToolRegistry()
