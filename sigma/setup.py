"""Sigma Setup Wizard - Beautiful first-run configuration experience."""

import os
import sys
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

# Config directory
CONFIG_DIR = Path.home() / ".sigma"
CONFIG_FILE = CONFIG_DIR / "config.env"
SETUP_COMPLETE_FILE = CONFIG_DIR / ".setup_complete"


def is_setup_complete() -> bool:
    """Check if setup has been completed."""
    return SETUP_COMPLETE_FILE.exists()


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_logo():
    """Print the Sigma logo."""
    logo = """
[bold bright_cyan]
 ███████╗██╗ ██████╗ ███╗   ███╗ █████╗ 
 ██╔════╝██║██╔════╝ ████╗ ████║██╔══██╗
 ███████╗██║██║  ███╗██╔████╔██║███████║
 ╚════██║██║██║   ██║██║╚██╔╝██║██╔══██║
 ███████║██║╚██████╔╝██║ ╚═╝ ██║██║  ██║
 ╚══════╝╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝
[/bold bright_cyan]
"""
    console.print(logo)


def animate_text(text: str, delay: float = 0.02):
    """Animate text character by character."""
    for char in text:
        console.print(char, end="", highlight=False)
        time.sleep(delay)
    console.print()


def show_welcome():
    """Show the welcome screen."""
    clear_screen()
    print_logo()
    
    console.print()
    console.print(Panel(
        "[bold]Welcome to Sigma[/bold]\n\n"
        "[dim]The Institutional-Grade Financial Research Agent[/dim]\n\n"
        "This setup wizard will help you configure Sigma for\n"
        "optimal performance. It only takes about 2 minutes.",
        title="[bold bright_green]Setup Wizard[/bold bright_green]",
        border_style="bright_green",
        padding=(1, 2)
    ))
    console.print()
    
    Prompt.ask("[dim]Press Enter to begin[/dim]", default="")


def show_progress_step(step: int, total: int, title: str):
    """Show progress header."""
    console.print()
    console.print(f"[bold bright_cyan]Step {step}/{total}:[/bold bright_cyan] {title}")
    console.print("[dim]" + "─" * 50 + "[/dim]")
    console.print()


def setup_llm_provider() -> dict:
    """Configure LLM provider."""
    clear_screen()
    print_logo()
    show_progress_step(1, 4, "Choose Your AI Model")
    
    providers = [
        ("google", "Google Gemini", "Free tier available, fast responses", "GOOGLE_API_KEY"),
        ("openai", "OpenAI GPT-4", "Most capable, best for complex analysis", "OPENAI_API_KEY"),
        ("anthropic", "Anthropic Claude", "Excellent reasoning, very safe", "ANTHROPIC_API_KEY"),
        ("groq", "Groq (Llama)", "Extremely fast, free tier available", "GROQ_API_KEY"),
        ("xai", "xAI Grok", "Real-time knowledge, unique insights", "XAI_API_KEY"),
        ("ollama", "Ollama (Local)", "Free, private, runs on your machine", None),
    ]
    
    table = Table(box=box.ROUNDED, border_style="bright_blue")
    table.add_column("#", style="bold cyan", justify="center", width=3)
    table.add_column("Provider", style="bold")
    table.add_column("Description", style="dim")
    
    for i, (key, name, desc, _) in enumerate(providers, 1):
        table.add_row(str(i), name, desc)
    
    console.print(table)
    console.print()
    
    choice = Prompt.ask(
        "[bold]Select your preferred AI provider[/bold]",
        choices=[str(i) for i in range(1, len(providers) + 1)],
        default="1"
    )
    
    selected = providers[int(choice) - 1]
    provider_key, provider_name, _, env_key = selected
    
    config = {"DEFAULT_PROVIDER": provider_key}
    
    console.print()
    console.print(f"[green]Selected:[/green] {provider_name}")
    
    if env_key:
        console.print()
        console.print(Panel(
            f"[bold]Get your API key:[/bold]\n\n"
            f"{'https://aistudio.google.com/apikey' if provider_key == 'google' else ''}"
            f"{'https://platform.openai.com/api-keys' if provider_key == 'openai' else ''}"
            f"{'https://console.anthropic.com/settings/keys' if provider_key == 'anthropic' else ''}"
            f"{'https://console.groq.com/keys' if provider_key == 'groq' else ''}"
            f"{'https://console.x.ai/' if provider_key == 'xai' else ''}",
            title=f"[bold yellow]{provider_name} API Key[/bold yellow]",
            border_style="yellow"
        ))
        console.print()
        
        api_key = Prompt.ask(
            f"[bold]Enter your {provider_name} API key[/bold]",
            password=True
        )
        if api_key:
            config[env_key] = api_key
    else:
        # Ollama
        console.print()
        console.print(Panel(
            "[bold]Ollama Setup:[/bold]\n\n"
            "1. Install Ollama: https://ollama.ai\n"
            "2. Run: ollama pull llama3.2\n"
            "3. Ollama runs automatically in the background",
            title="[bold yellow]Local AI Setup[/bold yellow]",
            border_style="yellow"
        ))
        console.print()
        Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
    
    return config


def setup_additional_providers(config: dict) -> dict:
    """Configure additional LLM providers."""
    clear_screen()
    print_logo()
    show_progress_step(2, 4, "Additional AI Providers (Optional)")
    
    console.print(Panel(
        "You can add more AI providers to switch between them.\n"
        "This is [bold]optional[/bold] - skip if you only need one provider.",
        border_style="blue"
    ))
    console.print()
    
    if not Confirm.ask("[bold]Add additional AI providers?[/bold]", default=False):
        return config
    
    providers = [
        ("GOOGLE_API_KEY", "Google Gemini", "https://aistudio.google.com/apikey"),
        ("OPENAI_API_KEY", "OpenAI GPT-4", "https://platform.openai.com/api-keys"),
        ("ANTHROPIC_API_KEY", "Anthropic Claude", "https://console.anthropic.com/settings/keys"),
        ("GROQ_API_KEY", "Groq (Llama)", "https://console.groq.com/keys"),
        ("XAI_API_KEY", "xAI Grok", "https://console.x.ai/"),
    ]
    
    for env_key, name, url in providers:
        if env_key in config:
            continue
        
        console.print()
        if Confirm.ask(f"[bold]Add {name}?[/bold]", default=False):
            console.print(f"  [dim]Get key: {url}[/dim]")
            api_key = Prompt.ask(f"  [bold]API key[/bold]", password=True)
            if api_key:
                config[env_key] = api_key
                console.print(f"  [green]Added![/green]")
    
    return config


def setup_data_providers(config: dict) -> dict:
    """Configure financial data providers."""
    clear_screen()
    print_logo()
    show_progress_step(3, 4, "Financial Data Providers (Optional)")
    
    console.print(Panel(
        "[bold]Sigma works great with free data from Yahoo Finance.[/bold]\n\n"
        "For premium features, you can add professional data sources.\n"
        "All of these are [bold]optional[/bold].",
        border_style="blue"
    ))
    console.print()
    
    # Table of data providers
    table = Table(box=box.ROUNDED, border_style="dim")
    table.add_column("Provider", style="bold")
    table.add_column("Features", style="dim")
    table.add_column("Free Tier")
    
    table.add_row("Financial Modeling Prep", "Fundamentals, SEC filings", "[green]Yes[/green]")
    table.add_row("Polygon.io", "Real-time data, options", "[green]Yes[/green]")
    table.add_row("Alpha Vantage", "Technical indicators", "[green]Yes[/green]")
    table.add_row("Exa Search", "AI-powered news search", "[yellow]Limited[/yellow]")
    
    console.print(table)
    console.print()
    
    if not Confirm.ask("[bold]Configure data providers?[/bold]", default=False):
        return config
    
    providers = [
        ("FMP_API_KEY", "Financial Modeling Prep", "https://financialmodelingprep.com/developer/docs/"),
        ("POLYGON_API_KEY", "Polygon.io", "https://polygon.io/dashboard/api-keys"),
        ("ALPHA_VANTAGE_API_KEY", "Alpha Vantage", "https://www.alphavantage.co/support/#api-key"),
        ("EXASEARCH_API_KEY", "Exa Search", "https://exa.ai/"),
    ]
    
    for env_key, name, url in providers:
        console.print()
        if Confirm.ask(f"[bold]Add {name}?[/bold]", default=False):
            console.print(f"  [dim]Get key: {url}[/dim]")
            api_key = Prompt.ask(f"  [bold]API key[/bold]", password=True)
            if api_key:
                config[env_key] = api_key
                console.print(f"  [green]Added![/green]")
    
    return config


def setup_preferences(config: dict) -> dict:
    """Configure user preferences."""
    clear_screen()
    print_logo()
    show_progress_step(4, 4, "Preferences")
    
    # Default model selection
    provider = config.get("DEFAULT_PROVIDER", "google")
    
    console.print(Panel(
        "Configure your default settings.\n"
        "You can change these anytime with /model and /mode commands.",
        border_style="blue"
    ))
    console.print()
    
    # Analysis mode
    modes = [
        ("default", "Comprehensive - Uses all available tools"),
        ("technical", "Technical - Charts, indicators, price action"),
        ("fundamental", "Fundamental - Financials, ratios, valuations"),
        ("quant", "Quantitative - Predictions, backtesting"),
    ]
    
    console.print("[bold]Default analysis mode:[/bold]")
    for i, (key, desc) in enumerate(modes, 1):
        console.print(f"  {i}. {desc}")
    console.print()
    
    mode_choice = Prompt.ask(
        "[bold]Select mode[/bold]",
        choices=["1", "2", "3", "4"],
        default="1"
    )
    config["DEFAULT_MODE"] = modes[int(mode_choice) - 1][0]
    
    return config


def save_config(config: dict):
    """Save configuration to file."""
    # Ensure config directory exists
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write config file
    with open(CONFIG_FILE, 'w') as f:
        f.write("# Sigma Configuration\n")
        f.write("# Generated by setup wizard\n")
        f.write("# You can edit this file or run 'sigma --setup' again\n\n")
        
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    
    # Mark setup as complete
    SETUP_COMPLETE_FILE.touch()
    
    # Also create/update .env in current directory if it exists
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists() or Path.cwd().name == "sigma":
        with open(cwd_env, 'a') as f:
            f.write("\n# Added by Sigma setup\n")
            for key, value in config.items():
                if "API_KEY" in key:
                    f.write(f"{key}={value}\n")


def show_completion(config: dict):
    """Show completion screen."""
    clear_screen()
    print_logo()
    
    console.print()
    console.print(Panel(
        "[bold bright_green]Setup Complete![/bold bright_green]\n\n"
        "Sigma is ready to use. Here's what's configured:",
        border_style="bright_green",
        padding=(1, 2)
    ))
    console.print()
    
    # Summary table
    table = Table(box=box.ROUNDED, border_style="green")
    table.add_column("Setting", style="bold")
    table.add_column("Value", style="cyan")
    
    provider_names = {
        "google": "Google Gemini",
        "openai": "OpenAI GPT-4",
        "anthropic": "Anthropic Claude",
        "groq": "Groq (Llama)",
        "xai": "xAI Grok",
        "ollama": "Ollama (Local)"
    }
    
    table.add_row("AI Provider", provider_names.get(config.get("DEFAULT_PROVIDER", "google"), "Google Gemini"))
    table.add_row("Config Location", str(CONFIG_FILE))
    
    # Count configured APIs
    api_count = sum(1 for k in config if "API_KEY" in k)
    table.add_row("API Keys Configured", str(api_count))
    
    console.print(table)
    
    console.print()
    console.print(Panel(
        "[bold]Quick Start:[/bold]\n\n"
        "  [cyan]sigma[/cyan]                    Start Sigma\n"
        "  [cyan]sigma --help[/cyan]             Show help\n"
        "  [cyan]sigma --setup[/cyan]            Run setup again\n\n"
        "[bold]Inside Sigma:[/bold]\n\n"
        "  [dim]Analyze NVDA stock[/dim]\n"
        "  [dim]Compare AAPL, MSFT, GOOGL[/dim]\n"
        "  [dim]/lean run TSLA macd_momentum[/dim]\n\n"
        "[dim]Type /help for all commands[/dim]",
        title="[bold bright_cyan]Getting Started[/bold bright_cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()


def run_setup(force: bool = False) -> dict:
    """Run the setup wizard.
    
    Args:
        force: Force setup even if already complete
        
    Returns:
        Configuration dictionary
    """
    if is_setup_complete() and not force:
        return load_config()
    
    try:
        show_welcome()
        
        config = {}
        config = setup_llm_provider()
        config = setup_additional_providers(config)
        config = setup_data_providers(config)
        config = setup_preferences(config)
        
        # Save with progress
        console.print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold]Saving configuration...[/bold]"),
            console=console
        ) as progress:
            task = progress.add_task("save", total=None)
            save_config(config)
            time.sleep(0.5)
        
        show_completion(config)
        
        Prompt.ask("\n[dim]Press Enter to start Sigma[/dim]", default="")
        
        return config
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Setup cancelled. Run 'sigma --setup' to try again.[/yellow]")
        sys.exit(0)


def load_config() -> dict:
    """Load existing configuration."""
    config = {}
    
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config


def apply_config_to_env(config: dict):
    """Apply loaded config to environment variables."""
    for key, value in config.items():
        if key not in os.environ:
            os.environ[key] = value


def ensure_setup() -> dict:
    """Ensure setup is complete, running wizard if needed.
    
    Returns:
        Configuration dictionary
    """
    if is_setup_complete():
        config = load_config()
        apply_config_to_env(config)
        return config
    else:
        config = run_setup()
        apply_config_to_env(config)
        return config


if __name__ == "__main__":
    run_setup(force=True)
