# SPDX-License-Identifier: Apache-2.0
"""§6 blind compare honors the chosen models and reveals the TRUE mapping."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.provider.completion import ProviderResult
from aethos_core.research import blind_model_eval


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_blind_eval_stub_mode_returns_two_slots():
    get_settings.cache_clear()
    res = blind_model_eval.run_blind_model_eval(prompt="compare railway vs vercel hosting")
    assert res["ok"] is True
    assert len(res["blind_slots"]) == 2
    assert len(res["reveal_map"]) == 2
    assert "selected" in res


def test_blind_eval_honors_chosen_models_and_reveals_true_mapping(monkeypatch):
    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-6")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
    get_settings.cache_clear()

    def fake_complete(text, **kwargs):
        from aethos_core.llm.effective_model import resolve_effective_model

        eff = resolve_effective_model(turn_override=kwargs.get("model_override"))
        return ProviderResult(text=f"answer on {eff.model}", provider=eff.provider, model=eff.model, used_llm=True)

    monkeypatch.setattr("aethos_core.provider.completion.complete_chat", fake_complete)

    res = blind_model_eval.run_blind_model_eval(
        prompt="compare these two approaches in detail",
        model_a="anthropic:claude-opus-4-6",
        model_b="openrouter:openai/gpt-4.1-mini",
    )
    assert res["ok"] is True
    assert res["mode"] == "live"
    reveals = set(res["reveal_map"].values())
    # Each slot reveals the real model + provider — and they are distinct.
    assert any("claude-opus-4-6" in v and "anthropic" in v for v in reveals)
    assert any("openai/gpt-4.1-mini" in v and "openrouter" in v for v in reveals)
    assert len(reveals) == 2
