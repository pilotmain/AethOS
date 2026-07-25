# SPDX-License-Identifier: Apache-2.0
"""Model Foundry opt-in autostart + autodownload on approval.

Default-off flags keep verify-only behavior; when on, approval of a specific
serve item authorizes starting the loopback runtime and pulling weights.
"""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
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


def _item(session: str = "op-auto") -> dict:
    inbox = build_approval_inbox(session_id=session)
    return next(i for i in inbox.items if i.get("lane") == "model_foundry")


def _stateful_probe(*returns):
    seq = iter(returns)
    last = returns[-1]

    def _probe(**_):
        nonlocal last
        try:
            last = next(seq)
        except StopIteration:
            pass
        return last

    return _probe


# ── Step 1: tag map ─────────────────────────────────────────────────────────────


def test_ollama_tag_map_covers_catalog_and_rejects_unknown():
    assert model_foundry.ollama_tag_for("qwen2.5-14b") == "qwen2.5:14b"
    assert model_foundry.ollama_tag_for("llama-3.1-8b") == "llama3.1:8b"
    assert model_foundry.ollama_tag_for("does-not-exist") is None
    # Every fit-catalog id must have a tag so autodownload never guesses.
    for entry in model_foundry._MODEL_CATALOG:
        assert model_foundry.ollama_tag_for(entry["id"]), entry["id"]


# ── Step 4: governed item language reflects flags ───────────────────────────────


def test_item_language_flags_off_keeps_forbidden():
    _serve()
    item = _item()
    assert "auto_download_weights" in item["remains_forbidden"]
    assert "runtime_autostart" in item["remains_forbidden"]
    assert "external_bind" in item["remains_forbidden"]
    assert "ungoverned_serve" in item["remains_forbidden"]
    assert not any("download" in u for u in item["unlocks"])
    assert not any("runtime" in u for u in item["unlocks"])


def test_item_language_flags_on_moves_to_unlocks(monkeypatch):
    monkeypatch.setenv("MODEL_FOUNDRY_AUTOSTART_ENABLED", "true")
    monkeypatch.setenv("MODEL_FOUNDRY_AUTODOWNLOAD_ENABLED", "true")
    get_settings.cache_clear()
    _serve()
    item = _item()
    assert any("start loopback runtime" in u for u in item["unlocks"])
    assert any("download model weights" in u and "GB" in u for u in item["unlocks"])
    assert "auto_download_weights" not in item["remains_forbidden"]
    assert "runtime_autostart" not in item["remains_forbidden"]
    # Always forbidden regardless of flags.
    assert "external_bind" in item["remains_forbidden"]
    assert "ungoverned_serve" in item["remains_forbidden"]
    assert item["blast_radius"]["autostart"] is True
    assert item["blast_radius"]["autodownload"] is True


# ── Step 2: autostart ───────────────────────────────────────────────────────────


def test_autostart_off_preserves_verify_only(monkeypatch):
    _serve()
    item = _item()
    monkeypatch.setattr(serve_exec, "probe_local_serve_runtime", _stateful_probe(
        {"ok": False, "reason": "local_runtime_unavailable", "available": [], "endpoint": "http://127.0.0.1:11434"},
    ))
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-auto", inbox_id=item["inbox_id"])
    assert result.ok is False
    assert result.blockers == ["local_runtime_unavailable"]
    assert model_foundry.get_managed_runtime() is None


def test_autostart_on_without_ollama_binary_is_actionable(monkeypatch):
    monkeypatch.setenv("MODEL_FOUNDRY_AUTOSTART_ENABLED", "true")
    get_settings.cache_clear()
    _serve()
    item = _item()
    monkeypatch.setattr(serve_exec, "probe_local_serve_runtime", _stateful_probe(
        {"ok": False, "reason": "local_runtime_unavailable", "available": [], "endpoint": "http://127.0.0.1:11434"},
    ))
    monkeypatch.setattr(model_foundry, "ollama_available", lambda: False)
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-auto", inbox_id=item["inbox_id"])
    assert result.ok is False
    assert result.blockers == ["ollama_not_installed"]
    assert "ollama.com/download" in result.detail


def test_autostart_on_starts_then_serves_when_model_present(monkeypatch):
    monkeypatch.setenv("MODEL_FOUNDRY_AUTOSTART_ENABLED", "true")
    get_settings.cache_clear()
    req_id = _serve()
    item = _item()
    monkeypatch.setattr(model_foundry, "ollama_available", lambda: True)
    started = {}
    monkeypatch.setattr(model_foundry, "start_ollama_runtime", lambda **k: started.update(k) or {"ok": True, "pid": 4242})
    monkeypatch.setattr(serve_exec, "probe_local_serve_runtime", _stateful_probe(
        {"ok": False, "reason": "local_runtime_unavailable", "available": [], "endpoint": "http://127.0.0.1:11434"},
        {"ok": True, "reason": "", "available": ["qwen2.5:14b"], "endpoint": "http://127.0.0.1:11434"},
    ))
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-auto", inbox_id=item["inbox_id"])
    assert result.ok is True
    assert result.execution_status == "served"
    assert model_foundry.get_serve_request(req_id)["status"] == "served"


# ── Step 3: autodownload ────────────────────────────────────────────────────────


def test_autodownload_on_pulls_when_model_missing(monkeypatch):
    monkeypatch.setenv("MODEL_FOUNDRY_AUTODOWNLOAD_ENABLED", "true")
    get_settings.cache_clear()
    req_id = _serve()
    item = _item()
    monkeypatch.setattr(serve_exec, "probe_local_serve_runtime", _stateful_probe(
        {"ok": False, "reason": "model_not_downloaded", "available": ["llama3.2:latest"], "endpoint": "http://127.0.0.1:11434"},
    ))
    monkeypatch.setattr(model_foundry, "free_disk_gb", lambda *a, **k: 999.0)
    pulled = {}
    monkeypatch.setattr(model_foundry, "run_model_pull", lambda **k: pulled.update(k) or {"ok": True})
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-auto", inbox_id=item["inbox_id"])
    assert result.ok is True
    assert result.execution_status == "downloading"
    assert pulled["tag"] == "qwen2.5:14b"
    assert pulled["req_id"] == req_id


def test_autodownload_refuses_on_insufficient_disk(monkeypatch):
    monkeypatch.setenv("MODEL_FOUNDRY_AUTODOWNLOAD_ENABLED", "true")
    get_settings.cache_clear()
    _serve()
    item = _item()
    monkeypatch.setattr(serve_exec, "probe_local_serve_runtime", _stateful_probe(
        {"ok": False, "reason": "model_not_downloaded", "available": [], "endpoint": "http://127.0.0.1:11434"},
    ))
    monkeypatch.setattr(model_foundry, "free_disk_gb", lambda *a, **k: 1.0)
    called = {"pull": False}
    monkeypatch.setattr(model_foundry, "run_model_pull", lambda **k: called.update(pull=True))
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-auto", inbox_id=item["inbox_id"])
    assert result.ok is False
    assert result.blockers == ["insufficient_disk"]
    assert called["pull"] is False


def test_autodownload_off_keeps_actionable_error(monkeypatch):
    _serve()
    item = _item()
    monkeypatch.setattr(serve_exec, "probe_local_serve_runtime", _stateful_probe(
        {"ok": False, "reason": "model_not_downloaded", "available": [], "endpoint": "http://127.0.0.1:11434"},
    ))
    result = serve_exec.execute_serve_preflight_from_inbox(session_id="op-auto", inbox_id=item["inbox_id"])
    assert result.ok is False
    assert result.blockers == ["model_not_downloaded"]


# ── pull worker (sync) marks served + progress ──────────────────────────────────


def test_run_model_pull_sync_marks_served(monkeypatch):
    req_id = _serve()

    class _FakeProc:
        def __init__(self):
            self.stdout = iter(["pulling manifest\n", "pulling 1a2b: 50%\n", "pulling 1a2b: 100%\n"])

        def wait(self):
            return 0

    monkeypatch.setattr(model_foundry.subprocess, "Popen", lambda *a, **k: _FakeProc())
    model_foundry.run_model_pull(req_id=req_id, tag="qwen2.5:14b", port=11434, sync=True)
    record = model_foundry.get_serve_request(req_id)
    assert record["status"] == "served"
    assert record["progress"] == 100
    assert record["endpoint"] == "http://127.0.0.1:11434"
    assert model_foundry.served_model_endpoint("qwen2.5-14b") == "http://127.0.0.1:11434"


def test_run_model_pull_sync_failure_returns_to_pending(monkeypatch):
    req_id = _serve()

    class _FakeProc:
        def __init__(self):
            self.stdout = iter(["pulling manifest\n"])

        def wait(self):
            return 1

    monkeypatch.setattr(model_foundry.subprocess, "Popen", lambda *a, **k: _FakeProc())
    model_foundry.run_model_pull(req_id=req_id, tag="qwen2.5:14b", port=11434, sync=True)
    record = model_foundry.get_serve_request(req_id)
    assert record["status"] == "pending_approval"
    assert record["phase"] == "error"
    assert "pull_exit_1" in record["error"]


# ── Step 5: stop terminates managed runtime + clears catalog ────────────────────


def test_stop_clears_runtime_and_catalog(monkeypatch):
    from aethos_core.llm.model_catalog import list_available_models

    req_id = _serve()
    # Simulate a served model + a managed runtime record (nonexistent pid → handled).
    model_foundry.update_serve_request(
        req_id, status="served", executed=True, served=True, endpoint="http://127.0.0.1:11434"
    )
    store = model_foundry._load_store()
    store["runtime"] = {"pid": 2_000_000_000, "port": 11434, "managed": True}
    model_foundry._save_store(store)
    assert "local:qwen2.5-14b" in {r["id"] for r in list_available_models()}

    stop = model_foundry.stop_serve(req_id=req_id)
    assert stop["ok"] is True
    assert model_foundry.get_managed_runtime() is None
    assert "local:qwen2.5-14b" not in {r["id"] for r in list_available_models()}
