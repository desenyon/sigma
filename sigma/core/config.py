"""Configuration for Sigma."""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    XAI = "xai"
    GROQ = "groq"


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # App
    app_name: str = "Sigma"
    debug: bool = False
    
    # LLM
    default_provider: LLMProvider = LLMProvider.GOOGLE
    
    # API Keys
    openai_api_key: Optional[SecretStr] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[SecretStr] = Field(default=None, alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[SecretStr] = Field(default=None, alias="GOOGLE_API_KEY")
    xai_api_key: Optional[SecretStr] = Field(default=None, alias="XAI_API_KEY")
    groq_api_key: Optional[SecretStr] = Field(default=None, alias="GROQ_API_KEY")
    
    # Models
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-sonnet-4-20250514"
    google_model: str = "gemini-2.0-flash"
    ollama_model: str = "llama3.2"
    xai_model: str = "grok-beta"
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Ollama
    ollama_base_url: str = "http://127.0.0.1:11434"
    
    # Search
    exa_api_key: Optional[SecretStr] = Field(default=None, alias="EXASEARCH_API_KEY")
    tavily_api_key: Optional[SecretStr] = Field(default=None, alias="TAVILY_API_KEY")
    serper_api_key: Optional[SecretStr] = Field(default=None, alias="SERPER_API_KEY")
    
    # Financial
    financial_datasets_api_key: Optional[SecretStr] = Field(default=None, alias="FINANCIAL_DATASETS_API_KEY")
    fmp_api_key: Optional[SecretStr] = Field(default=None, alias="FMP_API_KEY")
    polygon_api_key: Optional[SecretStr] = Field(default=None, alias="POLYGON_API_KEY")
    alpha_vantage_api_key: Optional[SecretStr] = Field(default=None, alias="ALPHA_VANTAGE_API_KEY")
    
    # Agent
    max_iterations: int = 25
    max_tokens: int = 8192
    temperature: float = 0.1
    
    # Storage
    cache_dir: Path = Path.home() / ".sigma" / "cache"
    db_path: Path = Path.home() / ".sigma" / "sigma.db"
    
    def get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """Get API key for provider."""
        keys = {
            LLMProvider.OPENAI: self.openai_api_key,
            LLMProvider.ANTHROPIC: self.anthropic_api_key,
            LLMProvider.GOOGLE: self.google_api_key,
            LLMProvider.XAI: self.xai_api_key,
            LLMProvider.GROQ: self.groq_api_key,
        }
        key = keys.get(provider)
        return key.get_secret_value() if key else None
    
    def get_model(self, provider: Optional[LLMProvider] = None) -> str:
        """Get model for provider."""
        provider = provider or self.default_provider
        models = {
            LLMProvider.OPENAI: self.openai_model,
            LLMProvider.ANTHROPIC: self.anthropic_model,
            LLMProvider.GOOGLE: self.google_model,
            LLMProvider.OLLAMA: self.ollama_model,
            LLMProvider.XAI: self.xai_model,
            LLMProvider.GROQ: self.groq_model,
        }
        return models.get(provider, self.google_model)
    
    def get_available_providers(self) -> list[LLMProvider]:
        """Get providers with API keys."""
        available = []
        for p in LLMProvider:
            if p == LLMProvider.OLLAMA:
                available.append(p)
            elif self.get_api_key(p):
                available.append(p)
        return available


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
