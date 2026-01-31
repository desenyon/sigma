"""Configuration management for Sigma v3.2.0."""

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


__version__ = "3.2.0"


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    XAI = "xai"
    OLLAMA = "ollama"


# Available models per provider
AVAILABLE_MODELS = {
    "google": ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-preview", "o1-mini"],
    "anthropic": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    "xai": ["grok-2", "grok-2-mini"],
    "ollama": ["llama3.2", "llama3.1", "mistral", "codellama", "phi3"],
}

# Config directory
CONFIG_DIR = Path.home() / ".sigma"
CONFIG_FILE = CONFIG_DIR / "config.env"


class Settings(BaseSettings):
    """Application settings."""
    
    # Provider settings
    default_provider: LLMProvider = LLMProvider.GOOGLE
    default_model: str = Field(default="gemini-2.0-flash", alias="DEFAULT_MODEL")
    
    # API Keys
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    xai_api_key: Optional[str] = Field(default=None, alias="XAI_API_KEY")
    
    # Model settings
    google_model: str = "gemini-2.0-flash"
    openai_model: str = "gpt-4o"
    anthropic_model: str = "claude-sonnet-4-20250514"
    groq_model: str = "llama-3.3-70b-versatile"
    xai_model: str = "grok-2"
    ollama_model: str = "llama3.2"
    
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    
    # Data API keys
    alpha_vantage_api_key: str = "6ER128DD3NQUPTVC"  # Built-in free key
    exa_api_key: Optional[str] = None
    
    class Config:
        env_file = str(CONFIG_FILE)
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    def get_api_key(self, provider: LLMProvider) -> Optional[str]:
        """Get API key for a provider."""
        key_map = {
            LLMProvider.GOOGLE: self.google_api_key,
            LLMProvider.OPENAI: self.openai_api_key,
            LLMProvider.ANTHROPIC: self.anthropic_api_key,
            LLMProvider.GROQ: self.groq_api_key,
            LLMProvider.XAI: self.xai_api_key,
            LLMProvider.OLLAMA: None,  # No key needed
        }
        return key_map.get(provider)
    
    def get_model(self, provider: LLMProvider) -> str:
        """Get model for a provider."""
        model_map = {
            LLMProvider.GOOGLE: self.google_model,
            LLMProvider.OPENAI: self.openai_model,
            LLMProvider.ANTHROPIC: self.anthropic_model,
            LLMProvider.GROQ: self.groq_model,
            LLMProvider.XAI: self.xai_model,
            LLMProvider.OLLAMA: self.ollama_model,
        }
        return model_map.get(provider, "")
    
    def get_available_providers(self) -> list[LLMProvider]:
        """Get list of providers with configured API keys."""
        available = []
        for provider in LLMProvider:
            if provider == LLMProvider.OLLAMA:
                available.append(provider)  # Always available
            elif self.get_api_key(provider):
                available.append(provider)
        return available
    
    def is_configured(self) -> bool:
        """Check if at least one provider is configured."""
        return len(self.get_available_providers()) > 0


def get_settings() -> Settings:
    """Get application settings."""
    # Ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load from environment and config file
    return Settings()


def save_api_key(provider: str, key: str) -> None:
    """Save an API key to the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read existing config
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    config[k] = v
    
    # Update key
    key_map = {
        "google": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "groq": "GROQ_API_KEY",
        "xai": "XAI_API_KEY",
    }
    
    env_key = key_map.get(provider.lower())
    if env_key:
        config[env_key] = key
    
    # Write back
    with open(CONFIG_FILE, "w") as f:
        f.write("# Sigma Configuration\n\n")
        for k, v in sorted(config.items()):
            f.write(f"{k}={v}\n")


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider."""
    settings = get_settings()
    try:
        return settings.get_api_key(LLMProvider(provider.lower()))
    except ValueError:
        return None


def save_setting(key: str, value: str) -> None:
    """Save a setting to the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read existing config
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    config[k] = v
    
    # Map setting name to config key
    setting_map = {
        "default_provider": "DEFAULT_PROVIDER",
        "default_model": "DEFAULT_MODEL",
        "output_dir": "OUTPUT_DIR",
        "cache_enabled": "CACHE_ENABLED",
        "lean_cli_path": "LEAN_CLI_PATH",
    }
    
    config_key = setting_map.get(key, key.upper())
    config[config_key] = str(value)
    
    # Write back
    with open(CONFIG_FILE, "w") as f:
        f.write("# Sigma Configuration\n\n")
        for k, v in sorted(config.items()):
            f.write(f"{k}={v}\n")
