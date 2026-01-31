"""LLM client implementations for all providers."""

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Callable, Optional

from sigma.config import LLMProvider, get_settings


class BaseLLM(ABC):
    """Base class for LLM clients."""
    
    @abstractmethod
    async def generate(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        on_tool_call: Optional[Callable] = None,
    ) -> str:
        """Generate a response."""
        pass


class GoogleLLM(BaseLLM):
    """Google Gemini client."""
    
    def __init__(self, api_key: str, model: str):
        from google import genai
        self.client = genai.Client(api_key=api_key)
        self.model_name = model
    
    async def generate(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        on_tool_call: Optional[Callable] = None,
    ) -> str:
        from google.genai import types
        
        # Extract system prompt and build contents
        system_prompt = None
        contents = []
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_prompt = content
            elif role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=content)]
                ))
            elif role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part(text=content)]
                ))
        
        # Build config
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
        )
        
        # Add tools if provided
        if tools:
            function_declarations = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool["function"]
                    function_declarations.append(types.FunctionDeclaration(
                        name=func["name"],
                        description=func.get("description", ""),
                        parameters=func.get("parameters", {}),
                    ))
            if function_declarations:
                config.tools = [types.Tool(function_declarations=function_declarations)]
        
        # Generate
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )
        
        # Handle function calls
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                # Collect all function calls first
                function_calls = []
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
                
                # If there are function calls, process all of them
                if function_calls and on_tool_call:
                    # Add the model's response with function calls
                    contents.append(candidate.content)
                    
                    # Execute all function calls and build responses
                    function_responses = []
                    for fc in function_calls:
                        args = dict(fc.args) if fc.args else {}
                        result = await on_tool_call(fc.name, args)
                        function_responses.append(types.Part(
                            function_response=types.FunctionResponse(
                                name=fc.name,
                                response={"result": str(result)}
                            )
                        ))
                    
                    # Add all function responses in a single user message
                    contents.append(types.Content(
                        role="user",
                        parts=function_responses
                    ))
                    
                    # Get final response
                    final_response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=config,
                    )
                    
                    # Check if there are more function calls in the response
                    if final_response.candidates:
                        final_candidate = final_response.candidates[0]
                        if final_candidate.content and final_candidate.content.parts:
                            for part in final_candidate.content.parts:
                                if hasattr(part, 'function_call') and part.function_call:
                                    # Recursive call to handle chained tool calls
                                    new_contents = contents + [final_candidate.content]
                                    fc = part.function_call
                                    args = dict(fc.args) if fc.args else {}
                                    result = await on_tool_call(fc.name, args)
                                    new_contents.append(types.Content(
                                        role="user",
                                        parts=[types.Part(
                                            function_response=types.FunctionResponse(
                                                name=fc.name,
                                                response={"result": str(result)}
                                            )
                                        )]
                                    ))
                                    final_final = self.client.models.generate_content(
                                        model=self.model_name,
                                        contents=new_contents,
                                        config=config,
                                    )
                                    return final_final.text or ""
                    
                    return final_response.text or ""
        
        return response.text or ""


class OpenAILLM(BaseLLM):
    """OpenAI client."""
    
    def __init__(self, api_key: str, model: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        on_tool_call: Optional[Callable] = None,
    ) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = await self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        # Handle tool calls
        if message.tool_calls and on_tool_call:
            tool_results = []
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                result = await on_tool_call(tc.function.name, args)
                tool_results.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "content": json.dumps(result)
                })
            
            # Continue with tool results
            messages = messages + [message.model_dump()] + tool_results
            return await self.generate(messages, tools, on_tool_call)
        
        return message.content or ""


class AnthropicLLM(BaseLLM):
    """Anthropic Claude client."""
    
    def __init__(self, api_key: str, model: str):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def generate(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        on_tool_call: Optional[Callable] = None,
    ) -> str:
        # Extract system message
        system = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                filtered_messages.append(msg)
        
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": filtered_messages,
        }
        
        if system:
            kwargs["system"] = system
        
        if tools:
            # Convert to Anthropic format
            kwargs["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters", {})
                }
                for t in tools if t.get("type") == "function"
            ]
        
        response = await self.client.messages.create(**kwargs)
        
        # Handle tool use
        result_text = ""
        for block in response.content:
            if block.type == "text":
                result_text += block.text
            elif block.type == "tool_use" and on_tool_call:
                result = await on_tool_call(block.name, block.input)
                # Continue conversation
                filtered_messages.append({
                    "role": "assistant",
                    "content": response.content
                })
                filtered_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    }]
                })
                return await self.generate(
                    [{"role": "system", "content": system}] + filtered_messages,
                    tools, on_tool_call
                )
        
        return result_text


class GroqLLM(BaseLLM):
    """Groq client."""
    
    def __init__(self, api_key: str, model: str):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=api_key)
        self.model = model
    
    async def generate(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        on_tool_call: Optional[Callable] = None,
    ) -> str:
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = await self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        # Handle tool calls (similar to OpenAI)
        if message.tool_calls and on_tool_call:
            tool_results = []
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                result = await on_tool_call(tc.function.name, args)
                tool_results.append({
                    "tool_call_id": tc.id,
                    "role": "tool",
                    "content": json.dumps(result)
                })
            
            messages = messages + [{"role": "assistant", "tool_calls": message.tool_calls}] + tool_results
            return await self.generate(messages, tools, on_tool_call)
        
        return message.content or ""


class OllamaLLM(BaseLLM):
    """Ollama local client."""
    
    def __init__(self, host: str, model: str):
        self.host = host.rstrip("/")
        self.model = model
    
    async def generate(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        on_tool_call: Optional[Callable] = None,
    ) -> str:
        import aiohttp
        
        # Ollama doesn't support tools natively, so we embed tool info in prompt
        if tools:
            tool_desc = self._format_tools_for_prompt(tools)
            # Prepend to system message
            for i, msg in enumerate(messages):
                if msg["role"] == "system":
                    messages[i]["content"] = f"{msg['content']}\n\n{tool_desc}"
                    break
            else:
                messages.insert(0, {"role": "system", "content": tool_desc})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.host}/api/chat",
                json={"model": self.model, "messages": messages, "stream": False}
            ) as resp:
                data = await resp.json()
                return data.get("message", {}).get("content", "")
    
    def _format_tools_for_prompt(self, tools: list[dict]) -> str:
        """Format tools as text for prompt injection."""
        lines = ["You have access to these tools:"]
        for tool in tools:
            if tool.get("type") == "function":
                f = tool["function"]
                lines.append(f"- {f['name']}: {f.get('description', '')}")
        lines.append("\nTo use a tool, respond with: TOOL_CALL: tool_name(args)")
        return "\n".join(lines)


def get_llm(provider: LLMProvider, model: Optional[str] = None) -> BaseLLM:
    """Get LLM client for a provider."""
    settings = get_settings()
    
    if model is None:
        model = settings.get_model(provider)
    
    if provider == LLMProvider.GOOGLE:
        api_key = settings.google_api_key
        if not api_key:
            raise ValueError("Google API key not configured")
        return GoogleLLM(api_key, model)
    
    elif provider == LLMProvider.OPENAI:
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        return OpenAILLM(api_key, model)
    
    elif provider == LLMProvider.ANTHROPIC:
        api_key = settings.anthropic_api_key
        if not api_key:
            raise ValueError("Anthropic API key not configured")
        return AnthropicLLM(api_key, model)
    
    elif provider == LLMProvider.GROQ:
        api_key = settings.groq_api_key
        if not api_key:
            raise ValueError("Groq API key not configured")
        return GroqLLM(api_key, model)
    
    elif provider == LLMProvider.OLLAMA:
        return OllamaLLM(settings.ollama_host, model)
    
    else:
        raise ValueError(f"Unsupported provider: {provider}")
