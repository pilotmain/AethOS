# SPDX-License-Identifier: Apache-2.0
"""Session model override — catalog, precedence, persistence."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.llm.effective_model import (
    ModelSelectionUnavailable,
    effective_model_for_agent_tool_loop,
    resolve_effective_model,
)
from aethos_core.llm.model_catalog import DEFAULT_CATALOG_ID, catalog_entry_for_id, list_available_models
from aethos_core.llm.session_model_override import (
    clear_session_model_override,
    get_session_model_override,
    set_session_model_override,
)


@pytest.fixture(autouse=True)
def _llm_enabled(monkeypatch):
    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    monkeypatch.setenv("ACTIVE_PROVIDER", "anthropic")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_catalog_includes_default_and_anthropic_models():
    models = list_available_models(include_unconfigured=False)
    ids = {row["id"] for row in models}
    assert DEFAULT_CATALOG_ID in ids
    assert "anthropic:claude-opus-4-6" in ids
    assert "anthropic:claude-sonnet-4-6" in ids


def test_env_default_when_no_session_override():
    effective = resolve_effective_model(session_id="model-test-default")
    assert effective.source == "env"
    assert effective.model == "claude-sonnet-4-6"
    assert effective.provider == "anthropic"


def test_session_override_takes_precedence_over_env():
    sid = "model-test-session"
    clear_session_model_override(sid)
    result = set_session_model_override(sid, "anthropic:claude-opus-4-6")
    assert result["ok"] is True
    assert get_session_model_override(sid) == "anthropic:claude-opus-4-6"

    effective = resolve_effective_model(session_id=sid)
    assert effective.source == "session"
    assert effective.model == "claude-opus-4-6"
    assert effective.catalog_id == "anthropic:claude-opus-4-6"


def test_turn_override_beats_session_override():
    sid = "model-test-turn"
    set_session_model_override(sid, "anthropic:claude-haiku-4-5")
    effective = resolve_effective_model(session_id=sid, turn_override="anthropic:claude-opus-4-6")
    assert effective.source == "turn"
    assert effective.model == "claude-opus-4-6"


def test_clear_session_override_restores_env_default():
    sid = "model-test-clear"
    set_session_model_override(sid, "anthropic:claude-opus-4-6")
    clear_session_model_override(sid)
    assert get_session_model_override(sid) is None
    effective = resolve_effective_model(session_id=sid)
    assert effective.source == "env"


def test_unknown_catalog_id_rejected():
    result = set_session_model_override("model-test-bad", "anthropic:does-not-exist")
    assert result["ok"] is False


def test_catalog_entry_lookup():
    entry = catalog_entry_for_id("anthropic:claude-haiku-4-5")
    assert entry is not None
    assert entry["model"] == "claude-haiku-4-5"


def test_model_selection_honored_resolve_to_tool_loop():
    """§5 — real path: session override → resolve → agent tool loop model id."""
    sid = "model-test-honored"
    set_session_model_override(sid, "anthropic:claude-opus-4-6")
    effective = resolve_effective_model(session_id=sid)
    tool_model = effective_model_for_agent_tool_loop(effective)
    assert tool_model is not None
    assert tool_model.catalog_id == "anthropic:claude-opus-4-6"
    assert tool_model.model == "claude-opus-4-6"


def test_explicit_selection_without_key_raises(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    get_settings.cache_clear()
    from aethos_core.security.credential_vault import get_credential_vault, reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    get_credential_vault().clear_all_for_tests()
    with pytest.raises(ModelSelectionUnavailable) as exc_info:
        resolve_effective_model(turn_override="anthropic:claude-opus-4-6")
    assert exc_info.value.catalog_id == "anthropic:claude-opus-4-6"
    assert "API key" in exc_info.value.reason
