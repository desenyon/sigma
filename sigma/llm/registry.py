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
        
        # Seed with known models
        self.register("gpt-4o", "openai", ["tools", "json", "vision"], 128000, "high")
        self.register("gpt-4o-mini", "openai", ["tools", "json", "vision"], 128000, "low")
        self.register("o3-mini", "openai", ["reasoning", "tools"], 128000, "high")
        
        self.register("claude-3-5-sonnet-latest", "anthropic", ["tools", "vision", "reasoning"], 200000, "high")
        
        self.register("gemini-2.0-flash", "google", ["tools", "vision", "json"], 1000000, "free")
        self.register("gemini-2.0-pro-exp", "google", ["tools", "vision", "reasoning"], 2000000, "free")
        
        # Ollama models will be dynamic, but we can register defaults
        self.register("llama3.2", "ollama", ["tools"], 128000, "free")
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
        if model_id.startswith("moonshot"): return "sigma_cloud"  # Add explicit mapping for Sigma Cloud default
        if model_id.startswith("gpt"): return "openai"
        if model_id.startswith("claude"): return "anthropic"
        if model_id.startswith("gemini"): return "google"
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
