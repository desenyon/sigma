"""Tests for the Ink bridge actions."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from ephemeral import ink_bridge


def test_status_payload_contains_provider_and_health() -> None:
    payload = ink_bridge._status_payload()
    assert "provider" in payload
    assert "health" in payload
    assert "ollama" in payload
    assert "installed_models" in payload["ollama"]


def test_status_payload_reports_local_ready() -> None:
    with (
        patch("ephemeral.ink_bridge.detect_ollama", return_value=(True, "http://localhost:11434")),
        patch("ephemeral.ink_bridge.list_ollama_model_names", return_value=["qwen2.5:1.5b"]),
        patch("ephemeral.ink_bridge.ollama_has_model", return_value=True),
    ):
        payload = ink_bridge._status_payload()

    assert payload["local_ready"] is True
    assert payload["ollama"]["current_model_available"] is True


def test_quote_payload_raises_without_symbols() -> None:
    try:
        ink_bridge._quote_payload({})
    except ink_bridge.BridgeError as exc:
        assert "requires one or more symbols" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected BridgeError for empty quote payload")


def test_handle_request_set_provider_delegates_to_save_setting() -> None:
    with patch("ephemeral.ink_bridge.save_setting") as save_setting:
        result = asyncio.run(ink_bridge.handle_request({"action": "set-provider", "provider": "ollama"}))
    save_setting.assert_called_once_with("default_provider", "ollama")
    assert result["ok"] is True


def test_help_payload_includes_slash_commands() -> None:
    payload = ink_bridge._help_payload()
    assert "/help" in payload["slash_commands"]
    assert payload["title"] == "Ephemeral Help"


def test_export_payload_writes_markdown(tmp_path) -> None:
    history = [{"label": "Ask", "input": "What changed?", "body": "A short answer."}]
    with patch("ephemeral.ink_bridge.Path.home", return_value=tmp_path):
        result = ink_bridge._export_payload({"history": history})
    export_path = tmp_path / ".ephemeral" / "exports"
    files = list(export_path.glob("ephemeral-ink-*.md"))
    assert result["path"]
    assert files
    assert "What changed?" in files[0].read_text(encoding="utf-8")


def test_engine_payload_delegates_to_engine() -> None:
    with patch("ephemeral.ink_bridge.Engine") as engine_cls:
        engine_cls.return_value.process_query = AsyncMock(return_value={"type": "result", "result": {"ok": True}})
        result = asyncio.run(ink_bridge._engine_payload("report", {"query": "Generate a report for NVDA"}))
    assert result["requested_action"] == "report"
    assert result["engine_result"]["result"]["ok"] is True
