from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Static, Label
from textual.reactive import reactive
from textual.message import Message
from textual import work
from rich.console import RenderableType
from rich.style import Style
from rich.text import Text
import re
import httpx
import asyncio
from sigma.config import get_settings

class SigmaLoader(Static):
    """A custom loading indicator with the Sigma logo."""
    
    frames = ["σ", "σ.", "σ..", "σ...", "σ..", "σ."]
    
    def on_mount(self) -> None:
        self.frame_index = 0
        self.interval = self.set_interval(0.15, self.animate)
        
    def animate(self) -> None:
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.update(Text(self.frames[self.frame_index], style="bold #7aa2f7"))

class SigmaInput(Input):
    """
    A specialized input widget that features:
    1. Ticker symbol recognition/highlighting.
    2. Generative autocomplete via local LLM.
    3. Minimalist 'Claude Code' styling.
    """

    DEFAULT_CSS = """
    SigmaInput {
        border: none;
        height: 1;
        padding: 0;
        margin: 0;
        background: transparent;
        color: #e0e0e0;
    }
    SigmaInput:focus {
        border: none;
    }
    .ticker-highlight {
        color: #73daca;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("tab", "accept_suggestion", "Accept Suggestion"),
    ]

    # Reactive property to store the current suggestion
    suggestion = reactive("")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = get_settings()
        self.debounce_timer = None
        
    def on_mount(self) -> None:
        self.border_title = None
        
    def action_accept_suggestion(self):
        if self.suggestion:
            self.value += self.suggestion
            self.suggestion = ""
            self.cursor_position = len(self.value)
        
    def on_change(self, event: Input.Changed) -> None:
        # Ticker Recognition
        self._check_tickers(event.value)
        
        # Debounced Autocomplete
        if self.debounce_timer:
            self.debounce_timer.cancel()
        
        if event.value.strip():
            self.debounce_timer = self.set_timer(0.4, self._fetch_suggestion)
        else:
            self.suggestion = ""

    def _check_tickers(self, value: str) -> None:
        # Regex for tickers like $AAPL or just AAPL (3-5 uppercase letters)
        # We'll just emit a message if found, or maybe just highlight logic
        # For now, let's look for $TICKER pattern
        ticker_pattern = r"\$[A-Z]{2,5}\b"
        matches = re.findall(ticker_pattern, value)
        if matches:
            # We could emit an event here to show a badge elsewhere
            pass

    @work(exclusive=True, thread=True)
    async def _fetch_suggestion(self) -> None:
        if not self.value or len(self.value) < 3:
            return

        try:
            # Use the local model (e.g., qwen2.5:1.5b) for speed
            model = "qwen2.5:1.5b" 
            prompt = f"Complete this sentence naturally (max 5 words): {self.value}"
            
            async with httpx.AsyncClient(timeout=1.0) as client:
                response = await client.post(
                    f"{self.settings.ollama_host}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"num_predict": 6, "temperature": 0.1}
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    completion = data.get("response", "").strip()
                    # Only show if it actually continues the text
                    if completion and not completion.lower().startswith(self.value.lower()):
                         # If completion repeats the input, strip it
                         self.suggestion = completion
                    elif completion.lower().startswith(self.value.lower()):
                         self.suggestion = completion[len(self.value):]
        except Exception:
            # Fail silently for autocomplete
            pass

    def render(self) -> RenderableType:
        # Custom rendering to overlay suggestion
        # This is tricky in Textual's Input. 
        # For now, we rely on the standard Input render but maybe we can add a suggestion label next to it.
        return super().render()

class TickerBadge(Static):
    """Shows detected tickers."""
    
    DEFAULT_CSS = """
    TickerBadge {
        background: #2b2d31;
        color: #73daca;
        padding: 0 1;
        margin: 0 1;
        display: none;
        height: 1;
    }
    TickerBadge.visible {
        display: block;
    }
    """
    
    def set_ticker(self, ticker: str):
        self.update(f"σ {ticker}")
        self.add_class("visible")
        
    def clear(self):
        self.remove_class("visible")

