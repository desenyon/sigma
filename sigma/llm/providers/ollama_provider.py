import json
from typing import Any, Callable, Dict, List, Optional, Union, AsyncIterator
import logging
import aiohttp

from .base import BaseLLM

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLM):
    """Ollama client."""
    
    provider_name = "ollama"
    
    def __init__(self, base_url: str = "http://localhost:11434", rate_limiter=None):
        super().__init__(rate_limiter)
        self.base_url = base_url
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        on_tool_call: Optional[Callable] = None,
        stream: bool = True,
        json_mode: bool = False,
    ) -> Union[str, AsyncIterator[str]]:
        await self._wait_for_rate_limit()
        
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        
        if json_mode:
            payload["format"] = "json"
            
        if tools:
            # Check if ollama model supports tools. Most new ones do.
            # Convert tools to Ollama format (matches OpenAI mostly)
            payload["tools"] = tools
        
        if stream:
            return self._stream_response(url, payload, on_tool_call, tools, messages)
        else:
            return await self._block_response(url, payload, on_tool_call, tools, messages)

    async def _block_response(self, url, payload, on_tool_call, tools, messages):
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Ollama error {response.status}: {text}")
                
                data = await response.json()
                message = data.get("message", {})
                
                if message.get("tool_calls") and on_tool_call:
                    tool_calls = message["tool_calls"]
                    
                    tool_results = []
                    for tc in tool_calls:
                        func = tc["function"]
                        try:
                            # Ollama arguments are usually a dict already
                            args = func["arguments"]
                            if isinstance(args, str):
                                args = json.loads(args)
                            result = await on_tool_call(func["name"], args)
                        except Exception as e:
                            result = {"error": str(e)}
                        
                        tool_results.append({
                            "role": "tool",
                            "content": json.dumps(result, default=str)
                        })
                    
                    # Recurse
                    new_messages = messages + [message] + tool_results
                    return await self.generate(new_messages, payload["model"], tools, on_tool_call, stream=False, json_mode=False) # Keep json_mode arg?

                return message.get("content", "")

    async def _stream_response(self, url, payload, on_tool_call, tools, messages) -> AsyncIterator[str]:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"Ollama error {response.status}: {text}")
                
                tool_calls_acc = []
                current_text = ""
                final_msg = None
                
                # Ollama streams line-delimited JSON objects
                async for line in response.content:
                    if not line:
                        continue
                    try:
                        # Decode bytes to string
                        line_str = line.decode('utf-8') if isinstance(line, bytes) else line
                        chunk = json.loads(line_str)
                        
                        delta = chunk.get("message", {})
                        content = delta.get("content", "")
                        
                        if content:
                            current_text += content
                            yield content
                        
                        if delta.get("tool_calls"):
                            tool_calls_acc.extend(delta["tool_calls"])
                            
                        if chunk.get("done"):
                            final_msg = {
                                "role": "assistant",
                                "content": current_text,
                            }
                            if tool_calls_acc:
                                final_msg["tool_calls"] = tool_calls_acc
                            
                    except json.JSONDecodeError:
                        continue
                
                if tool_calls_acc and on_tool_call:
                     # Execute and recurse
                     tool_results = []
                     for tc in tool_calls_acc:
                        func = tc["function"]
                        try:
                            args = func["arguments"]
                            if isinstance(args, str):
                                args = json.loads(args)
                            result = await on_tool_call(func["name"], args)
                        except Exception as e:
                            result = {"error": str(e)}
                        
                        tool_results.append({
                            "role": "tool",
                            "content": json.dumps(result, default=str)
                        })
                     
                     new_messages = messages + [final_msg] + tool_results
                     
                     # Recursively call generate with updated history
                     generator = await self.generate(new_messages, payload["model"], tools, on_tool_call, stream=True)
                     
                     if hasattr(generator, '__aiter__'):
                         async for x in generator:
                             yield x
                     elif isinstance(generator, str):
                         yield generator
