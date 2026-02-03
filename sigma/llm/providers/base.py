from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union
from ..rate_limit import RateLimiter

class BaseLLM(ABC):
    """Base class for LLM clients."""
    
    provider_name: str = "base"
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        self.rate_limiter = rate_limiter
        
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        on_tool_call: Optional[Callable] = None,
        stream: bool = True,
        json_mode: bool = False,
    ) -> Union[str, Any]:
        """Generate a response."""
        pass
    
    async def _wait_for_rate_limit(self):
        """Apply rate limiting."""
        if self.rate_limiter:
            await self.rate_limiter.wait()
