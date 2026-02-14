#!/usr/bin/env python3
"""
Live Integration Test for Sigma v3.6.1
WARNING: This script makes REAL API calls and consumes quota.
"""

import sys
import os
import asyncio
from pathlib import Path

# Ensure we can import sigma
sys.path.insert(0, str(Path(__file__).parent.parent))

from sigma.config import get_settings, LLMProvider
from sigma.tools.registry import TOOL_REGISTRY
from sigma.llm.router import LLMRouter

async def test_live_integrations():
    settings = get_settings()
    print(f"Loaded Settings. Default Provider: {settings.default_provider}")
    
    results = {}
    
    # 1. Test Alpha Vantage
    if settings.alpha_vantage_api_key:
        print("\n[TEST] Alpha Vantage (Live)...")
        try:
            tool = TOOL_REGISTRY.get_tool("get_stock_quote")
            # Using 'IBM' as it's often free/safe for AV
            res = tool.func(symbol="IBM")
            if "error" in res:
                print(f"  [FAIL] {res['error']}")
                results["Alpha Vantage"] = False
            else:
                price = res.get("price") or res.get("Global Quote", {}).get("05. price")
                print(f"  [PASS] Price: {price}")
                results["Alpha Vantage"] = True
        except Exception as e:
            print(f"  [ERR] {e}")
            results["Alpha Vantage"] = False
    else:
        print("\n[SKIP] Alpha Vantage (No Key)")

    # 2. Test Polygon
    if settings.polygon_api_key:
        print("\n[TEST] Polygon.io (Live)...")
        try:
            tool = TOOL_REGISTRY.get_tool("polygon_get_quote")
            # Use async if the tool is async, but registry wraps them.
            # Most tools in library.py are sync, but let's check.
            # polygon tools are usually sync in this codebase based on previous reads.
            res = tool.func(symbol="AAPL")
            
            # Check if it's a coroutine
            if asyncio.iscoroutine(res):
                res = await res
                
            if "error" in res:
                print(f"  [FAIL] {res['error']}")
                results["Polygon"] = False
            else:
                print(f"  [PASS] Data received")
                results["Polygon"] = True
        except Exception as e:
            print(f"  [ERR] {e}")
            results["Polygon"] = False
    else:
        print("\n[SKIP] Polygon (No Key)")

    # 3. Test Exa
    if settings.exa_api_key:
        print("\n[TEST] Exa Search (Live)...")
        try:
            tool = TOOL_REGISTRY.get_tool("search_exa")
            res = tool.func(query="latest stock market news")
            
            if asyncio.iscoroutine(res):
                res = await res
                
            if "error" in res:
                print(f"  [FAIL] {res['error']}")
                results["Exa"] = False
            else:
                count = len(res.get("results", []))
                print(f"  [PASS] Got {count} results")
                results["Exa"] = True
        except Exception as e:
            print(f"  [ERR] {e}")
            results["Exa"] = False
    else:
        print("\n[SKIP] Exa (No Key)")

    # 4. Test LLM Generation
    print(f"\n[TEST] LLM Generation ({settings.default_provider})...")
    try:
        router = LLMRouter(settings)
        messages = [{"role": "user", "content": "Say 'Sigma works' and nothing else."}]
        
        # Access provider directly for test
        provider_name = settings.default_provider.value if hasattr(settings.default_provider, 'value') else settings.default_provider
        provider_client = router.providers.get(provider_name)
        
        if provider_client:
            # Most providers return an object with 'content' attribute or string
            # Check the signature of generate in router.py: return await client.generate(...)
            # If stream=True by default in chat, we might need to handle async iterator.
            # But let's call generate directly on the provider client if possible.
            
            # Use router.chat instead as it handles logic
            response = await router.chat(messages=messages, stream=False)
            
            # Response might be a string or object depending on implementation
            print(f"  [PASS] Response: {response}")
            results["LLM"] = True
        else:
            print(f"  [FAIL] Provider {provider_name} not initialized in router. Available: {list(router.providers.keys())}")
            results["LLM"] = False
    except Exception as e:
        print(f"  [ERR] {e}")
        results["LLM"] = False

    # Summary
    print("\n" + "="*30)
    print("LIVE TEST SUMMARY")
    print("="*30)
    all_pass = True
    for k, v in results.items():
        status = "PASS" if v else "FAIL"
        print(f"{k}: {status}")
        if not v: all_pass = False
    
    return all_pass

if __name__ == "__main__":
    success = asyncio.run(test_live_integrations())
    if not success:
        sys.exit(1)
