# SPDX-License-Identifier: Apache-2.0
"""§3/§5 honest cross-provider failover + §2 per-model metering split.

Failover must honor the selection first, continue on the next provider on failure,
label the swap (never silent), and stop at a bounded cap. Metering must expose a
per-model split and report local inference as an explicit $0.00 (not "n/a").
"""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.llm.effective_model import EffectiveModel
from aethos_core.observability import metering
from aethos_core.provider import completion as completion_mod
from aethos_core.provider.completion import ProviderResult


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _multi_provider(monkeypatch):
    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-opus-4-6")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
    monkeypatch.setenv("MODEL_FAILOVER_ENABLED", "true")
    get_settings.cache_clear()


def _anthropic_selection() -> EffectiveModel:
    return EffectiveModel(
        catalog_id="anthropic:claude-opus-4-6",
        provider="anthropic",
        model="claude-opus-4-6",
        label="Claude Opus 4.6",
        source="session",
    )


# ── §3 failover continues honestly and labels the swap ──────────────────────────


def test_failover_continues_on_next_provider_with_notice(monkeypatch):
    _multi_provider(monkeypatch)
    calls: list[str] = []

    def fake(user_text, *, provider, model, include_identity, system_overlay):
        calls.append(provider)
        if provider == "anthropic":
            return ProviderResult(text="error 429 rate limit", provider="anthropic", model=model, used_llm=False)
        return ProviderResult(
            text="answer from openrouter", provider="openrouter", model=model, used_llm=True,
            input_tokens=5, output_tokens=5,
        )

    monkeypatch.setattr(completion_mod, "_complete_one_attempt", fake)
    res = completion_mod._complete_with_failover(
        "hello there", _anthropic_selection(), include_identity=False, system_overlay=None, session_id="s1"
    )
    assert res.used_llm is True
    assert res.provider == "openrouter"
    assert res.failover is True
    assert "continued on" in (res.failover_notice or "")
    assert "rate-limited (429)" in res.text
    assert calls[0] == "anthropic"  # selection honored first


def test_failover_all_down_returns_single_error_and_is_bounded(monkeypatch):
    _multi_provider(monkeypatch)
    calls: list[str] = []

    def fake(user_text, *, provider, model, include_identity, system_overlay):
        calls.append(provider)
        return ProviderResult(text="boom 500 server error", provider=provider, model=model, used_llm=False)

    monkeypatch.setattr(completion_mod, "_complete_one_attempt", fake)
    res = completion_mod._complete_with_failover(
        "hello there", _anthropic_selection(), include_identity=False, system_overlay=None, session_id="s1"
    )
    assert res.used_llm is False
    assert "All configured providers failed" in res.text
    cap = int(get_settings().model_failover_max_attempts)
    assert len(calls) <= cap


def test_no_failover_when_disabled_returns_single_path(monkeypatch):
    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("MODEL_FAILOVER_ENABLED", "false")
    get_settings.cache_clear()
    chain = completion_mod.provider_failover_chain("anthropic", "claude-opus-4-6", "Claude Opus 4.6")
    assert chain == [("anthropic", "claude-opus-4-6", "Claude Opus 4.6")]


def test_provider_failover_chain_one_model_per_provider(monkeypatch):
    _multi_provider(monkeypatch)
    chain = completion_mod.provider_failover_chain("anthropic", "claude-opus-4-6", "Claude Opus 4.6")
    providers = [prov for prov, _model, _label in chain]
    assert providers[0] == "anthropic"
    assert providers.count("anthropic") == 1
    assert "openrouter" in providers
    assert providers.index("openrouter") > 0


def test_cross_provider_failover_anthropic_timeout_then_openrouter(monkeypatch):
    _multi_provider(monkeypatch)
    calls: list[str] = []

    def fake(user_text, *, provider, model, include_identity, system_overlay):
        calls.append(provider)
        if provider == "anthropic":
            return ProviderResult(
                text="Anthropic temporarily unavailable (timeout or connection error)",
                provider="anthropic",
                model=model,
                used_llm=False,
            )
        return ProviderResult(
            text="answer from openrouter",
            provider="openrouter",
            model=model,
            used_llm=True,
            input_tokens=3,
            output_tokens=3,
        )

    monkeypatch.setattr(completion_mod, "_complete_one_attempt", fake)
    res = completion_mod._complete_with_failover(
        "hello", _anthropic_selection(), include_identity=False, system_overlay=None, session_id="s1"
    )
    assert res.used_llm is True
    assert res.provider == "openrouter"
    assert calls == ["anthropic", "openrouter"]


def test_all_providers_fail_single_provider_honest_hint(monkeypatch):
    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("MODEL_FAILOVER_ENABLED", "true")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "false")
    get_settings.cache_clear()
    monkeypatch.setattr(completion_mod, "_local_llm_ready", lambda: False)
    monkeypatch.setattr(
        "aethos_core.llm.model_catalog._served_foundry_rows",
        lambda: [],
    )
    monkeypatch.setattr(
        completion_mod,
        "provider_failover_chain",
        lambda provider, model, label: [(provider, model, label)],
    )

    def fake(user_text, *, provider, model, include_identity, system_overlay):
        return ProviderResult(
            text="timed out",
            provider=provider,
            model=model,
            used_llm=False,
        )

    monkeypatch.setattr(completion_mod, "_complete_one_attempt", fake)
    res = completion_mod._complete_with_failover(
        "hello", _anthropic_selection(), include_identity=False, system_overlay=None, session_id="s1"
    )
    # Single-provider chat must NOT push a second provider (failover/arbiter concern only),
    # but must still name the real reason honestly instead of disguising it.
    assert "add a second provider" not in res.text.lower()
    assert "timed out" in res.text.lower()
    assert "connections" in res.text.lower()


def test_tool_loop_failover_continues_on_next_provider(monkeypatch):
    _multi_provider(monkeypatch)
    calls: list[tuple[str, str]] = []

    def fake(provider: str, model: str, **kwargs):
        calls.append((provider, model))
        if provider == "anthropic":
            return completion_mod.ToolLoopResult(
                text="Anthropic returned 404 (model not found for your API key)",
                provider="anthropic",
                model=model,
                used_llm=False,
                loop_outcome="error_degraded",
            )
        return completion_mod.ToolLoopResult(
            text="ok", provider=provider, model=model, used_llm=True, tool_calls=1, iterations=1
        )

    monkeypatch.setattr(completion_mod, "_run_tool_loop_one_attempt", fake)
    res = completion_mod.run_tool_loop_with_provider_failover(
        _anthropic_selection(),
        system="sys",
        user_message="hi",
        tools=[],
        tool_executor=lambda _n, _i: "",
        channel="chat",
    )
    assert res is not None
    assert res.used_llm is True
    assert res.provider != "anthropic"
    assert calls[0] == ("anthropic", "claude-opus-4-6")
    assert "continued on" in res.text


def test_tool_loop_all_providers_fail_names_each(monkeypatch):
    _multi_provider(monkeypatch)

    def fake(provider: str, model: str, **kwargs):
        return completion_mod.ToolLoopResult(
            text="boom auth failed",
            provider=provider,
            model=model,
            used_llm=False,
            loop_outcome="error_degraded",
        )

    monkeypatch.setattr(completion_mod, "_run_tool_loop_one_attempt", fake)
    res = completion_mod.run_tool_loop_with_provider_failover(
        _anthropic_selection(),
        system="sys",
        user_message="hi",
        tools=[],
        tool_executor=lambda _n, _i: "",
        channel="chat",
    )
    assert res is not None
    assert "All configured providers failed" in res.text
    assert "auth failed" in res.text


# ── §2 metering: local $0.00 + per-model session split ──────────────────────────


@pytest.fixture()
def _metering_clean():
    metering.clear_metering_for_tests()
    yield
    metering.clear_metering_for_tests()


def test_metering_local_cost_is_zero_not_na(_metering_clean):
    metering.record_usage(
        org_id="o1", input_tokens=10, output_tokens=10, model="qwen2.5:14b", provider="local", session_id="s1"
    )
    summ = metering.get_usage_summary(org_id="o1", session_id="s1")
    cost = summ["session"]["cost"]
    assert cost["known"] is True
    assert cost["usd"] == 0.0
    assert cost["label"] != "n/a"


def test_metering_session_model_split_percentages(_metering_clean):
    # 80 local tokens, 20 cloud tokens → 80% / 20%.
    metering.record_usage(
        org_id="o2", input_tokens=40, output_tokens=40, model="qwen2.5:14b", provider="local", session_id="s2"
    )
    metering.record_usage(
        org_id="o2", input_tokens=10, output_tokens=10, model="claude-opus-4-6", provider="anthropic", session_id="s2"
    )
    summ = metering.get_usage_summary(org_id="o2", session_id="s2")
    split = summ["session"]["models"]
    assert len(split) == 2
    by_model = {row["model"]: row for row in split}
    assert by_model["qwen2.5:14b"]["pct"] == 80.0
    assert by_model["claude-opus-4-6"]["pct"] == 20.0
    assert by_model["qwen2.5:14b"]["cost"]["usd"] == 0.0  # local free
    assert by_model["claude-opus-4-6"]["cost"]["known"] is True  # cloud priced


def test_compute_cost_local_zero():
    assert metering.compute_cost_usd("anything", 1000, 1000, provider="local") == 0.0
    assert metering.compute_cost_usd("totally-unknown-model", 1000, 1000) is None


# ── §C3 prompt cache verified end-to-end ────────────────────────────────────────


def test_prompt_cache_breakpoint_respects_flag(monkeypatch):
    monkeypatch.setenv("PROMPT_CACHE_ENABLED", "true")
    monkeypatch.setenv("PROMPT_CACHE_RETENTION", "short")
    get_settings.cache_clear()
    marker = completion_mod._prompt_cache_breakpoint()
    assert marker == {"type": "ephemeral"}

    monkeypatch.setenv("PROMPT_CACHE_RETENTION", "long")
    get_settings.cache_clear()
    assert completion_mod._prompt_cache_breakpoint() == {"type": "ephemeral", "ttl": "1h"}

    monkeypatch.setenv("PROMPT_CACHE_ENABLED", "false")
    get_settings.cache_clear()
    assert completion_mod._prompt_cache_breakpoint() is None


def test_cacheable_system_and_tools_attach_cache_control(monkeypatch):
    monkeypatch.setenv("PROMPT_CACHE_ENABLED", "true")
    get_settings.cache_clear()
    system = completion_mod._cacheable_system("persona + tools prefix")
    # system becomes a block list carrying cache_control when caching is on
    blocks = system if isinstance(system, list) else [system]
    assert any(isinstance(b, dict) and b.get("cache_control") for b in blocks)

    tools = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
    out = completion_mod._cacheable_tools(tools)
    assert out[-1].get("cache_control"), "last tool carries the cache breakpoint"
    assert "cache_control" not in out[0]


def test_cache_hit_ratio_surfaces_in_usage_summary(_metering_clean):
    metering.record_usage(
        org_id="oc",
        input_tokens=100,
        output_tokens=20,
        model="claude-opus-4-6",
        provider="anthropic",
        session_id="sc",
        cache_read_tokens=300.0,
        cache_creation_tokens=100.0,
    )
    summ = metering.get_usage_summary(org_id="oc", session_id="sc")
    cache = summ["session"]["cache"]
    assert cache["known"] is True
    # read / (read + creation + fresh) = 300 / (300+100+100) = 60.0%
    assert cache["hit_ratio"] == 60.0
    assert cache["read_tokens"] == 300.0


# ── §C3 streaming verified token-by-token ───────────────────────────────────────


def test_stream_text_chunks_tokenizes_and_reconstructs():
    from aethos_core.api.routes.chat import _stream_text_chunks

    text = "AethOS streams the governed reply token by token for low perceived latency."
    chunks = list(_stream_text_chunks(text, group=4))
    assert len(chunks) > 1  # streamed in multiple deltas, not one blob
    assert "".join(chunks) == text  # lossless reconstruction on the client
