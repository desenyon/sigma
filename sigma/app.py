"""Sigma v3.6.1 - Finance Research Agent."""

import asyncio
import time
from typing import Any, List, Dict, Optional
from datetime import datetime

from rich.markdown import Markdown
from rich.text import Text
from rich.console import RenderableType
from rich.style import Style
from rich.syntax import Syntax

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, Container
from textual.widgets import Static, Label, Footer, Header, Button
from textual.binding import Binding
from textual.reactive import reactive
from textual.message import Message
from textual.events import Key

from .config import get_settings
from .llm.router import get_router, LLMRouter
from .tools.registry import TOOL_REGISTRY
# Import tools to ensure registration
import sigma.tools.local_backtest
import sigma.tools.backtest
import sigma.tools.alpha_vantage
import sigma.tools.exa_search
import sigma.tools.polygon
from .core.engine import Engine

from .ui.widgets import SigmaInput, SigmaLoader, TickerBadge

__version__ = "3.6.1"

class ChatMessage(Static):
    """Base class for chat messages."""
    pass

class UserMessage(ChatMessage):
    """A message from the user."""
    
    def __init__(self, content: str, **kwargs):
        super().__init__(**kwargs)
        self.content = content

    def render(self) -> RenderableType:
        return Text(f"> {self.content}", style="bold #a9b1d6")

class ToolMessage(ChatMessage):
    """A message representing a tool call."""
    
    status = reactive("Running...")
    result = reactive("")
    
    def __init__(self, tool_name: str, **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.start_time = time.time()
        self.finished = False

    def render(self) -> RenderableType:
        # Minimalist tool output
        if not self.finished:
            return Text(f"  [RUN] {self.tool_name}...", style="dim #565f89")
        
        status_color = "#9ece6a" if "Error" not in self.status else "#f7768e"
        status_text = "[OK]" if "Error" not in self.status else "[ERR]"
        
        text = Text()
        text.append(f"  {status_text} ", style=status_color)
        text.append(f"{self.tool_name} ", style="bold #7aa2f7")
        
        duration = time.time() - self.start_time
        text.append(f"({duration:.2f}s)", style="dim")
            
        if self.result is not None and str(self.result).strip():
            display_result = str(self.result).strip()
            # Clean up newlines for compact display
            display_result = display_result.replace("\n", " ")
            if len(display_result) > 100:
                display_result = display_result[:100] + "..."
            text.append(f" -> {display_result}", style="italic #565f89")
            
        return text
        
    def complete(self, result: Any, error: bool = False):
        self.finished = True
        self.result = result
        self.status = "Error" if error else "Completed"
        if error:
            self.add_class("error")
        else:
            self.add_class("completed")
        self.refresh()

class AssistantMessage(ChatMessage):
    """A message from the assistant."""
    
    content = reactive("")
    
    def render(self) -> RenderableType:
        return Markdown(self.content)
    
    def append(self, chunk: str):
        self.content += chunk

from .utils.formatting import format_tool_result

class SigmaApp(App):
    """The main Sigma TUI application."""
    
    CSS = """
    /* Tokyonight / Claude Code Inspired Theme */
    Screen {
        background: #1a1b26; /* Tokyonight Background */
        color: #a9b1d6;
    }
    
    #chat-view {
        height: 1fr;
        overflow-y: auto;
        padding: 1 2;
        scrollbar-gutter: stable;
    }
    
    #input-area {
        height: auto;
        dock: bottom;
        background: #16161e; /* Slightly darker */
        padding: 1 2;
        border-top: solid #2f334d;
        layout: vertical;
    }
    
    #input-bar {
        height: 1;
        layout: horizontal;
    }

    #prompt-char {
        color: #7aa2f7;
        margin-right: 1;
        text-style: bold;
    }
    
    SigmaInput {
        width: 1fr;
        background: transparent;
        border: none;
        color: #c0caf5;
    }
    SigmaInput:focus {
        border: none;
    }
    
    SigmaLoader {
        width: auto;
        margin-left: 2;
        display: none;
    }
    SigmaLoader.active {
        display: block;
    }

    UserMessage {
        margin: 1 0;
        color: #c0caf5;
    }

    ToolMessage {
        margin-left: 2;
        color: #565f89;
    }
    
    AssistantMessage {
        margin: 1 0 2 0;
        color: #c0caf5;
    }

    .welcome-message {
        text-align: center;
        color: #565f89;
        margin: 2 0;
        text-style: italic;
    }
    
    #suggestion-label {
        color: #565f89;
        padding-left: 2;
        margin-bottom: 0;
        text-style: italic;
        display: none;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+l", "clear_chat", "Clear"),
    ]

    def compose(self) -> ComposeResult:
        # yield Header(show_clock=True) # Minimalist - no header
        yield VerticalScroll(id="chat-view")
        
        with Container(id="input-area"):
            yield Label("", id="suggestion-label")
            with Horizontal(id="input-bar"):
                yield Label(">", id="prompt-char")
                yield SigmaInput(placeholder="Simmering...")
                yield TickerBadge(id="ticker-badge")
                yield SigmaLoader(id="loader")
            
    def on_mount(self):
        self.query_one("#chat-view").mount(
            Static(f"Sigma v{__version__} ready.", classes="welcome-message")
        )
        self.engine = Engine()
        self.router = get_router(get_settings())
        
        # Connect input suggestion to label
        self.query_one(SigmaInput).watch_suggestion = self.update_suggestion_label

    def update_suggestion_label(self, old_val, new_val):
        label = self.query_one("#suggestion-label")
        if new_val:
            label.update(f"Suggestion: {new_val} (Tab)")
            label.styles.display = "block"
        else:
            label.styles.display = "none"

    async def on_input_submitted(self, event: SigmaInput.Submitted):
        query = event.value.strip()
        if not query:
            return
            
        event.input.value = ""
        chat_view = self.query_one("#chat-view")
        
        # Add User Message
        await chat_view.mount(UserMessage(query))
        
        # Add Assistant Message Placeholder
        assistant_msg = AssistantMessage()
        await chat_view.mount(assistant_msg)
        
        # Start processing
        self.query_one("#loader").add_class("active")
        self.process_query(query, assistant_msg)

    @work
    async def process_query(self, query: str, message_widget: AssistantMessage):
        chat_view = self.query_one("#chat-view")
        
        try:
            # Tool Execution Callback
            async def on_tool_call(name: str, args: dict):
                # 1. Mount Tool Message
                tool_msg = ToolMessage(name)
                self.call_from_thread(chat_view.mount, tool_msg)
                self.call_from_thread(chat_view.scroll_end)
                
                # 2. Execute Tool
                try:
                    tool_def = TOOL_REGISTRY.get_tool(name)
                    if not tool_def:
                        result = {"error": f"Tool {name} not found"}
                    else:
                        if asyncio.iscoroutinefunction(tool_def.func):
                            result = await tool_def.func(**args)
                        else:
                            result = await asyncio.to_thread(tool_def.func, **args)
                            
                except Exception as e:
                    result = {"error": str(e)}
                
                # 3. Update UI
                formatted = format_tool_result(result)
                self.call_from_thread(tool_msg.complete, formatted, error="error" in str(result).lower() and "error" in result if isinstance(result, dict) else False)
                
                return result

            # Parse Intent
            try:
                plan = await self.engine.intent_parser.parse(query)
                # We don't show the plan explicitly in the new minimalist UI unless debug mode
            except Exception as e:
                pass

            system_prompt = f"""You are Sigma, an elite financial research assistant.
Your goal is to provide accurate, data-driven, and comprehensive financial analysis.

GUIDELINES:
- ALWAYS use tools to fetch real data.
- Be concise. Use Markdown.
- Use the provided tools proactively.
"""
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            tools = TOOL_REGISTRY.to_llm_format()
            
            response_stream = await self.router.chat(
                messages=messages,
                stream=True,
                tools=tools,
                on_tool_call=on_tool_call
            )
            
            if hasattr(response_stream, '__aiter__'):
                async for chunk in response_stream:
                    self.call_from_thread(message_widget.append, chunk)
                    self.call_from_thread(chat_view.scroll_end)
            else:
                self.call_from_thread(message_widget.append, str(response_stream))

        except Exception as e:
            self.call_from_thread(message_widget.append, f"\n\n**Error:** {str(e)}")
        
        finally:
            self.call_from_thread(self.query_one("#loader").remove_class, "active")
            self.call_from_thread(chat_view.scroll_end)

    def action_clear_chat(self):
        self.query_one("#chat-view").remove_children()

def launch():
    app = SigmaApp()
    app.run()

if __name__ == "__main__":
    launch()
