"""Sigma v3.2.0 - Setup Wizard."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

from .config import (
    get_settings,
    save_api_key,
    save_setting,
    LLMProvider,
    AVAILABLE_MODELS,
    CONFIG_DIR,
)


__version__ = "3.2.0"
SIGMA = "σ"
console = Console()

# Clean banner - just SIGMA, no SETU
BANNER = """
[bold blue]███████╗██╗ ██████╗ ███╗   ███╗ █████╗ [/bold blue]
[bold blue]██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗[/bold blue]
[bold blue]███████╗██║██║  ███╗██╔████╔██║███████║[/bold blue]
[bold blue]╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║[/bold blue]
[bold blue]███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║[/bold blue]
[bold blue]╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝[/bold blue]

[bold cyan]σ Finance Research Agent[/bold cyan] [dim]- Setup Wizard v3.2.0[/dim]
"""


class SetupWizard:
    """Interactive setup wizard."""
    
    def __init__(self):
        self.settings = get_settings()
        self.providers = {
            LLMProvider.GOOGLE: {
                "name": "Google Gemini",
                "models": AVAILABLE_MODELS.get("google", []),
                "url": "https://aistudio.google.com/apikey",
                "free": True,
                "desc": "Fast, capable, free tier",
                "recommended": True,
            },
            LLMProvider.OPENAI: {
                "name": "OpenAI GPT",
                "models": AVAILABLE_MODELS.get("openai", []),
                "url": "https://platform.openai.com/api-keys",
                "free": False,
                "desc": "Industry standard",
            },
            LLMProvider.ANTHROPIC: {
                "name": "Anthropic Claude",
                "models": AVAILABLE_MODELS.get("anthropic", []),
                "url": "https://console.anthropic.com/",
                "free": False,
                "desc": "Advanced reasoning",
            },
            LLMProvider.GROQ: {
                "name": "Groq (Llama)",
                "models": AVAILABLE_MODELS.get("groq", []),
                "url": "https://console.groq.com/keys",
                "free": True,
                "desc": "Ultra-fast, free tier",
                "recommended": True,
            },
            LLMProvider.XAI: {
                "name": "xAI Grok",
                "models": AVAILABLE_MODELS.get("xai", []),
                "url": "https://console.x.ai/",
                "free": False,
                "desc": "X.com AI",
            },
            LLMProvider.OLLAMA: {
                "name": "Ollama (Local)",
                "models": AVAILABLE_MODELS.get("ollama", []),
                "url": "https://ollama.ai/download",
                "free": True,
                "desc": "Run locally, no API key",
            },
        }
    
    def run(self) -> bool:
        """Run setup wizard."""
        console.clear()
        console.print(BANNER)
        console.print()
        
        console.print(Panel(
            "[bold]Welcome to Sigma Setup[/bold]\n\n"
            "This wizard will configure Sigma for first use.\n"
            f"Configuration stored in [cyan]~/.sigma/[/cyan]\n\n"
            "[bold]Steps:[/bold]\n"
            "  1. Choose AI provider\n"
            "  2. Configure API key\n"
            "  3. Select model\n"
            "  4. Data settings\n"
            "  5. Optional: Ollama, LEAN",
            title=f"[cyan]{SIGMA} Setup[/cyan]",
            border_style="blue",
        ))
        console.print()
        
        if not Confirm.ask("Ready to begin?", default=True):
            console.print("[dim]Cancelled.[/dim]")
            return False
        
        console.print()
        
        # Steps
        self._setup_provider()
        console.print()
        self._setup_api_key()
        console.print()
        self._setup_model()
        console.print()
        self._setup_data()
        console.print()
        self._setup_integrations()
        console.print()
        self._show_summary()
        
        return True
    
    def _setup_provider(self):
        """Choose AI provider."""
        console.print(Panel("[bold]Step 1: AI Provider[/bold]", border_style="blue"))
        console.print()
        
        providers = list(self.providers.keys())
        
        for i, p in enumerate(providers, 1):
            info = self.providers[p]
            name = info["name"]
            desc = info["desc"]
            free = "[green]free[/green]" if info.get("free") else "[yellow]paid[/yellow]"
            rec = " [cyan](recommended)[/cyan]" if info.get("recommended") else ""
            console.print(f"  {i}. [bold]{name}[/bold] - {desc} {free}{rec}")
        
        console.print()
        choice = Prompt.ask(
            "Choose provider",
            choices=[str(i) for i in range(1, len(providers) + 1)],
            default="1"
        )
        
        provider = providers[int(choice) - 1]
        save_setting("default_provider", provider.value)
        self.settings.default_provider = provider
        
        console.print(f"[cyan]{SIGMA}[/cyan] Provider: [bold]{self.providers[provider]['name']}[/bold]")
    
    def _setup_api_key(self):
        """Configure API key."""
        console.print(Panel("[bold]Step 2: API Key[/bold]", border_style="blue"))
        console.print()
        
        provider = self.settings.default_provider
        info = self.providers[provider]
        
        if provider == LLMProvider.OLLAMA:
            console.print("[dim]Ollama runs locally - no API key needed.[/dim]")
            if Confirm.ask("Is Ollama installed?", default=True):
                console.print(f"[cyan]{SIGMA}[/cyan] Ollama configured")
            else:
                console.print(f"Install from: [bold]{info['url']}[/bold]")
            return
        
        # Check existing
        key_attr = f"{provider.value}_api_key"
        existing = getattr(self.settings, key_attr, None)
        
        if existing:
            masked = f"{existing[:8]}...{existing[-4:]}"
            console.print(f"[dim]Existing key: {masked}[/dim]")
            if not Confirm.ask("Replace?", default=False):
                console.print(f"[cyan]{SIGMA}[/cyan] Keeping existing key")
                return
        
        console.print(f"Get key from: [bold]{info['url']}[/bold]")
        console.print()
        
        api_key = Prompt.ask("API key", password=True)
        
        if api_key:
            save_api_key(provider, api_key)
            setattr(self.settings, key_attr, api_key)
            console.print(f"[cyan]{SIGMA}[/cyan] Key saved for {info['name']}")
        else:
            console.print("[yellow]Skipped[/yellow]")
    
    def _setup_model(self):
        """Select model."""
        console.print(Panel("[bold]Step 3: Model[/bold]", border_style="blue"))
        console.print()
        
        provider = self.settings.default_provider
        models = self.providers[provider]["models"]
        
        if not models:
            console.print("[yellow]No models for this provider[/yellow]")
            return
        
        console.print("Available models:")
        for i, m in enumerate(models, 1):
            current = " [cyan](current)[/cyan]" if m == self.settings.default_model else ""
            console.print(f"  {i}. {m}{current}")
        
        console.print()
        choice = Prompt.ask(
            "Choose model",
            choices=[str(i) for i in range(1, len(models) + 1)],
            default="1"
        )
        
        model = models[int(choice) - 1]
        save_setting("default_model", model)
        self.settings.default_model = model
        
        console.print(f"[cyan]{SIGMA}[/cyan] Model: [bold]{model}[/bold]")
    
    def _setup_data(self):
        """Data settings."""
        console.print(Panel("[bold]Step 4: Data Settings[/bold]", border_style="blue"))
        console.print()
        
        console.print(f"Data stored in: [bold]~/.sigma[/bold]")
        console.print()
        
        # Output directory
        default_out = os.path.expanduser("~/Documents/Sigma")
        out_dir = Prompt.ask("Output directory", default=default_out)
        
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        save_setting("output_dir", out_dir)
        console.print(f"[cyan]{SIGMA}[/cyan] Output: {out_dir}")
        
        # Cache
        if Confirm.ask("Enable caching?", default=True):
            save_setting("cache_enabled", "true")
            console.print(f"[cyan]{SIGMA}[/cyan] Caching enabled")
        else:
            save_setting("cache_enabled", "false")
    
    def _setup_integrations(self):
        """Optional integrations."""
        console.print(Panel("[bold]Step 5: Integrations[/bold]", border_style="blue"))
        console.print()
        
        # Ollama (if not primary)
        if self.settings.default_provider != LLMProvider.OLLAMA:
            if Confirm.ask("Setup Ollama for local fallback?", default=False):
                console.print("[dim]Install: https://ollama.ai/download[/dim]")
                console.print("[dim]Run: ollama pull llama3.2[/dim]")
        
        # LEAN
        if Confirm.ask("Setup LEAN/QuantConnect?", default=False):
            console.print("[dim]LEAN provides advanced backtesting.[/dim]")
            console.print("[dim]Install: pip install lean[/dim]")
            console.print()
            
            lean_path = Prompt.ask("LEAN CLI path (or Enter to skip)", default="")
            if lean_path:
                save_setting("lean_cli_path", lean_path)
                console.print(f"[cyan]{SIGMA}[/cyan] LEAN configured")
    
    def _show_summary(self):
        """Show summary."""
        console.print(Panel(
            "[bold green]Setup Complete![/bold green]",
            border_style="green",
        ))
        console.print()
        
        table = Table(show_header=False, box=None)
        table.add_column("", style="bold")
        table.add_column("")
        
        provider = getattr(self.settings.default_provider, 'value', str(self.settings.default_provider))
        table.add_row("Provider", provider)
        table.add_row("Model", self.settings.default_model)
        
        console.print(table)
        console.print()
        console.print(f"Run [bold]sigma[/bold] to start!")
        console.print()


def run_setup() -> bool:
    """Run the setup wizard."""
    wizard = SetupWizard()
    return wizard.run()


def quick_setup():
    """Quick setup for first-time users."""
    console.print(BANNER)
    console.print()
    
    console.print("[bold]Quick Setup[/bold]")
    console.print()
    
    # Pick provider
    console.print("Choose provider:")
    console.print("  1. [bold]Google Gemini[/bold] [green](free, recommended)[/green]")
    console.print("  2. [bold]Groq[/bold] [green](free, fast)[/green]")
    console.print("  3. [bold]Ollama[/bold] [green](local, no key)[/green]")
    console.print()
    
    choice = Prompt.ask("Provider", choices=["1", "2", "3"], default="1")
    
    providers = {
        "1": ("google", "gemini-2.0-flash"),
        "2": ("groq", "llama-3.3-70b-versatile"),
        "3": ("ollama", "llama3.2"),
    }
    
    provider_key, model = providers[choice]
    provider_name = {"google": "Google Gemini", "groq": "Groq", "ollama": "Ollama"}[provider_key]
    
    if provider_key != "ollama":
        urls = {
            "google": "https://aistudio.google.com/apikey",
            "groq": "https://console.groq.com/keys",
        }
        console.print(f"\nGet key from: [bold]{urls[provider_key]}[/bold]")
        api_key = Prompt.ask("API key", password=True)
        
        if api_key:
            save_api_key(LLMProvider(provider_key), api_key)
    
    save_setting("default_provider", provider_key)
    save_setting("default_model", model)
    
    console.print()
    console.print(f"[bold green]{SIGMA} Setup complete![/bold green]")
    console.print(f"Provider: {provider_name}")
    console.print(f"Model: {model}")
    console.print()
    console.print("Run [bold]sigma[/bold] to start!")


if __name__ == "__main__":
    if "--quick" in sys.argv:
        quick_setup()
    else:
        run_setup()
