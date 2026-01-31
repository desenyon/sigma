"""LLM provider implementations."""

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional

import httpx

from sigma.core.config import LLMProvider, get_settings
from sigma.core.models import Message, MessageRole, ToolCall


class BaseLLM(ABC):
    """Base LLM provider."""
    
    def __init__(self, model: Optional[str] = None):
        self.settings = get_settings()
        self.model = model or self.settings.get_model(self.provider)
    
    @property
    @abstractmethod
    def provider(self) -> LLMProvider:
        """Provider type."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> tuple[str, list[ToolCall]]:
        """Generate response."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        """Stream response."""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI provider."""
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OPENAI
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert to OpenAI format."""
        result = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.name:
                m["name"] = msg.name
            result.append(m)
        return result
    
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> tuple[str, list[ToolCall]]:
        api_key = self.settings.get_api_key(LLMProvider.OPENAI)
        if not api_key:
            raise ValueError("OpenAI API key not set")
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature or self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
        }
        
        if tools:
            data["tools"] = [{"type": "function", "function": t} for t in tools]
            data["tool_choice"] = "auto"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
            )
            resp.raise_for_status()
            result = resp.json()
        
        choice = result["choices"][0]
        msg = choice["message"]
        content = msg.get("content", "") or ""
        
        tool_calls = []
        if "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=json.loads(tc["function"]["arguments"]),
                ))
        
        return content, tool_calls
    
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        api_key = self.settings.get_api_key(LLMProvider.OPENAI)
        if not api_key:
            raise ValueError("OpenAI API key not set")
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature or self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
            "stream": True,
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        payload = line[6:]
                        if payload == "[DONE]":
                            break
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]


class AnthropicLLM(BaseLLM):
    """Anthropic provider."""
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.ANTHROPIC
    
    def _convert_messages(self, messages: list[Message]) -> tuple[Optional[str], list[dict]]:
        """Convert to Anthropic format."""
        system = None
        result = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system = msg.content
                continue
            
            if msg.role == MessageRole.TOOL:
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id,
                        "content": msg.content,
                    }]
                })
            elif msg.tool_calls:
                content: list[dict[str, Any]] = []
                if msg.content:
                    content.append({"type": "text", "text": msg.content})
                for tc in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.arguments,
                    })
                result.append({"role": "assistant", "content": content})
            else:
                result.append({"role": msg.role.value, "content": msg.content})
        
        return system, result
    
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> tuple[str, list[ToolCall]]:
        api_key = self.settings.get_api_key(LLMProvider.ANTHROPIC)
        if not api_key:
            raise ValueError("Anthropic API key not set")
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        system, msgs = self._convert_messages(messages)
        data: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": self.settings.max_tokens,
            "temperature": temperature or self.settings.temperature,
        }
        
        if system:
            data["system"] = system
        
        if tools:
            data["tools"] = [
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": t.get("parameters", {}),
                }
                for t in tools
            ]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
            )
            resp.raise_for_status()
            result = resp.json()
        
        content = ""
        tool_calls = []
        
        for block in result.get("content", []):
            if block["type"] == "text":
                content += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append(ToolCall(
                    id=block["id"],
                    name=block["name"],
                    arguments=block["input"],
                ))
        
        return content, tool_calls
    
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        api_key = self.settings.get_api_key(LLMProvider.ANTHROPIC)
        if not api_key:
            raise ValueError("Anthropic API key not set")
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        
        system, msgs = self._convert_messages(messages)
        data: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": self.settings.max_tokens,
            "temperature": temperature or self.settings.temperature,
            "stream": True,
        }
        
        if system:
            data["system"] = system
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        event = json.loads(line[6:])
                        if event["type"] == "content_block_delta":
                            delta = event.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")


class GoogleLLM(BaseLLM):
    """Google Gemini provider using REST API."""
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GOOGLE
    
    def _convert_messages(self, messages: list[Message]) -> tuple[Optional[str], list[dict]]:
        """Convert to Gemini format."""
        system = None
        contents = []
        
        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                system = msg.content
                continue
            
            role = "model" if msg.role == MessageRole.ASSISTANT else "user"
            
            if msg.role == MessageRole.TOOL:
                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.name or "tool",
                            "response": {"result": msg.content}
                        }
                    }]
                })
            elif msg.tool_calls:
                parts: list[dict[str, Any]] = []
                if msg.content:
                    parts.append({"text": msg.content})
                for tc in msg.tool_calls:
                    parts.append({
                        "functionCall": {
                            "name": tc.name,
                            "args": tc.arguments
                        }
                    })
                contents.append({"role": role, "parts": parts})
            else:
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })
        
        return system, contents
    
    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert tools to Gemini format."""
        declarations = []
        for t in tools:
            decl: dict[str, Any] = {
                "name": t["name"],
                "description": t.get("description", ""),
            }
            if "parameters" in t and t["parameters"]:
                params = t["parameters"].copy()
                # Gemini doesn't want 'additionalProperties'
                params.pop("additionalProperties", None)
                decl["parameters"] = params
            declarations.append(decl)
        return [{"functionDeclarations": declarations}]
    
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> tuple[str, list[ToolCall]]:
        api_key = self.settings.get_api_key(LLMProvider.GOOGLE)
        if not api_key:
            raise ValueError("Google API key not set")
        
        system, contents = self._convert_messages(messages)
        
        data: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature or self.settings.temperature,
                "maxOutputTokens": self.settings.max_tokens,
            }
        }
        
        if system:
            data["systemInstruction"] = {"parts": [{"text": system}]}
        
        if tools:
            data["tools"] = self._convert_tools(tools)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={api_key}"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(url, json=data)
            resp.raise_for_status()
            result = resp.json()
        
        content = ""
        tool_calls = []
        
        candidates = result.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for i, part in enumerate(parts):
                if "text" in part:
                    content += part["text"]
                elif "functionCall" in part:
                    fc = part["functionCall"]
                    tool_calls.append(ToolCall(
                        id=f"call_{i}",
                        name=fc["name"],
                        arguments=fc.get("args", {}),
                    ))
        
        return content, tool_calls
    
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        api_key = self.settings.get_api_key(LLMProvider.GOOGLE)
        if not api_key:
            raise ValueError("Google API key not set")
        
        system, contents = self._convert_messages(messages)
        
        data: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature or self.settings.temperature,
                "maxOutputTokens": self.settings.max_tokens,
            }
        }
        
        if system:
            data["systemInstruction"] = {"parts": [{"text": system}]}
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?key={api_key}&alt=sse"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=data) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk = json.loads(line[6:])
                        candidates = chunk.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                if "text" in part:
                                    yield part["text"]


class OllamaLLM(BaseLLM):
    """Ollama provider."""
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.OLLAMA
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert to Ollama format."""
        result = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": tc.arguments}
                    }
                    for tc in msg.tool_calls
                ]
            result.append(m)
        return result
    
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> tuple[str, list[ToolCall]]:
        data: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "stream": False,
            "options": {
                "temperature": temperature or self.settings.temperature,
                "num_predict": self.settings.max_tokens,
            }
        }
        
        if tools:
            data["tools"] = [{"type": "function", "function": t} for t in tools]
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{self.settings.ollama_base_url}/api/chat",
                json=data,
            )
            resp.raise_for_status()
            result = resp.json()
        
        msg = result.get("message", {})
        content = msg.get("content", "") or ""
        
        tool_calls = []
        if "tool_calls" in msg and msg["tool_calls"]:
            for i, tc in enumerate(msg["tool_calls"]):
                fn = tc.get("function", {})
                tool_calls.append(ToolCall(
                    id=f"call_{i}",
                    name=fn.get("name", ""),
                    arguments=fn.get("arguments", {}),
                ))
        
        return content, tool_calls
    
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        data: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "stream": True,
            "options": {
                "temperature": temperature or self.settings.temperature,
                "num_predict": self.settings.max_tokens,
            }
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream(
                "POST",
                f"{self.settings.ollama_base_url}/api/chat",
                json=data,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line:
                        chunk = json.loads(line)
                        msg = chunk.get("message", {})
                        if "content" in msg:
                            yield msg["content"]


class GroqLLM(BaseLLM):
    """Groq provider."""
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.GROQ
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert to Groq format (OpenAI compatible)."""
        result = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.name:
                m["name"] = msg.name
            result.append(m)
        return result
    
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> tuple[str, list[ToolCall]]:
        api_key = self.settings.get_api_key(LLMProvider.GROQ)
        if not api_key:
            raise ValueError("Groq API key not set")
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature or self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
        }
        
        if tools:
            data["tools"] = [{"type": "function", "function": t} for t in tools]
            data["tool_choice"] = "auto"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
            )
            resp.raise_for_status()
            result = resp.json()
        
        choice = result["choices"][0]
        msg = choice["message"]
        content = msg.get("content", "") or ""
        
        tool_calls = []
        if "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=json.loads(tc["function"]["arguments"]),
                ))
        
        return content, tool_calls
    
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        api_key = self.settings.get_api_key(LLMProvider.GROQ)
        if not api_key:
            raise ValueError("Groq API key not set")
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature or self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
            "stream": True,
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        payload = line[6:]
                        if payload == "[DONE]":
                            break
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]


class XaiLLM(BaseLLM):
    """xAI Grok provider."""
    
    @property
    def provider(self) -> LLMProvider:
        return LLMProvider.XAI
    
    def _convert_messages(self, messages: list[Message]) -> list[dict]:
        """Convert to xAI format (OpenAI compatible)."""
        result = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role.value, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)}
                    }
                    for tc in msg.tool_calls
                ]
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            result.append(m)
        return result
    
    async def generate(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> tuple[str, list[ToolCall]]:
        api_key = self.settings.get_api_key(LLMProvider.XAI)
        if not api_key:
            raise ValueError("xAI API key not set")
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature or self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
        }
        
        if tools:
            data["tools"] = [{"type": "function", "function": t} for t in tools]
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=data,
            )
            resp.raise_for_status()
            result = resp.json()
        
        choice = result["choices"][0]
        msg = choice["message"]
        content = msg.get("content", "") or ""
        
        tool_calls = []
        if "tool_calls" in msg and msg["tool_calls"]:
            for tc in msg["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=json.loads(tc["function"]["arguments"]),
                ))
        
        return content, tool_calls
    
    async def stream(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
        temperature: Optional[float] = None,
    ) -> AsyncIterator[str]:
        api_key = self.settings.get_api_key(LLMProvider.XAI)
        if not api_key:
            raise ValueError("xAI API key not set")
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data: dict[str, Any] = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": temperature or self.settings.temperature,
            "max_tokens": self.settings.max_tokens,
            "stream": True,
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                "https://api.x.ai/v1/chat/completions",
                headers=headers,
                json=data,
            ) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        payload = line[6:]
                        if payload == "[DONE]":
                            break
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]


def get_llm(provider: Optional[LLMProvider] = None, model: Optional[str] = None) -> BaseLLM:
    """Get LLM instance."""
    settings = get_settings()
    provider = provider or settings.default_provider
    
    providers = {
        LLMProvider.OPENAI: OpenAILLM,
        LLMProvider.ANTHROPIC: AnthropicLLM,
        LLMProvider.GOOGLE: GoogleLLM,
        LLMProvider.OLLAMA: OllamaLLM,
        LLMProvider.GROQ: GroqLLM,
        LLMProvider.XAI: XaiLLM,
    }
    
    cls = providers.get(provider)
    if not cls:
        raise ValueError(f"Unknown provider: {provider}")
    
    return cls(model=model)
