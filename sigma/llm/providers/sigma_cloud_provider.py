import json
from typing import Any, Callable, Dict, List, Optional, Union, AsyncIterator
import logging

from .base import BaseLLM
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class SigmaCloudProvider(OpenAIProvider):
    """
    Sigma Cloud (Powered by Hack Club).
    
    Requires SIGMA_CLOUD_API_KEY to be configured via:
    - Environment variable: SIGMA_CLOUD_API_KEY
    - Config file: ~/.sigma/config.env
    - Setup wizard: sigma-setup
    """
    
    provider_name = "sigma_cloud"
    
    def __init__(self, api_key: Optional[str] = None, rate_limiter=None):
        if not api_key:
            raise ValueError(
                "Sigma Cloud API key required. Configure via:\n"
                "  1. Run 'sigma-setup' to configure keys\n"
                "  2. Set SIGMA_CLOUD_API_KEY environment variable\n"
                "  3. Add to ~/.sigma/config.env\n"
                "Get your key at: https://hackclub.com/api"
            )
        key = api_key
        
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
