"""Configuration management for Sigma v3.3.2."""

import os
import shutil
import subprocess
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

from pydantic import Field
from pydantic_settings import BaseSettings


__version__ = "3.3.2"


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
    "google": ["gemini-3-flash-preview", "gemini-2.5-pro", "gemini-2.5-flash"],
    "openai": ["gpt-4o", "gpt-4o-mini", "o1", "o1-mini", "o3-mini"],
    "anthropic": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
    "xai": ["grok-2", "grok-2-mini"],
    "ollama": ["llama3.2", "llama3.1", "mistral", "codellama", "phi3"],
}

# Config directory
CONFIG_DIR = Path.home() / ".sigma"
CONFIG_FILE = CONFIG_DIR / "config.env"
FIRST_RUN_MARKER = CONFIG_DIR / ".first_run_complete"


def is_first_run() -> bool:
    """Check if this is the first run of the application."""
    return not FIRST_RUN_MARKER.exists()


def mark_first_run_complete() -> None:
    """Mark that the first run setup has been completed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    FIRST_RUN_MARKER.touch()


def detect_lean_installation() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Auto-detect LEAN/QuantConnect installation.
    Returns: (is_installed, cli_path, lean_directory)
    """
    lean_cli_path = None
    lean_directory = None
    
    # Check if lean CLI is available in PATH
    lean_cli = shutil.which("lean")
    if lean_cli:
        lean_cli_path = lean_cli
    
    # Check common installation paths for LEAN directory
    common_paths = [
        Path.home() / "Lean",
        Path.home() / ".lean",
        Path.home() / "QuantConnect" / "Lean",
        Path("/opt/lean"),
        Path.home() / "Projects" / "Lean",
        Path.home() / ".local" / "share" / "lean",
    ]
    
    for path in common_paths:
        if path.exists():
            # Check for LEAN directory structure
            if (path / "Launcher").exists() or (path / "Algorithm.Python").exists() or (path / "lean.json").exists():
                lean_directory = str(path)
                break
    
    # Check if lean is installed via pip (check both pip and pip3)
    if not lean_cli_path:
        for pip_cmd in ["pip3", "pip"]:
            try:
                result = subprocess.run(
                    [pip_cmd, "show", "lean"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    # Parse location from pip show output
                    for line in result.stdout.split("\n"):
                        if line.startswith("Location:"):
                            # lean is installed via pip
                            lean_cli_path = "lean"
                            break
                    if lean_cli_path:
                        break
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                continue
    
    # Also check if lean command works directly
    if not lean_cli_path:
        try:
            result = subprocess.run(
                ["lean", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lean_cli_path = "lean"
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
    
    is_installed = lean_cli_path is not None or lean_directory is not None
    return is_installed, lean_cli_path, lean_directory


async def install_lean_cli() -> Tuple[bool, str]:
    """
    Install LEAN CLI via pip.
    Returns: (success, message)
    """
    import asyncio
    
    try:
        # Try pip3 first, then pip
        for pip_cmd in ["pip3", "pip"]:
            try:
                process = await asyncio.create_subprocess_exec(
                    pip_cmd, "install", "lean",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
                
                if process.returncode == 0:
                    return True, "LEAN CLI installed successfully!"
            except (FileNotFoundError, asyncio.TimeoutError):
                continue
        
        return False, "Failed to install LEAN CLI. Please install manually: pip install lean"
    except Exception as e:
        return False, f"Installation error: {str(e)}"


def install_lean_cli_sync() -> Tuple[bool, str]:
    """
    Install LEAN CLI via pip (synchronous version).
    Returns: (success, message)
    """
    try:
        # Try pip3 first, then pip
        for pip_cmd in ["pip3", "pip"]:
            try:
                result = subprocess.run(
                    [pip_cmd, "install", "lean"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    return True, "LEAN CLI installed successfully!"
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return False, "Failed to install LEAN CLI. Please install manually: pip install lean"
    except Exception as e:
        return False, f"Installation error: {str(e)}"


def detect_ollama() -> Tuple[bool, Optional[str]]:
    """
    Auto-detect Ollama installation and available models.
    Returns: (is_running, host_url)
    """
    import urllib.request
    import urllib.error
    
    hosts_to_check = [
        "http://localhost:11434",
        "http://127.0.0.1:11434",
    ]
    
    for host in hosts_to_check:
        try:
            req = urllib.request.Request(f"{host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True, host
        except (urllib.error.URLError, OSError):
            continue
    
    return False, None


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
    
    # LEAN settings
    lean_cli_path: Optional[str] = Field(default=None, alias="LEAN_CLI_PATH")
    lean_directory: Optional[str] = Field(default=None, alias="LEAN_DIRECTORY")
    lean_enabled: bool = Field(default=False, alias="LEAN_ENABLED")
    
    # Data API keys
    alpha_vantage_api_key: str = Field(default="6ER128DD3NQUPTVC", alias="ALPHA_VANTAGE_API_KEY")
    exa_api_key: Optional[str] = Field(default=None, alias="EXA_API_KEY")
    
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
        "lean_directory": "LEAN_DIRECTORY",
        "lean_enabled": "LEAN_ENABLED",
        "ollama_host": "OLLAMA_HOST",
    }
    
    config_key = setting_map.get(key, key.upper())
    config[config_key] = str(value)
    
    # Write back
    with open(CONFIG_FILE, "w") as f:
        f.write("# Sigma Configuration\n\n")
        for k, v in sorted(config.items()):
            f.write(f"{k}={v}\n")
