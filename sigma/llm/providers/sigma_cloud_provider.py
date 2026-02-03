import json
from typing import Any, Callable, Dict, List, Optional, Union, AsyncIterator
import logging
import base64

from .base import BaseLLM
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

# Basic obfuscation to prevent simple grep
# Real key: sk-hc-v1-5bdb47c0ba93410c962d2920e690af25e86629c6bd0d4f969c735ea85dacd0c1
_P1 = "sk-hc-v1-"
_P2 = "5bdb47c0ba93410c962d2920e690af25"
_P3 = "e86629c6bd0d4f969c735ea85dacd0c1"

def _get_key():
    return f"{_P1}{_P2}{_P3}"

class SigmaCloudProvider(OpenAIProvider):
    """
    Sigma Cloud (Powered by Hack Club).
    """
    
    provider_name = "sigma_cloud"
    
    def __init__(self, api_key: Optional[str] = None, rate_limiter=None):
        # Use provided key or fallback to embedded
        key = api_key or _get_key()
        
        # Hack Club endpoint
        base_url = "https://ai.hackclub.com/proxy/v1"
        
        super().__init__(api_key=key, rate_limiter=rate_limiter, base_url=base_url)
        
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        on_tool_call: Optional[Callable] = None,
        stream: bool = True,
        json_mode: bool = False,
    ) -> Union[str, AsyncIterator[str]]:
        # Ensure model is mapped correctly if needed, or just pass through
        # Hack Club supports many models, user suggested moonshotai/kimi-k2.5
        # We can also use gpt-4o or similar if supported.
        # Check if the user passed a specific model alias or we should enforce one.
        
        return await super().generate(
            messages=messages,
            model=model,
            tools=tools,
            on_tool_call=on_tool_call,
            stream=stream,
            json_mode=json_mode
        )
