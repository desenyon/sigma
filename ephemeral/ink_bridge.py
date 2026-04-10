"""Machine-readable bridge for the Ink frontend."""

from __future__ import annotations

import asyncio
import copy
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from ephemeral.config import (
    AVAILABLE_MODELS,
    detect_lean_installation,
    detect_ollama,
    get_settings,
    list_ollama_model_names,
    needs_llm_setup,
    ollama_has_model,
    save_api_key,
    save_setting,
)
from ephemeral.ink_launcher import ink_dependencies_ready, ink_ui_root, install_hint
from ephemeral.services.health import collect_service_health


class BridgeError(Exception):
    """Structured bridge failure."""


Engine = None
STATUS_CACHE_TTL_SECONDS = 1.5
_PAYLOAD_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}


def _engine_cls():
    global Engine
    if Engine is None:
        from ephemeral.core.engine import Engine as _Engine

        Engine = _Engine
    return Engine


def _mask_secret(value: str | None) -> str:
    if not value:
        return "missing"
    if len(value) <= 8:
        return "set"
    return f"{value[:4]}...{value[-4:]}"


def _build_markdown_export(payload: Dict[str, Any]) -> str:
    body = str(payload.get("content") or "").strip()
    if body:
        return body

    history = payload.get("history") or []
    lines = [
        "# Ephemeral Session",
        "",
        f"_Exported: {datetime.now().isoformat(timespec='seconds')}_",
        "",
    ]
    for entry in history:
        label = str(entry.get("label") or "Entry")
        user_input = str(entry.get("input") or "").strip()
        body_text = str(entry.get("body") or entry.get("error") or "").strip()
        lines.append(f"## {label}")
        if user_input:
            lines.append("")
            lines.append(f"**Input:** `{user_input}`")
        if body_text:
            lines.append("")
            lines.append(body_text)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _cached_payload(key: str, builder, ttl_seconds: float = STATUS_CACHE_TTL_SECONDS) -> Dict[str, Any]:
    now = time.monotonic()
    cached = _PAYLOAD_CACHE.get(key)
    if cached and now - cached[0] <= ttl_seconds:
        return copy.deepcopy(cached[1])

    payload = builder()
    _PAYLOAD_CACHE[key] = (now, payload)
    return copy.deepcopy(payload)


def _invalidate_cached_payloads() -> None:
    _PAYLOAD_CACHE.clear()


def _status_payload() -> Dict[str, Any]:
    settings = get_settings()
    health = collect_service_health(settings)
    ollama_reachable, detected_host = detect_ollama()
    ollama_host = detected_host or settings.ollama_host
    installed_models = list_ollama_model_names(ollama_host) if ollama_reachable else []
    current_model = settings.default_model
    current_model_available = ollama_has_model(ollama_host, current_model) if current_model else False

    return {
        "provider": settings.default_provider.value,
        "model": current_model,
        "needs_setup": needs_llm_setup(settings),
        "local_ready": ollama_reachable and current_model_available,
        "ollama": {
            "reachable": ollama_reachable,
            "host": ollama_host,
            "current_model_available": current_model_available,
            "installed_models": installed_models[:8],
        },
        "lean": {
            "installed": detect_lean_installation()[0],
        },
        "health": health.to_dict(),
        "available_models": AVAILABLE_MODELS,
        "ink": {
            "ui_root": str(ink_ui_root()),
            "node_available": bool(shutil.which("node")),
            "dependencies_ready": ink_dependencies_ready(),
            "install_hint": install_hint(),
        },
    }


def _doctor_payload() -> Dict[str, Any]:
    settings = get_settings()
    health = collect_service_health(settings)
    return {
        "status": _status_payload(),
        "checks": health.to_dict()["checks"],
        "router_backends": health.router_backends,
    }


def _help_payload() -> Dict[str, Any]:
    from ephemeral.core.engine import AutocompleteEngine

    return {
        "title": "Ephemeral Help",
        "body": (
            "Ink is the primary interactive CLI. Keep the navigator on the left, the active result in the "
            "workspace, and the composer at the bottom for every command."
        ),
        "slash_commands": list(AutocompleteEngine.COMMANDS),
        "tips": [
            "Use natural language with Ask for thesis work, catalysts, and portfolio questions.",
            "Use Quote, News, Compare, Chart, and Backtest for direct market workflows.",
            "Use the composer with Up and Down when empty to switch actions quickly.",
            "Use slash commands any time you want to bypass the selected action.",
        ],
    }


def _shortcuts_payload() -> Dict[str, Any]:
    return {
        "title": "Shortcuts",
        "items": [
            {"key": "Enter", "action": "Run the current action or slash command"},
            {"key": "Tab", "action": "Rotate between navigator, history, result, and composer"},
            {"key": "Up / Down", "action": "Move the highlighted action when the composer is empty"},
            {"key": "Esc", "action": "Clear the current input"},
            {"key": "Ctrl+L", "action": "Clear history"},
            {"key": "Ctrl+C", "action": "Quit"},
        ],
    }


def _keys_payload() -> Dict[str, Any]:
    settings = get_settings()
    rows = [
        {"provider": "google", "status": _mask_secret(settings.google_api_key)},
        {"provider": "openai", "status": _mask_secret(settings.openai_api_key)},
        {"provider": "anthropic", "status": _mask_secret(settings.anthropic_api_key)},
        {"provider": "groq", "status": _mask_secret(settings.groq_api_key)},
        {"provider": "xai", "status": _mask_secret(settings.xai_api_key)},
        {"provider": "polygon", "status": _mask_secret(settings.polygon_api_key)},
        {"provider": "alphavantage", "status": _mask_secret(settings.alpha_vantage_api_key)},
        {"provider": "exa", "status": _mask_secret(settings.exa_api_key)},
    ]
    return {
        "title": "API Keys",
        "rows": rows,
        "configured": sum(1 for row in rows if row["status"] != "missing"),
    }


def _setup_help_payload() -> Dict[str, Any]:
    return {
        "title": "Setup",
        "steps": [
            "Run `npm install --prefix ephemeral/ink_ui` after cloning so the Ink shell can launch.",
            "Run `ephemeral --setkey openai <key>` or save keys in `~/.ephemeral/config.env`.",
            "Set a provider with `ephemeral --provider <provider>`.",
            "Set a model with `ephemeral --model <model-id>`.",
            "Run `ephemeral --status` or open Status in Ink to verify routing.",
            "If you prefer local models, start Ollama and select one of the models already installed or pull a model such as `qwen3.5:8b`.",
        ],
        "docs_url": "https://github.com/desenyon/ephemeral#readme",
    }


def _reload_payload() -> Dict[str, Any]:
    from ephemeral.llm import get_router

    settings = get_settings()
    health = collect_service_health(settings, router_factory=lambda: get_router(settings, force=True))
    status = _status_payload()
    status["health"] = health.to_dict()
    return {
        "title": "Router reloaded",
        "status": status,
    }


async def _ask_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    from ephemeral.app import SYSTEM_PROMPT
    from ephemeral.llm import get_router
    from ephemeral.llm.tool_guidance import USER_TOOL_NUDGE, build_augmented_system_prompt
    from ephemeral.tools import execute_tool, get_tools_for_llm
    from ephemeral.tools.registry import TOOL_REGISTRY

    query = str(payload.get("query") or "").strip()
    if not query:
        raise BridgeError("`ask` requires a non-empty query.")

    settings = get_settings()
    router = get_router(settings, force=True)
    tool_calls: List[Dict[str, Any]] = []

    async def handle_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        result = execute_tool(name, args)
        tool_calls.append({"name": name, "args": args, "result": result})
        return result

    user_text = query + USER_TOOL_NUDGE if settings.ephemeral_aggressive_tools else query
    messages = [
        {
            "role": "system",
            "content": build_augmented_system_prompt(SYSTEM_PROMPT, TOOL_REGISTRY),
        },
        {"role": "user", "content": user_text},
    ]
    response = await router.chat(
        messages,
        tools=get_tools_for_llm(),
        on_tool_call=handle_tool,
        stream=False,
    )
    return {
        "query": query,
        "response": str(response),
        "tool_calls": tool_calls,
        "provider": settings.default_provider.value,
        "model": settings.default_model,
    }


def _quote_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    from ephemeral.tools import get_stock_quote

    symbols = [str(symbol).upper() for symbol in payload.get("symbols") or [] if str(symbol).strip()]
    if not symbols:
        raise BridgeError("`quote` requires one or more symbols.")
    return {"quotes": [get_stock_quote(symbol) for symbol in symbols]}


def _news_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    from ephemeral.tools.library import fetch_news_digest

    symbol = str(payload.get("symbol") or "").upper().strip()
    query = str(payload.get("query") or "").strip()
    limit = int(payload.get("limit") or 10)
    if not symbol and not query:
        raise BridgeError("`news` requires a symbol or query.")
    return fetch_news_digest(symbol=symbol, query=query, limit=limit)


def _compare_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    from ephemeral.tools import compare_stocks

    symbols = [str(symbol).upper() for symbol in payload.get("symbols") or [] if str(symbol).strip()]
    if len(symbols) < 2:
        raise BridgeError("`compare` requires at least two symbols.")
    period = str(payload.get("period") or "1y")
    return compare_stocks(symbols, period=period)


def _chart_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    import yfinance as yf

    from ephemeral.charts import create_candlestick_chart, create_comparison_chart

    symbol = str(payload.get("symbol") or "").upper().strip()
    period = str(payload.get("period") or "6mo")
    compare_symbols = [
        str(item).upper()
        for item in payload.get("symbols") or []
        if str(item).strip()
    ]
    if compare_symbols:
        histories: Dict[str, Any] = {}
        for ticker in compare_symbols:
            hist = yf.Ticker(ticker).history(period=period)
            if not hist.empty:
                histories[ticker] = hist
        if not histories:
            raise BridgeError("No chart data was returned for the requested symbols.")
        chart_path = create_comparison_chart(list(histories.keys()), histories, normalize=True)
        return {"chart_path": chart_path, "symbols": list(histories.keys()), "period": period}

    if not symbol:
        raise BridgeError("`chart` requires a symbol.")
    history = yf.Ticker(symbol).history(period=period)
    if history.empty:
        raise BridgeError(f"No chart data found for {symbol}.")
    chart_path = create_candlestick_chart(symbol, history)
    return {
        "chart_path": chart_path,
        "symbol": symbol,
        "period": period,
        "rows": int(history.shape[0]),
    }


def _backtest_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    from ephemeral.backtest import get_available_strategies, run_backtest

    symbol = str(payload.get("symbol") or "").upper().strip()
    strategy = str(payload.get("strategy") or "sma_crossover").strip()
    period = str(payload.get("period") or "1y")
    if not symbol:
        raise BridgeError("`backtest` requires a symbol.")
    return {
        "available_strategies": get_available_strategies(),
        "result": run_backtest(symbol, strategy, period),
    }


def _models_payload() -> Dict[str, Any]:
    settings = get_settings()
    return {
        "default_provider": settings.default_provider.value,
        "default_model": settings.default_model,
        "providers": AVAILABLE_MODELS,
    }


def _tools_payload() -> Dict[str, Any]:
    from ephemeral.tools.registry import TOOL_REGISTRY

    return {"tools": sorted(TOOL_REGISTRY.get_tool_names())}


async def _engine_payload(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    query = str(payload.get("query") or "").strip()
    if not query:
        raise BridgeError(f"`{action}` requires a prompt, symbol list, or thesis input.")

    engine = _engine_cls()()
    result = await engine.process_query(query)
    return {
        "requested_action": action,
        "query": query,
        "engine_result": result,
    }


def _export_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    body = _build_markdown_export(payload)
    output_dir = Path.home() / ".ephemeral" / "exports"
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"ephemeral-ink-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    target.write_text(body, encoding="utf-8")
    return {
        "title": "Export complete",
        "path": str(target),
        "characters": len(body),
    }


def _set_provider_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    provider = str(payload.get("provider") or "").strip().lower()
    if not provider:
        raise BridgeError("`set-provider` requires a provider.")
    save_setting("default_provider", provider)
    return _status_payload()


def _set_model_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    model = str(payload.get("model") or "").strip()
    if not model:
        raise BridgeError("`set-model` requires a model id.")
    save_setting("default_model", model)
    return _status_payload()


def _set_key_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    provider = str(payload.get("provider") or "").strip().lower()
    key = str(payload.get("key") or "").strip()
    if not provider or not key:
        raise BridgeError("`set-key` requires both provider and key.")
    if not save_api_key(provider, key):
        raise BridgeError(f"Unknown provider `{provider}`.")
    return {"provider": provider, "saved": True}


def _legacy_ui_payload() -> Dict[str, Any]:
    return {
        "command": [sys.executable, "-m", "ephemeral.cli", "--legacy-ui"],
        "cwd": str(Path.cwd()),
    }


async def handle_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    if not action:
        raise BridgeError("Bridge payload is missing an action.")

    if action == "help":
        data = _cached_payload("help", _help_payload, ttl_seconds=300)
    elif action == "shortcuts":
        data = _cached_payload("shortcuts", _shortcuts_payload, ttl_seconds=300)
    elif action == "keys":
        data = _keys_payload()
    elif action == "setup-help":
        data = _cached_payload("setup-help", _setup_help_payload, ttl_seconds=300)
    elif action == "reload":
        _invalidate_cached_payloads()
        data = _reload_payload()
    elif action == "status":
        data = _cached_payload("status", _status_payload)
    elif action == "doctor":
        data = _cached_payload("doctor", _doctor_payload)
    elif action == "ask":
        data = await _ask_payload(payload)
    elif action == "quote":
        data = _quote_payload(payload)
    elif action == "news":
        data = _news_payload(payload)
    elif action == "compare":
        data = _compare_payload(payload)
    elif action == "chart":
        data = _chart_payload(payload)
    elif action == "backtest":
        data = _backtest_payload(payload)
    elif action == "models":
        data = _cached_payload("models", _models_payload, ttl_seconds=60)
    elif action == "tools":
        data = _cached_payload("tools", _tools_payload, ttl_seconds=60)
    elif action == "portfolio":
        data = await _engine_payload(action, payload)
    elif action == "strategy":
        data = await _engine_payload(action, payload)
    elif action == "report":
        data = await _engine_payload(action, payload)
    elif action == "alert":
        data = await _engine_payload(action, payload)
    elif action == "export":
        data = _export_payload(payload)
    elif action == "set-provider":
        data = _set_provider_payload(payload)
        _invalidate_cached_payloads()
    elif action == "set-model":
        data = _set_model_payload(payload)
        _invalidate_cached_payloads()
    elif action == "set-key":
        data = _set_key_payload(payload)
        _invalidate_cached_payloads()
    elif action == "legacy-ui":
        data = _legacy_ui_payload()
    else:
        raise BridgeError(f"Unknown bridge action `{action}`.")

    return {"ok": True, "action": action, "data": data}


async def handle_packet(packet: Dict[str, Any]) -> Dict[str, Any]:
    request_id = packet.get("id")
    payload = packet.get("payload", packet)
    if not isinstance(payload, dict):
        raise BridgeError("Bridge packet payload must be a JSON object.")

    response = await handle_request(payload)
    if request_id is None:
        return response
    return {"id": request_id, **response}


def _serialize_response(response: Dict[str, Any], *, pretty: bool = False) -> str:
    return json.dumps(response, indent=2 if pretty else None, default=str)


def _write_response(response: Dict[str, Any], *, pretty: bool = False) -> None:
    sys.stdout.write(_serialize_response(response, pretty=pretty))
    sys.stdout.write("\n")
    sys.stdout.flush()


def serve_forever() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            packet = json.loads(line)
            response = asyncio.run(handle_packet(packet))
        except BridgeError as exc:
            response = {"ok": False, "error": str(exc)}
        except Exception as exc:  # pragma: no cover - defensive bridge boundary
            response = {"ok": False, "error": str(exc)}

        _write_response(response, pretty=False)

    return 0


def main() -> int:
    try:
        if "--server" in sys.argv:
            return serve_forever()

        payload = json.load(sys.stdin)
        result = asyncio.run(handle_request(payload))
        _write_response(result, pretty=True)
        return 0
    except BridgeError as exc:
        _write_response({"ok": False, "error": str(exc)})
        return 1
    except Exception as exc:  # pragma: no cover - defensive bridge boundary
        _write_response({"ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
