import json
from typing import Any, Callable, Dict, List, Optional, Union, AsyncIterator
import logging

from .base import BaseLLM

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLM):
    """OpenAI client."""
    
    provider_name = "openai"
    
    def __init__(self, api_key: str, rate_limiter=None, base_url: Optional[str] = None):
        super().__init__(rate_limiter)
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
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
        
        kwargs = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        try:
            if stream:
                return self._stream_response(kwargs, on_tool_call, tools, messages)
            else:
                return await self._block_response(kwargs, on_tool_call, tools, messages)
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise

    async def _block_response(self, kwargs, on_tool_call, tools, messages):
        response = await self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        # Handle tool calls for non-streaming
        if message.tool_calls and on_tool_call:
            # We don't support recursive tool calls in blocking mode here nicely without complex recursion
            # But the requirement is to have it work.
            # For simplicity in this phase, I'm just returning the content or processing one level.
            # Ideally the Engine handles the loop, but here the Provider abstraction might be asked to handle it.
            # The prompt says "Engine... coordinates tool usage".
            # So the Provider should probably just return the tool call specific structure if it's not final.
            # But to be drop-in compatible, let's keep it simple.
            
            # Actually, standard practice for these agents:
            # Provider returns the raw opaque response or a standardized "Response" object.
            # The Engine loops. 
            # But looking at the existing code, `generate` calls `on_tool_call` recursively.
            
            tool_msgs = []
            for tc in message.tool_calls:
                # Execute tool
                try:
                    args = json.loads(tc.function.arguments)
                    tool_result = await on_tool_call(tc.function.name, args)
                except Exception as e:
                    tool_result = {"error": str(e)}
                
                tool_msgs.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "name": tc.function.name,
                    "content": json.dumps(tool_result, default=str)
                })

            # Recurse
            # Warning: This recursion assumes we want to continue generation.
            # Remove tool_choice to avoid loops if needed, or rely on model to stop.
            new_messages = messages + [message.model_dump()] + tool_msgs
            kwargs["messages"] = new_messages
            # remove tools if we want to force stop? no, model might want to call more.
            
            return await self._block_response(kwargs, on_tool_call, tools, new_messages)

        return message.content or ""

    async def _stream_response(self, kwargs, on_tool_call, tools, messages) -> AsyncIterator[str]:
        # Note: Handling tool calls in stream is complex. 
        # For this implementation, if we see tool calls, we accumulate them, execute, and then recurse.
        # If it's text, we yield.
        
        stream = await self.client.chat.completions.create(**kwargs)
        
        tool_calls = []
        current_content = ""
        
        async for chunk in stream:
            delta = chunk.choices[0].delta
            
            if delta.content:
                current_content += delta.content
                yield delta.content
            
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    if len(tool_calls) <= tc.index:
                        tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                    
                    if tc.id:
                        tool_calls[tc.index]["id"] = tc.id
                    if tc.function.name:
                        tool_calls[tc.index]["function"]["name"] += tc.function.name
                    if tc.function.arguments:
                        tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

        if tool_calls and on_tool_call:
            # We have tool calls. We must execute them and recurse.
            # Since we already yielded content, we just continue yielding from the new stream.
            
            # Construct the assistant message that provoked this
            assistant_msg = {
                "role": "assistant",
                "content": current_content if current_content else None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": tc["function"]
                    } for tc in tool_calls
                ]
            }
            
            tool_outputs = []
            for tc in tool_calls:
                fname = tc["function"]["name"]
                fargs = tc["function"]["arguments"]
                try:
                    args = json.loads(fargs)
                    # Notify UI of tool usage? 
                    # The Engine handles notifications, but here we just execute.
                    result = await on_tool_call(fname, args)
                except Exception as e:
                    result = {"error": str(e)}
                
                tool_outputs.append({
                    "tool_call_id": tc["id"],
                    "role": "tool",
                    "name": fname,
                    "content": json.dumps(result, default=str)
                })
            
            new_messages = messages + [assistant_msg] + tool_outputs
            kwargs["messages"] = new_messages
            
            # Recurse stream
            async for chunk in self._stream_response(kwargs, on_tool_call, tools, new_messages):
                yield chunk
