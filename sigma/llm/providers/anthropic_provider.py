import json
from typing import Any, Callable, Dict, List, Optional, Union, AsyncIterator
import logging

from .base import BaseLLM

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseLLM):
    """Anthropic Claude client."""
    
    provider_name = "anthropic"
    
    def __init__(self, api_key: str, rate_limiter=None, base_url: Optional[str] = None):
        super().__init__(rate_limiter)
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key, base_url=base_url)
    
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
        
        # Format messages for Anthropic (separate system message)
        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)
                
        kwargs = {
            "model": model,
            "max_tokens": 4096,
            "messages": filtered_messages,
            "system": system_prompt,
        }
        
        if tools:
            kwargs["tools"] = tools
        
        if stream:
            return self._stream_response(kwargs, on_tool_call, tools, messages) # Pass original messages for recursion
        else:
            return await self._block_response(kwargs, on_tool_call, tools, messages)

    async def _block_response(self, kwargs, on_tool_call, tools, messages):
        response = await self.client.messages.create(**kwargs)
        
        # Check for tool usage
        if response.stop_reason == "tool_use" and on_tool_call:
            tool_results = []
            assistant_content = []
            
            # Construct assistant message parts
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })
                    
                    # Execute tool
                    try:
                        result = await on_tool_call(block.name, block.input)
                    except Exception as e:
                        result = {"error": str(e)}
                        
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str)
                    })
            
            # Append exchange to history
            new_messages = messages + [
                {"role": "assistant", "content": assistant_content},
                {"role": "user", "content": tool_results}
            ]
            
            # Recurse
            # Re-format for next call
            next_kwargs = kwargs.copy()
            next_system = ""
            next_filtered = []
            for msg in new_messages:
                if isinstance(msg.get("content"), str): # Basic text message
                    if msg["role"] == "system":
                        next_system = msg["content"]
                    else:
                        next_filtered.append(msg)
                else: # Complex content
                    next_filtered.append(msg)
            
            next_kwargs["messages"] = next_filtered
            next_kwargs["system"] = next_system
            
            return await self._block_response(next_kwargs, on_tool_call, tools, new_messages)

        return response.content[0].text if response.content else ""

    async def _stream_response(self, kwargs, on_tool_call, tools, messages) -> AsyncIterator[str]:
        async with self.client.messages.stream(**kwargs) as stream:
            current_tool_use: Dict[str, Any] = {}
            current_text = ""
            tool_uses = []
            
            async for event in stream:
                if event.type == "content_block_delta":
                    if event.delta.type == "text_delta":
                        yield event.delta.text
                        current_text += event.delta.text
                    elif event.delta.type == "input_json_delta":
                        # Accumulate JSON
                        current_tool_use["input_json"] = current_tool_use.get("input_json", "") + event.delta.partial_json
                
                elif event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        current_tool_use = {
                            "name": event.content_block.name,
                            "id": event.content_block.id,
                            "input_json": ""
                        }
                
                elif event.type == "content_block_stop":
                    if current_tool_use:
                        try:
                            current_tool_use["input"] = json.loads(current_tool_use["input_json"])
                        except:
                            current_tool_use["input"] = {}
                        tool_uses.append(current_tool_use)
                        current_tool_use = {}
                
                elif event.type == "message_stop":
                    pass

        # If tools were used, execute and recurse
        if tool_uses and on_tool_call:
            # Reconstruct assistant message
            assistant_content = []
            if current_text:
                assistant_content.append({"type": "text", "text": current_text})
            
            tool_results = []
            for tu in tool_uses:
                assistant_content.append({
                    "type": "tool_use",
                    "id": tu["id"],
                    "name": tu["name"],
                    "input": tu["input"]
                })
                try:
                    res = await on_tool_call(tu["name"], tu["input"])
                except Exception as e:
                    res = {"error": str(e)}
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": json.dumps(res, default=str)
                })

            new_messages = messages + [
                {"role": "assistant", "content": assistant_content},
                {"role": "user", "content": tool_results}
            ]
            
            # Prepare next call
            next_kwargs = kwargs.copy()
            next_system = ""
            next_filtered = []
            for msg in new_messages:
                if isinstance(msg.get("content"), str):
                    if msg["role"] == "system":
                        next_system = msg["content"]
                    else:
                        next_filtered.append(msg)
                else:
                    next_filtered.append(msg)
            
            next_kwargs["messages"] = next_filtered
            next_kwargs["system"] = next_system
            
            async for chunk in self._stream_response(next_kwargs, on_tool_call, tools, new_messages):
                yield chunk
