# SPDX-License-Identifier: Apache-2.0
"""A single OpenRouter key should be able to power a real multi-model arbiter:
OpenRouter reaches many providers, so the auto-pool expands it into several
cross-provider models (validated against the live catalog, cost-modest), instead of
the old single 'openrouter/auto' entry that left the arbiter with <2 models.
"""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.arbiter import pool as arb


_FAKE_OPENROUTER = [
    ("anthropic/claude-3.5-haiku", "Claude 3.5 Haiku"),
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
    ("openai/gpt-4o-mini", "GPT-4o mini"),
    ("openai/gpt-4o", "GPT-4o"),
    ("google/gemini-flash-1.5", "Gemini Flash 1.5"),
]


def test_openrouter_entries_are_diverse_and_cost_modest():
    with patch(
        "aethos_core.llm.model_providers.refresh_live_models_for_provider",
        return_value=_FAKE_OPENROUTER,
    ):
        entries = arb.openrouter_arbiter_entries(max_n=3)
    fams = [e["model_id"].split("/")[0] for e in entries]
    assert len(entries) == 3
    assert fams == ["anthropic", "openai", "google"]  # one per family, preferred order
    # cheaper variants chosen within each family
    assert entries[0]["model_id"] == "anthropic/claude-3.5-haiku"
    assert entries[1]["model_id"] == "openai/gpt-4o-mini"
    assert all(e["provider"] == "openrouter" for e in entries)


def test_openrouter_only_setup_expands_into_a_real_pool():
    # Connected models = just OpenRouter's single auto entry (the old behavior).
    with patch.object(arb, "_openrouter_connected", return_value=True):
        with patch(
            "aethos_core.llm.model_catalog.list_available_models",
            return_value=[{"id": "or", "provider": "openrouter", "model": "openrouter/auto", "label": "OpenRouter auto"}],
        ):
            with patch(
                "aethos_core.llm.model_providers.refresh_live_models_for_provider",
                return_value=_FAKE_OPENROUTER,
            ):
                pool = arb.default_pool_from_connected_models()
    assert len(pool) >= 2  # arbiter now has enough to run
    # the non-deterministic auto placeholder is replaced by real models
    assert all(p["model_id"] not in ("openrouter/auto", "auto") for p in pool)
    assert len({p["model_id"] for p in pool}) == len(pool)  # deduped


def test_fetch_failure_falls_back_safely():
    # Only openrouter/auto available + live fetch fails: auto is excluded (poor critic), and
    # with nothing to expand the pool is empty — safe (validate_pool declines honestly), no crash.
    with patch.object(arb, "_openrouter_connected", return_value=True):
        with patch(
            "aethos_core.llm.model_catalog.list_available_models",
            return_value=[{"id": "or", "provider": "openrouter", "model": "openrouter/auto", "label": "OpenRouter auto"}],
        ):
            with patch(
                "aethos_core.llm.model_providers.refresh_live_models_for_provider",
                return_value=[],  # live fetch failed/empty
            ):
                pool = arb.default_pool_from_connected_models()
    assert pool == []


def test_default_pool_is_cross_provider_not_all_one():
    """Diversity: with 8 Anthropic + several OpenRouter models connected, the default pool
    spans providers (not 8 Claudes) and caps per provider — cross-provider consensus + cheaper."""
    from collections import Counter

    avail = [{"id": "default", "provider": "anthropic", "model": "default", "label": "Default"}]
    avail += [{"id": f"a{i}", "provider": "anthropic", "model": f"claude-{i}", "label": f"Claude {i}"} for i in range(8)]
    avail += [{"id": f"o{i}", "provider": "openrouter", "model": f"openai/m{i}", "label": f"OR {i}"} for i in range(5)]
    with patch("aethos_core.llm.model_catalog.list_available_models", return_value=avail):
        pool = arb.default_pool_from_connected_models()
    provs = {p["provider"] for p in pool}
    assert provs == {"anthropic", "openrouter"}, f"expected cross-provider, got {provs}"
    counts = Counter(p["provider"] for p in pool)
    assert counts["anthropic"] <= arb._PER_VENDOR_CAP
    assert counts["openrouter"] <= arb._PER_VENDOR_CAP


def test_validate_pool_accepts_vault_openrouter_key():
    """Regression: a vault-stored OpenRouter key (registry-resolved) must validate — the old
    settings-only check wrongly rejected it with 'OPENROUTER_API_KEY is not set'."""
    pool = [
        {"provider": "openrouter", "model_id": "openai/gpt-4o-mini", "label": "GPT-4o mini"},
        {"provider": "openrouter", "model_id": "anthropic/claude-3.5-haiku", "label": "Claude 3.5 Haiku"},
    ]
    with patch("aethos_core.llm.model_providers.resolve_model_provider_key", return_value="sk-or-vault"):
        res = arb.validate_pool(pool)
    assert res["valid"] is True, res["errors"]
    assert not any("OPENROUTER_API_KEY is not set" in e for e in res["errors"])


def test_default_pool_excludes_openrouter_auto():
    """openrouter/auto is non-deterministic (and can hang) — it must not be an arbiter critic."""
    avail = [
        {"id": "a", "provider": "anthropic", "model": "claude-x", "label": "Claude X"},
        {"id": "auto", "provider": "openrouter", "model": "openrouter/auto", "label": "OR auto"},
        {"id": "g", "provider": "openrouter", "model": "openai/gpt-4o-mini", "label": "GPT-4o mini"},
    ]
    with patch("aethos_core.llm.model_catalog.list_available_models", return_value=avail):
        pool = arb.default_pool_from_connected_models()
    assert all(p["model_id"] not in ("openrouter/auto", "auto") for p in pool), pool
    assert any(p["model_id"] == "openai/gpt-4o-mini" for p in pool)


def test_per_model_timeout_is_capped():
    from aethos_core.arbiter.dispatcher import _model_timeout_sec

    # Must never be the old ~227s budget — a slow model should drop fast, not hang the run.
    assert 45.0 <= _model_timeout_sec() <= 75.0


def test_default_pool_spans_vendors_and_dedups_same_vendor():
    """Cross-vendor: Anthropic direct + OpenRouter (claude + gpt + gemini) should yield one model
    per vendor — Claude-via-OpenRouter is deduped against direct Anthropic, and the Anthropic slot
    uses the DIRECT provider (more reliable than routed)."""
    avail = [
        {"id": "a", "provider": "anthropic", "model": "claude-opus-4-6", "label": "Claude Opus"},
        {"id": "o1", "provider": "openrouter", "model": "anthropic/claude-3-haiku", "label": "Claude via OR"},
        {"id": "o2", "provider": "openrouter", "model": "openai/gpt-4o-mini", "label": "GPT"},
        {"id": "o3", "provider": "openrouter", "model": "google/gemini-flash-1.5", "label": "Gemini"},
    ]
    with patch("aethos_core.llm.model_catalog.list_available_models", return_value=avail):
        pool = arb.default_pool_from_connected_models()
    vendors = [arb._vendor_of(p) for p in pool]
    assert len(vendors) == len(set(vendors)), f"duplicate vendor in {vendors}"
    assert {"anthropic", "openai", "google"} <= set(vendors)
    anth = [p for p in pool if arb._vendor_of(p) == "anthropic"][0]
    assert anth["provider"] == "anthropic", "should prefer direct Anthropic over Claude-via-OpenRouter"
