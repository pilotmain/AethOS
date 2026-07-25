# SPDX-License-Identifier: Apache-2.0
"""Model Foundry serve → governed approval inbox → execute → chat catalog.

Covers the dead-end fix: a serve request must appear in the Mission Control
approval inbox, have a real execute path (no silent no-op), and register the
served model into the chat model picker.
"""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.llm.model_catalog import list_available_models
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
from aethos_core.mission_control.approval_inbox import serve_approval_execution_service as serve_exec
from aethos_core.mission_control.approval_inbox.approval_audit_service import clear_ui_approval_audit_for_tests
from aethos_core.workspace_suite import model_foundry


@pytest.fixture(autouse=True)
def _enable_foundry(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_FOUNDRY_ENABLED", "true")
    monkeypatch.setenv("WORKSPACE_SUITE_STORE_DIR", str(tmp_path / "ws"))
    get_settings.cache_clear()
    model_foundry.clear_foundry_for_tests()
    clear_ui_approval_audit_for_tests()
    yield
    model_foundry.clear_foundry_for_tests()
    clear_ui_approval_audit_for_tests()
    get_settings.cache_clear()


def _serve(model_id: str = "qwen2.5-14b", port: int = 11434) -> str:
    res = model_foundry.create_serve_preflight(model_id=model_id, port=port)
    assert res["ok"], res
    return str(res["serve_request"]["id"])


# ── Step 1: serve request appears as a pending governed inbox item ──────────────


def test_serve_request_appears_in_approval_inbox():
    _serve()
    inbox = build_approval_inbox(session_id="op-foundry")
    assert inbox.ok
    serve_items = [i for i in inbox.items if i.get("lane") == "model_foundry"]
    assert len(serve_items) == 1
    item = serve_items[0]
    assert item["gate_id"] == "model_serve"
    assert item["serve_execution_enabled"] is True
    assert "qwen2.5-14b" in item["blast_radius"]["model_id"]
    assert item["blast_radius"]["bind"] == "127.0.0.1"
    assert "loopback" in item["blast_radius"]["description"].lower()


def test_serve_request_hidden_when_foundry_disabled(monkeypatch):
    _serve()
    monkeypatch.setenv("MODEL_FOUNDRY_ENABLED", "false")
    get_settings.cache_clear()
    inbox = build_approval_inbox(session_id="op-foundry")
    assert [i for i in inbox.items if i.get("lane") == "model_foundry"] == []


# ── §1: hardware scan never silently reports 0 RAM ──────────────────────────────


def test_scan_hardware_reports_real_memory_not_zero():
    """psutil + OS-native fallbacks → real RAM, never a silent 0 that zeroes fit."""
    hw = model_foundry.scan_hardware()
    assert hw["ok"] is True
    # On any real CI/dev host RAM is detectable (psutil or sysctl/proc fallback).
    assert hw["detection_unavailable"] is False
    assert isinstance(hw["total_ram_gb"], float) and hw["total_ram_gb"] > 0
    assert hw["usable_vram_gb"] > 0
    rec = model_foundry.recommend_models()
    assert rec["model_count"] > 0
    # Not every model should be "no" when hardware is genuinely detected.
    assert any(m["verdict"] != "no" for m in rec["models"])


def test_scan_hardware_detection_unavailable_is_honest(monkeypatch):
    """When detection genuinely fails, say so — don't report 0 or mark all 'no'."""
    monkeypatch.setattr(model_foundry, "_detect_total_ram_bytes", lambda system: 0)
    hw = model_foundry.scan_hardware()
    assert hw["ok"] is True
    assert hw["detection_unavailable"] is True
    assert hw["total_ram_gb"] is None
    assert hw["usable_vram_gb"] is None
    rec = model_foundry.recommend_models()
    assert rec["detection_unavailable"] is True
    assert rec["model_count"] == 0
    assert rec["models"] == []


# ── Step 2: execute path is real — clear error when runtime/model absent ────────


def test_execute_serve_without_runtime_returns_actionable_error(monkeypatch):
    _serve()
    inbox = build_approval_inbox(session_id="op-foundry")
    item = next(i for i in inbox.items if i.get("lane") == "model_foundry")

    monkeypatch.setattr(
        serve_exec,
        "probe_local_serve_runtime",
        lambda **_: {"ok": False, "reason": "local_runtime_unavailable", "available": [], "endpoint": "http://127.0.0.1:11434"},
    )
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-foundry", inbox_id=item["inbox_id"])
    assert result.ok is False
    assert result.blockers == ["local_runtime_unavailable"]
    assert "runtime" in result.detail.lower()
    # Not silently served, and not registered in the catalog.
    assert model_foundry.list_served_models() == []
    assert "local:qwen2.5-14b" not in {r["id"] for r in list_available_models()}


def test_execute_serve_model_not_downloaded_is_actionable(monkeypatch):
    _serve()
    inbox = build_approval_inbox(session_id="op-foundry")
    item = next(i for i in inbox.items if i.get("lane") == "model_foundry")

    monkeypatch.setattr(
        serve_exec,
        "probe_local_serve_runtime",
        lambda **_: {"ok": False, "reason": "model_not_downloaded", "available": ["llama3.2:latest"], "endpoint": "http://127.0.0.1:11434"},
    )
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-foundry", inbox_id=item["inbox_id"])
    assert result.ok is False
    assert result.blockers == ["model_not_downloaded"]
    assert "ollama pull" in result.detail.lower() or "pull" in result.detail.lower()
    assert model_foundry.list_served_models() == []


def test_execute_serve_missing_item_404_marker():
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-foundry", inbox_id="msf-nope")
    assert result.ok is False
    assert result.blockers == ["inbox_item_not_found"]


# ── Step 2 + 3: successful serve marks served and registers the catalog entry ───


def test_execute_serve_success_marks_served_and_registers_catalog(monkeypatch):
    req_id = _serve()
    inbox = build_approval_inbox(session_id="op-foundry")
    item = next(i for i in inbox.items if i.get("lane") == "model_foundry")

    monkeypatch.setattr(
        serve_exec,
        "probe_local_serve_runtime",
        lambda **_: {"ok": True, "reason": "", "available": ["qwen2.5:14b"], "endpoint": "http://127.0.0.1:11434"},
    )
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-foundry", inbox_id=item["inbox_id"])
    assert result.ok is True
    assert result.execution_status == "served"
    assert result.catalog_id == "local:qwen2.5-14b"
    assert result.endpoint == "http://127.0.0.1:11434"

    record = model_foundry.get_serve_request(req_id)
    assert record["status"] == "served"
    assert record["executed"] is True
    assert record["endpoint"] == "http://127.0.0.1:11434"

    # Now in the chat model picker as a configured local entry.
    picker = list_available_models()
    served = [r for r in picker if r["id"] == "local:qwen2.5-14b"]
    assert len(served) == 1
    assert served[0]["configured"] is True
    assert served[0]["provider"] == "local"
    assert "(local)" in served[0]["label"]

    # No longer pending in the inbox.
    inbox2 = build_approval_inbox(session_id="op-foundry")
    assert [i for i in inbox2.items if i.get("lane") == "model_foundry"] == []

    # Idempotent re-execute is a safe no-op.
    again = serve_exec.execute_serve_preflight_from_inbox(session_id="op-foundry", inbox_id=item["inbox_id"])
    # Item is gone from inbox after serving, so re-execute reports not found — never a silent mutation.
    assert again.ok is False
    assert again.blockers == ["inbox_item_not_found"]


# ── Step 4: governed stop removes the served catalog entry ──────────────────────


def test_stop_serve_removes_catalog_entry(monkeypatch):
    req_id = _serve()
    inbox = build_approval_inbox(session_id="op-foundry")
    item = next(i for i in inbox.items if i.get("lane") == "model_foundry")
    monkeypatch.setattr(
        serve_exec,
        "probe_local_serve_runtime",
        lambda **_: {"ok": True, "reason": "", "available": ["qwen2.5:14b"], "endpoint": "http://127.0.0.1:11434"},
    )
    serve_exec.execute_serve_preflight_from_inbox(session_id="op-foundry", inbox_id=item["inbox_id"])
    assert "local:qwen2.5-14b" in {r["id"] for r in list_available_models()}

    stop = model_foundry.stop_serve(req_id=req_id)
    assert stop["ok"] is True
    assert "local:qwen2.5-14b" not in {r["id"] for r in list_available_models()}
    assert model_foundry.list_served_models() == []


def test_serve_status_payload_tracks_lifecycle(monkeypatch):
    req_id = _serve()
    status = model_foundry.serve_status_payload()
    assert status["ok"] is True
    row = next(r for r in status["serve_requests"] if r["id"] == req_id)
    assert row["status"] == "pending_approval"
    assert row["label"] == "Qwen2.5 14B"


# ── probe parser unit coverage (no network) ─────────────────────────────────────


def test_probe_parsers_and_match():
    assert serve_exec._parse_ollama_tags({"models": [{"name": "qwen2.5:14b"}]}) == ["qwen2.5:14b"]
    assert serve_exec._parse_openai_models({"data": [{"id": "qwen2.5-14b"}]}) == ["qwen2.5-14b"]
    assert serve_exec._model_present("qwen2.5-14b", ["qwen2.5:14b"]) is True
    assert serve_exec._model_present("qwen2.5-14b", ["llama3.2:latest"]) is False
