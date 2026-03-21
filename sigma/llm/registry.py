from typing import Dict, List, Optional
from pydantic import BaseModel

class ModelInfo(BaseModel):
    provider: str
    model_id: str
    capabilities: List[str] = [] # "vision", "tools", "json", "reasoning"
    context_window: int = 4096
    cost_tier: str = "paid" # "free", "low", "high"

class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, ModelInfo] = {}
        
        # Seed with known models (2026-tier ids for provider routing)
        self.register("gpt-5.4", "openai", ["tools", "json", "vision", "reasoning"], 256000, "high")
        self.register("gpt-5.2", "openai", ["tools", "json", "vision", "reasoning"], 256000, "high")
        self.register("gpt-5-mini", "openai", ["tools", "json", "vision"], 256000, "low")
        self.register("o3-preview", "openai", ["reasoning", "tools"], 256000, "high")
        
        self.register("claude-opus-4-6", "anthropic", ["tools", "vision", "reasoning"], 200000, "high")
        self.register("claude-sonnet-4-6", "anthropic", ["tools", "vision", "reasoning"], 200000, "high")
        
        self.register("gemini-3.1-pro", "google", ["tools", "vision", "json", "reasoning"], 1000000, "high")
        self.register("gemini-3-flash", "google", ["tools", "vision", "json"], 1000000, "free")

        self.register("grok-4", "xai", ["tools", "json"], 256000, "high")
        
        # Ollama models will be dynamic, but we can register defaults
        self.register("qwen3.5:8b", "ollama", ["tools"], 128000, "free")
        self.register("llama3.3", "ollama", ["tools"], 128000, "free")
        self.register("mistral", "ollama", ["tools"], 32000, "free")
        self.register("deepseek-r1", "ollama", ["reasoning", "tools"], 128000, "free")

    def register(self, model_id: str, provider: str, capabilities: List[str], context_window: int, cost_tier: str):
        self._models[model_id] = ModelInfo(
            provider=provider,
            model_id=model_id,
            capabilities=capabilities,
            context_window=context_window,
            cost_tier=cost_tier
        )

    def get_provider(self, model_id: str) -> str:
        if model_id in self._models:
            return self._models[model_id].provider
        # Fallback heuristics
        if model_id.startswith("gpt"): return "openai"
        if model_id.startswith("o3"): return "openai"
        if model_id.startswith("claude"): return "anthropic"
        if model_id.startswith("gemini"): return "google"
        if model_id.startswith("grok"): return "xai"
        return "ollama"

    def list_models(self) -> List[ModelInfo]:
        return list(self._models.values())
    
    def find_best_model(self, provider: Optional[str] = None, capability: Optional[str] = None) -> Optional[str]:
        # Simple selection logic
        candidates = self._models.values()
        if provider:
            candidates = [m for m in candidates if m.provider == provider]
        if capability:
            candidates = [m for m in candidates if capability in m.capabilities]
            
        # Sort by "newest" implies preference order. 
        # For now return first match.
        if candidates:
            return list(candidates)[0].model_id
        return None

REGISTRY = ModelRegistry()
