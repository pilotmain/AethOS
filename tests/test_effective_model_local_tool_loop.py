# SPDX-License-Identifier: Apache-2.0
"""FIX 1 + FIX 3 — transparent local model use in Agent mode, and serve de-dupe.

Agent mode must NOT silently swap a selected local model for a cloud model:
- When the local runtime can run tools (flag on + reachable endpoint) the tool
  loop keeps the local model.
- A genuine cloud fallback is returned as a *different* model so the caller can
  surface it (never silent).
- The picker gates local entries (`agent_tool_capable`) so it never offers a
  selection it would ignore.

Also covers FIX 3: repeated serve clicks de-dupe to one pending request, and a
pending request can be dismissed.
"""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.llm import model_catalog
from aethos_core.llm.effective_model import (
    EffectiveModel,
    effective_model_for_agent_tool_loop,
    local_tool_loop_capable,
)
from aethos_core.provider import completion as completion_mod
from aethos_core.workspace_suite import model_foundry


@pytest.fixture(autouse=True)
def _clean_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKSPACE_SUITE_STORE_DIR", str(tmp_path / "ws"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _local() -> EffectiveModel:
    return EffectiveModel(
        catalog_id="local:qwen2.5-14b",
        provider="local",
        model="qwen2.5-14b",
        label="Qwen2.5 14B (local)",
        source="session",
    )


def _anthropic_enabled(monkeypatch) -> None:
    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-6")
    get_settings.cache_clear()


# ── FIX 1: local kept for the tool loop when the runtime is tool-capable ─────────


def test_local_kept_when_runtime_tool_capable(monkeypatch):
    monkeypatch.setenv("LOCAL_TOOL_LOOP_ENABLED", "true")
    _anthropic_enabled(monkeypatch)
    monkeypatch.setattr(
        completion_mod, "local_tool_loop_base_url", lambda model: "http://127.0.0.1:11434/v1"
    )
    out = effective_model_for_agent_tool_loop(_local())
    assert out is not None
    assert out.provider == "local"
    assert out.catalog_id == "local:qwen2.5-14b"  # no silent swap


def test_local_capable_helper_tracks_flag_and_endpoint(monkeypatch):
    monkeypatch.setattr(
        completion_mod, "local_tool_loop_base_url", lambda model: "http://127.0.0.1:11434/v1"
    )
    monkeypatch.setenv("LOCAL_TOOL_LOOP_ENABLED", "true")
    get_settings.cache_clear()
    assert local_tool_loop_capable(_local()) is True
    monkeypatch.setenv("LOCAL_TOOL_LOOP_ENABLED", "false")
    get_settings.cache_clear()
    assert local_tool_loop_capable(_local()) is False


# ── FIX 1: honest fallback (never silent) when local can't do tools ──────────────


def test_fallback_to_cloud_is_a_distinct_model_when_flag_off(monkeypatch):
    monkeypatch.setenv("LOCAL_TOOL_LOOP_ENABLED", "false")
    _anthropic_enabled(monkeypatch)
    out = effective_model_for_agent_tool_loop(_local())
    assert out is not None
    assert out.provider == "anthropic"
    # The swap is surfaced because the returned catalog id differs from the selection.
    assert out.catalog_id != "local:qwen2.5-14b"


def test_fallback_when_flag_on_but_no_runtime(monkeypatch):
    monkeypatch.setenv("LOCAL_TOOL_LOOP_ENABLED", "true")
    _anthropic_enabled(monkeypatch)
    monkeypatch.setattr(completion_mod, "local_tool_loop_base_url", lambda model: "")
    out = effective_model_for_agent_tool_loop(_local())
    assert out is not None
    assert out.provider == "anthropic"
    assert out.catalog_id != "local:qwen2.5-14b"


def test_no_fallback_without_cloud_key(monkeypatch):
    monkeypatch.setenv("LOCAL_TOOL_LOOP_ENABLED", "false")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("USE_REAL_LLM", "false")
    get_settings.cache_clear()
    assert effective_model_for_agent_tool_loop(_local()) is None


def test_openrouter_selection_kept_with_vault_key(monkeypatch):
    """Vault-only OpenRouter key must honor selection (not env-only gate)."""
    monkeypatch.setenv("MULTI_PROVIDER_TOOL_LOOP_ENABLED", "true")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    _anthropic_enabled(monkeypatch)
    orr = EffectiveModel(
        catalog_id="openrouter:openai/gpt-4.1-mini",
        provider="openrouter",
        model="openai/gpt-4.1-mini",
        label="OpenRouter · GPT-4.1 Mini",
        source="session",
    )

    def _configured(provider: str) -> bool:
        return provider == "openrouter" or provider == "anthropic"

    monkeypatch.setattr(
        "aethos_core.llm.model_providers.model_provider_configured",
        _configured,
    )
    out = effective_model_for_agent_tool_loop(orr)
    assert out is not None
    assert out.provider == "openrouter"
    assert out.catalog_id == "openrouter:openai/gpt-4.1-mini"


def test_openrouter_selection_kept_for_tool_loop(monkeypatch):
    monkeypatch.setenv("MULTI_PROVIDER_TOOL_LOOP_ENABLED", "true")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test-key")
    _anthropic_enabled(monkeypatch)  # anthropic key present too — must NOT swap
    orr = EffectiveModel(
        catalog_id="openrouter:openai/gpt-4.1-mini",
        provider="openrouter",
        model="openai/gpt-4.1-mini",
        label="OpenRouter · GPT-4.1 Mini",
        source="session",
    )
    out = effective_model_for_agent_tool_loop(orr)
    assert out is not None
    assert out.provider == "openrouter"
    assert out.catalog_id == "openrouter:openai/gpt-4.1-mini"  # honored, not swapped to Anthropic


def test_openrouter_falls_back_when_multi_provider_off(monkeypatch):
    monkeypatch.setenv("MULTI_PROVIDER_TOOL_LOOP_ENABLED", "false")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test-key")
    _anthropic_enabled(monkeypatch)
    orr = EffectiveModel(
        catalog_id="openrouter:openai/gpt-4.1-mini",
        provider="openrouter",
        model="openai/gpt-4.1-mini",
        label="OpenRouter · GPT-4.1 Mini",
        source="session",
    )
    out = effective_model_for_agent_tool_loop(orr)
    assert out is not None
    assert out.provider == "anthropic"  # honest, surfaced fallback


def test_anthropic_selection_kept(monkeypatch):
    _anthropic_enabled(monkeypatch)
    anth = EffectiveModel(
        catalog_id="anthropic:claude-opus-4-6",
        provider="anthropic",
        model="claude-opus-4-6",
        label="Claude Opus 4.6",
        source="session",
    )
    out = effective_model_for_agent_tool_loop(anth)
    assert out is anth


# ── FIX 1: picker gating via agent_tool_capable ─────────────────────────────────


def test_agent_tool_capable_local_tracks_flag(monkeypatch):
    monkeypatch.setenv("LOCAL_TOOL_LOOP_ENABLED", "true")
    get_settings.cache_clear()
    assert model_catalog._agent_tool_capable("local", True) is True
    monkeypatch.setenv("LOCAL_TOOL_LOOP_ENABLED", "false")
    get_settings.cache_clear()
    assert model_catalog._agent_tool_capable("local", True) is False


def test_agent_tool_capable_cloud_and_unconfigured():
    assert model_catalog._agent_tool_capable("anthropic", True) is True
    assert model_catalog._agent_tool_capable("openrouter", True) is True
    assert model_catalog._agent_tool_capable("local", False) is False
    assert model_catalog._agent_tool_capable("template", True) is False


def test_catalog_entries_expose_agent_tool_capable(monkeypatch):
    _anthropic_enabled(monkeypatch)
    rows = model_catalog.list_available_models(include_unconfigured=True)
    assert rows, "expected at least the default entry"
    assert all("agent_tool_capable" in row for row in rows)


# ── FIX 3: serve request de-dupe + dismiss ──────────────────────────────────────


@pytest.fixture()
def _foundry(monkeypatch):
    monkeypatch.setenv("MODEL_FOUNDRY_ENABLED", "true")
    get_settings.cache_clear()
    model_foundry.clear_foundry_for_tests()
    yield
    model_foundry.clear_foundry_for_tests()
    get_settings.cache_clear()


def test_repeated_serve_clicks_dedupe_to_one_pending(_foundry):
    first = model_foundry.create_serve_preflight(model_id="qwen2.5-14b", port=11434)
    assert first["ok"]
    second = model_foundry.create_serve_preflight(model_id="qwen2.5-14b", port=11434)
    assert second["ok"]
    assert second.get("deduped") is True
    assert second["serve_request"]["id"] == first["serve_request"]["id"]
    pending = model_foundry.list_pending_serve_requests()
    assert len(pending) == 1


def test_distinct_port_is_not_deduped(_foundry):
    model_foundry.create_serve_preflight(model_id="qwen2.5-14b", port=11434)
    model_foundry.create_serve_preflight(model_id="qwen2.5-14b", port=11435)
    assert len(model_foundry.list_pending_serve_requests()) == 2


def test_dismiss_removes_pending_request(_foundry):
    res = model_foundry.create_serve_preflight(model_id="qwen2.5-14b", port=11434)
    req_id = res["serve_request"]["id"]
    out = model_foundry.dismiss_serve_request(req_id)
    assert out["ok"] is True
    assert model_foundry.list_pending_serve_requests() == []


def test_dismiss_unknown_request_is_safe(_foundry):
    out = model_foundry.dismiss_serve_request("serve-nope")
    assert out["ok"] is False
    assert out["error"] == "unknown_request"


# ── Issue 2: served-endpoint resolution is id-format tolerant + runtime tag ──────


def _serve_qwen(*, runtime_models=None) -> str:
    res = model_foundry.create_serve_preflight(model_id="qwen2.5-14b", port=11434)
    req_id = res["serve_request"]["id"]
    model_foundry.update_serve_request(
        req_id,
        status="served",
        executed=True,
        served=True,
        endpoint="http://127.0.0.1:11434",
        runtime_models=runtime_models if runtime_models is not None else ["qwen2.5:14b"],
    )
    return req_id


def test_served_endpoint_resolves_across_id_formats(_foundry):
    _serve_qwen()
    for mid in ("qwen2.5-14b", "qwen2.5:14b", "QWEN2.5-14B", "qwen2514b"):
        assert model_foundry.served_model_endpoint(mid) == "http://127.0.0.1:11434"


def test_served_runtime_name_is_ollama_tag(_foundry):
    _serve_qwen(runtime_models=["qwen2.5:14b", "nomic-embed-text:latest"])
    assert model_foundry.served_model_runtime_name("qwen2.5-14b") == "qwen2.5:14b"


def test_served_runtime_name_falls_back_to_catalog_tag(_foundry):
    _serve_qwen(runtime_models=[])  # runtime didn't report names
    assert model_foundry.served_model_runtime_name("qwen2.5-14b") == "qwen2.5:14b"


def test_served_model_auto_enables_tool_loop_base_url(_foundry):
    # No LOCAL_LLM_BASE_URL set — a served Foundry model must be self-sufficient.
    _serve_qwen()
    assert completion_mod.local_tool_loop_base_url("qwen2.5-14b") == "http://127.0.0.1:11434/v1"
    assert local_tool_loop_capable(_local()) is True


def test_local_runtime_model_name_translates_catalog_id(_foundry):
    _serve_qwen()
    # The catalog id (qwen2.5-14b) must be addressed on Ollama as its runtime tag.
    assert completion_mod._local_runtime_model_name("qwen2.5-14b") == "qwen2.5:14b"


def test_local_tool_loop_payload_uses_runtime_tag(_foundry, monkeypatch):
    """The HTTP payload model must be the Ollama tag, not the Foundry catalog id."""
    _serve_qwen()
    captured: dict[str, str] = {}

    def _fake_loop(*, url, headers, provider, model, **_kwargs):
        captured["model"] = model
        captured["url"] = url
        return None

    monkeypatch.setattr(completion_mod, "_run_openai_compatible_tool_loop", _fake_loop)
    completion_mod.run_local_tool_loop(
        system="s",
        user_message="u",
        tools=[],
        tool_executor=lambda n, i: "{}",
        model="qwen2.5-14b",
    )
    assert captured["model"] == "qwen2.5:14b"
    assert captured["url"].startswith("http://127.0.0.1:11434")
