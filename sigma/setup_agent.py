import sys
import os
import subprocess
import platform
import shutil
import time
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from .config import get_settings, save_api_key, save_setting, mark_first_run_complete
from .llm.registry import REGISTRY

console = Console()

class SetupAgent:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.lean_ok = False
        self.ollama_ok = False
        
    def run(self):
        console.clear()
        console.print(Panel.fit("[bold blue]Welcome to Sigma Setup Agent[/bold blue]", border_style="blue"))
        console.print("[dim]Initializing your financial research environment...[/dim]\n")
        
        self.check_environment()
        self.install_lean()
        self.install_ollama()
        self.configure_ollama_model()
        self.configure_api_tools()
        
        mark_first_run_complete()
        console.print("\n[bold green]Setup Complete![/bold green] Launching Sigma...")
        time.sleep(2)

    def check_environment(self):
        console.print("[bold]1. Checking Environment[/bold]")
        
        # Python
        py_ver = sys.version.split()[0]
        console.print(f"  ✓ Python {py_ver}")
        
        # OS
        console.print(f"  ✓ OS: {self.os_type}")

    def install_lean(self):
        console.print("\n[bold]2. Setting up LEAN Engine[/bold]")
        
        # Check if lean is installed
        if shutil.which("lean"):
            console.print("  ✓ LEAN CLI found")
            self.lean_ok = True
            return

        if Confirm.ask("  [yellow]LEAN CLI not found. Install it now?[/yellow] (Required for backtesting)"):
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                task = progress.add_task("Installing LEAN CLI...", total=None)
                try:
                    # Attempt pipx first
                    if shutil.which("pipx"):
                        subprocess.run(["pipx", "install", "lean-cli"], check=True, capture_output=True)
                    else:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "lean-cli"])
                    progress.update(task, completed=True)
                    console.print("  ✓ LEAN CLI installed successfully")
                    self.lean_ok = True
                    
                    # Should run lean init? Might require user interaction. 
                    # Providing basic config is safer.
                    self._create_minimal_lean_config()
                    
                except Exception as e:
                    console.print(f"  [red]Failed to install LEAN: {e}[/red]")
                    console.print("  Please install manually: `pip install lean-cli`")

    def _create_minimal_lean_config(self):
        # Create a directory for lean data
        lean_dir = os.path.expanduser("~/.sigma/lean_data")
        os.makedirs(lean_dir, exist_ok=True)
        # We might need to run `lean init` eventually, but for now just ensure folder exists.

    def install_ollama(self):
        console.print("\n[bold]3. Setting up Ollama[/bold]")
        
        if shutil.which("ollama"):
            console.print("  ✓ Ollama binary found")
            self.ollama_ok = True
        else:
            console.print("  [yellow]Ollama not found.[/yellow]")
            if self.os_type == "darwin" and shutil.which("brew"):
                if Confirm.ask("  Install via Homebrew?"):
                    subprocess.run(["brew", "install", "ollama"], check=True)
                    self.ollama_ok = True
            elif self.os_type == "linux":
                console.print("  Please install Ollama: curl -fsSL https://ollama.com/install.sh | sh")
                Confirm.ask("  Press Enter once installed")
            
            # Verify again
            if shutil.which("ollama"):
                 self.ollama_ok = True
        
        if self.ollama_ok:
            # Check if running
            try:
                subprocess.run(["ollama", "list"], check=True, capture_output=True)
                console.print("  ✓ Ollama daemon is running")
            except subprocess.CalledProcessError:
                console.print("  [yellow]Ollama daemon not running. Attempting to start...[/yellow]")
                # Attempt start (background)
                if self.os_type == "darwin":
                    subprocess.Popen(["open", "-a", "Ollama"])
                elif self.os_type == "linux":
                    subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                time.sleep(5) # Wait for start
                console.print("  ✓ Attempted start. Please verify in taskbar if needed.")

    def configure_ollama_model(self):
        console.print("\n[bold]4. Configuring AI Models[/bold]")
        
        if not self.ollama_ok:
            console.print("  [dim]Skipping Ollama model setup (Ollama not available)[/dim]")
            return

        choices = ["llama3.2", "mistral", "phi3", "custom"]
        console.print("Select a default local model:")
        for i, m in enumerate(choices):
            console.print(f"  {i+1}) {m}")
        
        selection = Prompt.ask("Choose [1-4]", choices=["1", "2", "3", "4"], default="1")
        model = choices[int(selection)-1]
        
        if model == "custom":
            model = Prompt.ask("Enter model name (e.g. deepseek-coder)")
            
        console.print(f"  Selected: [bold]{model}[/bold]")
        
        # Check if pulled
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if model not in result.stdout:
                if Confirm.ask(f"  Pull {model} now? (Required to use it)"):
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
                         task = progress.add_task(f"Pulling {model}...", total=None)
                         subprocess.run(["ollama", "pull", model], check=True)
        except Exception as e:
            console.print(f"  [red]Error checking/pulling model: {e}[/red]")

        save_setting("default_model", model)
        save_setting("ollama_url", "http://localhost:11434")

    def configure_api_tools(self):
        console.print("\n[bold]5. Configuring API Keys[/bold]")
        
        providers = [
            ("Sigma Cloud (Hack Club)", "sigma_cloud"),
            ("OpenAI", "openai"),
            ("Anthropic", "anthropic"),
            ("Google Gemini", "google"),
            ("Groq", "groq"),
            ("xAI (Grok)", "xai"),
            ("Polygon.io", "polygon"),
            ("Exa Search", "exa"),
        ]
        
        for name, key_id in providers:
            settings = get_settings()
            existing = getattr(settings, key_id, None)
            
            if not existing:
                if Confirm.ask(f"  Configure {name}?"):
                    key = Prompt.ask(f"    Enter API Key for {name}", password=True)
                    if key:
                        save_api_key(key_id, key)
                        console.print(f"    ✓ Saved {name}")
            else:
                console.print(f"  ✓ {name} configured")

def run_setup():
    agent = SetupAgent()
    agent.run()
    return True

if __name__ == "__main__":
    run_setup()
