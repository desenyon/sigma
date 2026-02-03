from typing import Any, Callable, Dict, List, Optional, Union, AsyncIterator
import logging

from .providers.base import BaseLLM
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.google_provider import GoogleProvider
from .providers.ollama_provider import OllamaProvider
from .providers.sigma_cloud_provider import SigmaCloudProvider
from .registry import REGISTRY
from .rate_limit import RateLimiter

logger = logging.getLogger(__name__)

class LLMRouter:
    def __init__(self, settings):
        self.settings = settings
        self.providers: Dict[str, BaseLLM] = {}
        
        # Initialize providers based on settings
        self._init_providers()
        
    def _init_providers(self):
        # Sigma Cloud (Default)
        # Always available due to embedded key fallback in the provider itself
        self.providers["sigma_cloud"] = SigmaCloudProvider(
            api_key=self.settings.sigma_cloud_api_key,
            rate_limiter=RateLimiter(60, 0.5)
        )

        # OpenAI
        if self.settings.openai_api_key:
            self.providers["openai"] = OpenAIProvider(
                api_key=self.settings.openai_api_key,
                rate_limiter=RateLimiter(60, 0.2)
            )
            
        # Anthropic
        if self.settings.anthropic_api_key:
            self.providers["anthropic"] = AnthropicProvider(
                api_key=self.settings.anthropic_api_key,
                rate_limiter=RateLimiter(40, 0.5)
            )
            
        # Google
        if self.settings.google_api_key:
            self.providers["google"] = GoogleProvider(
                api_key=self.settings.google_api_key,
                rate_limiter=RateLimiter(60, 0.2)
            )
            
        # Ollama (always available usually)
        self.providers["ollama"] = OllamaProvider(
            base_url=getattr(self.settings, "ollama_url", "http://localhost:11434"),
            rate_limiter=RateLimiter(100, 0.01)
        )

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        on_tool_call: Optional[Callable] = None,
        stream: bool = True,
        json_mode: bool = False,
        provider: Optional[str] = None
    ) -> Union[str, AsyncIterator[str]]:
        
        # Determine model and provider
        selected_model = model or self.settings.default_model
        selected_provider = provider
        
        if not selected_provider:
            selected_provider = REGISTRY.get_provider(selected_model)
        
        # Get client
        client = self.providers.get(selected_provider)
        if not client:
             # Fallback logic
             if "ollama" in self.providers:
                 logger.warning(f"Provider {selected_provider} not available, falling back to Ollama")
                 client = self.providers["ollama"]
                 # Find a fallback model?
                 selected_model = self.settings.default_fallback_model or "llama3.2"
             else:
                 raise ValueError(f"Provider {selected_provider} not configured and no fallback available.")
        
        # Execute
        try:
            return await client.generate(
                messages=messages,
                model=selected_model,
                tools=tools,
                on_tool_call=on_tool_call,
                stream=stream,
                json_mode=json_mode
            )
        except Exception as e:
            logger.error(f"Error generation with {selected_provider}/{selected_model}: {e}")
            # Circuit breaker / fallback could go here
            if selected_provider != "ollama" and "ollama" in self.providers:
                 logger.info("Falling back to Ollama due to error")
                 return await self.providers["ollama"].generate(
                     messages=messages,
                     model="llama3.2", # Hardcoded fallback
                     tools=tools,
                     on_tool_call=on_tool_call,
                     stream=stream,
                     json_mode=json_mode
                 )
            raise

_router_instance: Optional[LLMRouter] = None

def get_router(settings: Any = None) -> LLMRouter:
    global _router_instance
    if not _router_instance:
        if settings:
            _router_instance = LLMRouter(settings)
        else:
            raise RuntimeError("LLM Router not initialized and no settings provided")
    return _router_instance
