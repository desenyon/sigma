
"""Exa (Metaphor) Search tool for Sigma."""

import os
import httpx
from typing import Dict, Any, List, Optional
from .registry import TOOL_REGISTRY

EXA_BASE_URL = "https://api.exa.ai"

@TOOL_REGISTRY.register(
    name="search_exa",
    description="Search the web using Exa (formerly Metaphor) for high-quality financial content.",
    provider="exa"
)
async def search_exa(query: str, num_results: int = 5, use_autoprompt: bool = True) -> Dict[str, Any]:
    """
    Search the web using Exa.
    
    Args:
        query: The search query.
        num_results: Number of results to return (default: 5).
        use_autoprompt: Whether to use Exa's autoprompt feature (default: True).
    """
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return {"error": "EXA_API_KEY not found in environment variables."}

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query,
        "numResults": num_results,
        "useAutoprompt": use_autoprompt,
        "contents": {"text": True}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{EXA_BASE_URL}/search", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

@TOOL_REGISTRY.register(
    name="find_similar_exa",
    description="Find similar content using Exa based on a URL.",
    provider="exa"
)
async def find_similar_exa(url: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Find similar content using Exa.
    
    Args:
        url: The URL to find similar content for.
        num_results: Number of results to return (default: 5).
    """
    api_key = os.getenv("EXA_API_KEY")
    if not api_key:
        return {"error": "EXA_API_KEY not found in environment variables."}

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": url,
        "numResults": num_results,
        "contents": {"text": True}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{EXA_BASE_URL}/findSimilar", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
