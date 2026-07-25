# SPDX-License-Identifier: Apache-2.0
"""Parse and validate the arbiter model pool from config."""

from __future__ import annotations

import logging
from typing import Any

from aethos_core.config import get_settings
from aethos_core.runtime_config.effective_settings import effective_attr, effective_str

_log = logging.getLogger("aethos.arbiter.pool")

# Built-in arbiter providers plus every configured bring-your-own-model provider
# from the model registry (OpenAI, Gemini, DeepSeek, Mistral, Groq, …). The
# dispatcher drives them all through provider.completion (OpenAI-compatible).
_BASE_PROVIDERS = frozenset({"anthropic", "openrouter", "local"})


def supported_providers() -> frozenset[str]:
    try:
        from aethos_core.llm.model_providers import MODEL_PROVIDERS

        return _BASE_PROVIDERS | frozenset(MODEL_PROVIDERS.keys())
    except Exception:
        return _BASE_PROVIDERS


# Backwards-compatible name (now a superset including registry providers).
SUPPORTED_PROVIDERS = supported_providers()


def parse_model_pool() -> list[dict[str, str]]:
    """
    Parse ARBITER_MODEL_POOL into structured entries.

    Format: "provider:model_id,provider:model_id,..."
    Example: "anthropic:claude-opus-4-6,openrouter:openai/gpt-4.1-mini,local:llama3.2"

    Returns list of {"provider": ..., "model_id": ..., "label": ...}.
    Unsupported providers and malformed entries are skipped with a warning.
    """
    raw = effective_str("ARBITER_MODEL_POOL").strip()
    pool = parse_model_pool_string(raw)
    if pool:
        return pool
    # §4 — no explicit pool (env or UI): default to the user's connected models so
    # the arbiter works from Mission Control without any .env editing.
    return default_pool_from_connected_models()


def _openrouter_connected() -> bool:
    s = get_settings()
    if str(getattr(s, "openrouter_api_key", "") or "").strip():
        return True
    try:
        from aethos_core.llm.model_providers import model_provider_configured

        return bool(model_provider_configured("openrouter"))
    except Exception:
        return False


# Prefer cheaper variants within a family — the arbiter runs every model per query,
# billed to the user, so default to economical models, not flagships.
_OPENROUTER_FAMILY_ORDER = ("anthropic", "openai", "google", "meta-llama", "mistralai", "deepseek")
_OPENROUTER_CHEAP_HINT = ("mini", "flash", "haiku", "small", "lite", "nano", "8b", "7b", "9b")


def openrouter_arbiter_entries(max_n: int = 3) -> list[dict[str, str]]:
    """Pick a diverse, cost-modest set of OpenRouter models so a single OpenRouter key
    can power a genuine multi-provider arbiter.

    Models are taken ONLY from OpenRouter's live catalog (so slugs are always valid),
    one per provider family, preferring cheaper variants. Returns [] on any failure so
    the caller falls back to existing behavior.
    """
    try:
        from aethos_core.llm.model_providers import refresh_live_models_for_provider

        rows = refresh_live_models_for_provider("openrouter")
    except Exception:
        return []
    if not rows:
        return []
    by_family: dict[str, list[tuple[str, str]]] = {}
    for mid, lbl in rows:
        fam = str(mid).split("/", 1)[0].lower()
        by_family.setdefault(fam, []).append((str(mid), str(lbl)))
    chosen: list[dict[str, str]] = []
    for fam in _OPENROUTER_FAMILY_ORDER:
        cands = by_family.get(fam)
        if not cands:
            continue
        pick = next((c for c in cands if any(h in c[0].lower() for h in _OPENROUTER_CHEAP_HINT)), cands[0])
        chosen.append(
            {"provider": "openrouter", "model_id": pick[0], "label": pick[1] or _label("openrouter", pick[0])}
        )
        if len(chosen) >= max_n:
            break
    return chosen


# How many models to take per VENDOR in the default pool. The arbiter's value is
# cross-vendor consensus, and every model is billed per run — so a default of 8 Claudes is
# both weaker (one vendor's view) and pricier than a diverse mix. The round-robin spans
# vendors first, so a multi-vendor setup gets one each before it deepens within a vendor;
# a single-vendor setup still gets 2 models so the arbiter can run.
_PER_VENDOR_CAP = 2


def _vendor_of(entry: dict[str, str]) -> str:
    """The underlying vendor of a pool entry. OpenRouter's 'vendor/model' ids count as their
    real vendor (openai, google, …) so they diversify; direct providers are their own vendor."""
    if entry["provider"] == "openrouter" and "/" in entry["model_id"]:
        return entry["model_id"].split("/", 1)[0].lower()
    return entry["provider"]


def _is_cheap_model(model_id: str) -> bool:
    return any(h in model_id.lower() for h in _OPENROUTER_CHEAP_HINT)


def default_pool_from_connected_models() -> list[dict[str, str]]:
    """Build a CROSS-VENDOR pool from the models the user has connected in Mission Control.

    Diversifies by underlying vendor (Anthropic / OpenAI / Google / Llama / …) — counting
    OpenRouter-routed models as their real vendor — so the arbiter spans architectures, not
    8 Claudes. A vendor reachable both directly and via OpenRouter is deduped (direct wins).
    """
    max_models = int(effective_attr("arbiter_max_models", 8) or 8)
    try:
        from aethos_core.llm.model_catalog import list_available_models
    except Exception:
        return []

    supported = supported_providers()
    # Group candidate models by VENDOR (not by provider).
    by_vendor: dict[str, list[dict[str, str]]] = {}
    for row in list_available_models(include_unconfigured=False):
        if str(row.get("id")) == "default":
            continue
        provider = str(row.get("provider") or "").strip().lower()
        model_id = str(row.get("model") or "").strip()
        if not model_id or provider not in supported:
            continue
        # Skip OpenRouter's non-deterministic auto-router as an arbiter critic: you can't
        # tell which model answered, and it can route to a slow/unavailable model.
        if provider == "openrouter" and model_id in ("openrouter/auto", "auto"):
            continue
        entry = {"provider": provider, "model_id": model_id, "label": str(row.get("label") or _label(provider, model_id))}
        by_vendor.setdefault(_vendor_of(entry), []).append(entry)

    # Within each vendor, prefer a direct-provider model over an OpenRouter-routed one
    # (direct is more reliable / fewer hops), then prefer cheaper variants.
    for items in by_vendor.values():
        items.sort(key=lambda e: (e["provider"] == "openrouter", not _is_cheap_model(e["model_id"])))

    # Preferred vendor order first, then any others, for a stable, sensible default.
    ordered_vendors = [v for v in _OPENROUTER_FAMILY_ORDER if v in by_vendor]
    ordered_vendors += [v for v in by_vendor if v not in ordered_vendors]

    pool: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def _add(entry: dict[str, str]) -> bool:
        key = (entry["provider"], entry["model_id"])
        if key in seen:
            return False
        seen.add(key)
        pool.append(entry)
        return True

    # Breadth first: ONE model per vendor → maximum cross-vendor diversity, no duplicate
    # vendors (a vendor reachable both directly and via OpenRouter contributes once).
    for vendor in ordered_vendors:
        if by_vendor[vendor]:
            _add(by_vendor[vendor][0])
            if len(pool) >= max_models:
                return pool

    # Depth only when breadth couldn't form an arbiter (a single-vendor setup): take more
    # from a vendor (up to the cap) so there are at least 2 models to run.
    if len(pool) < 2:
        for vendor in ordered_vendors:
            for entry in by_vendor[vendor][1:_PER_VENDOR_CAP]:
                _add(entry)
                if len(pool) >= max_models:
                    return pool
            if len(pool) >= 2:
                break

    # A single OpenRouter key can reach many providers' models. If the connected models
    # still can't form an arbiter (<2), expand OpenRouter into a few cross-provider models.
    if len(pool) < 2 and _openrouter_connected():
        expanded = openrouter_arbiter_entries(max_n=max(2, min(3, max_models)))
        if len(expanded) >= 2:
            pool = [
                p for p in pool
                if not (p["provider"] == "openrouter" and p["model_id"] in ("openrouter/auto", "auto"))
            ]
            seen = {(p["provider"], p["model_id"]) for p in pool}
            for e in expanded:
                k = (e["provider"], e["model_id"])
                if k not in seen:
                    seen.add(k)
                    pool.append(e)

    return pool[:max_models]


def parse_model_pool_string(raw: str) -> list[dict[str, str]]:
    """Parse a "provider:model_id,provider:model_id,..." string into pool entries.

    Shared by config-driven (parse_model_pool) and chat-tool-driven (arbiter_run
    pool override) parsing so both honor identical validation and max-models caps.
    """
    s = get_settings()
    raw = str(raw or "").strip()
    if not raw:
        return []

    pool: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    max_models = int(getattr(s, "arbiter_max_models", 8) or 8)

    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        if ":" not in entry:
            _log.warning(
                "Arbiter pool entry missing provider prefix (expected provider:model_id): %s",
                entry,
            )
            continue
        provider, _, model_id = entry.partition(":")
        provider = provider.strip().lower()
        model_id = model_id.strip()
        if not model_id:
            continue
        if provider not in supported_providers():
            _log.warning("Arbiter pool entry uses unsupported provider %r — skipping", provider)
            continue
        key = (provider, model_id)
        if key in seen:
            continue
        seen.add(key)
        pool.append(
            {"provider": provider, "model_id": model_id, "label": _label(provider, model_id)}
        )
        if len(pool) >= max_models:
            break

    return pool


def validate_pool(pool: list[dict[str, str]]) -> dict[str, Any]:
    """Check that at least 2 models are configured and required credentials exist."""
    s = get_settings()
    errors: list[str] = []

    if len(pool) < 2:
        errors.append(
            f"Arbiter requires at least 2 models from your enabled pool; got {len(pool)}. "
            "Add a second provider API key in Mission Control → Advanced settings → Credentials and enable its models "
            "(or enable more models on your existing providers)."
        )

    providers = {e["provider"] for e in pool}

    if "anthropic" in providers:
        from aethos_core.llm.model_providers import resolve_anthropic_api_key

        if not resolve_anthropic_api_key().strip():
            errors.append(
                "Pool includes anthropic: model but no Anthropic API key is configured "
                "(add it in Mission Control → Advanced settings → Credentials)."
            )
    # OpenRouter is now a vault-aware registry provider — the generic registry-provider
    # check below validates its key (.env or vault). No settings-only special case here,
    # which wrongly rejected vault-stored OpenRouter keys.
    if "local" in providers and not (
        getattr(s, "local_llm_enabled", False)
        and str(getattr(s, "local_llm_base_url", "") or "").strip()
    ):
        errors.append(
            "Pool includes local: model but LOCAL_LLM_ENABLED / LOCAL_LLM_BASE_URL are not set."
        )

    # Registry providers (OpenAI, Gemini, DeepSeek, …): key from .env or the vault.
    try:
        from aethos_core.llm.model_providers import is_registry_provider, resolve_model_provider_key

        for provider in providers:
            if is_registry_provider(provider) and not resolve_model_provider_key(provider):
                errors.append(
                    f"Pool includes {provider}: model but no {provider} API key is configured "
                    "(add it in Mission Control → Advanced settings → Credentials)."
                )
    except Exception:
        pass

    return {"valid": len(errors) == 0, "errors": errors, "pool_size": len(pool)}


def _label(provider: str, model_id: str) -> str:
    labels: dict[str, str] = {
        "claude-opus-4-6": "Claude Opus 4.6",
        "claude-sonnet-4-6": "Claude Sonnet 4.6",
        "claude-haiku-4-5": "Claude Haiku 4.5",
        "openai/gpt-4.1": "GPT-4.1",
        "openai/gpt-4.1-mini": "GPT-4.1 Mini",
        "openai/o3-mini": "o3-mini",
        "google/gemini-2.5-flash": "Gemini 2.5 Flash",
        "google/gemini-2.5-pro": "Gemini 2.5 Pro",
        "meta-llama/llama-3.3-70b-instruct": "Llama 3.3 70B",
        "mistralai/mistral-large": "Mistral Large",
        "llama3.2": "Llama 3.2 (local)",
        "llama3.1": "Llama 3.1 (local)",
        "mistral": "Mistral (local)",
        "codellama": "CodeLlama (local)",
    }
    if model_id in labels:
        return labels[model_id]
    return f"{_provider_display(provider)} · {_pretty_model(model_id)}"


_ACRONYMS = {"gpt": "GPT", "ai": "AI", "llm": "LLM", "db": "DB", "api": "API", "xl": "XL", "oss": "OSS"}
_PROVIDER_DISPLAY_NAMES = {
    "openrouter": "OpenRouter",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
    "meta-llama": "Meta Llama",
    "mistralai": "Mistral",
    "deepseek": "DeepSeek",
    "local": "Local",
}


def _provider_display(provider: str) -> str:
    return _PROVIDER_DISPLAY_NAMES.get((provider or "").lower(), (provider or "").title())


def _pretty_model(model_id: str) -> str:
    """Human label for a model id — acronym-aware, keeps version numbers (gpt-4o, not Gpt 4O).

    For OpenRouter 'vendor/model' ids, surface the vendor too (e.g. 'OpenAI · GPT-4o')."""
    raw = model_id or ""
    vendor = ""
    if "/" in raw:
        vendor_token, _, raw = raw.partition("/")
        vendor = _PROVIDER_DISPLAY_NAMES.get(vendor_token.lower(), vendor_token.title())
    words = []
    for w in raw.replace("_", "-").replace("-", " ").split():
        words.append(_ACRONYMS.get(w.lower(), w[:1].upper() + w[1:]))
    name = " ".join(words)
    return f"{vendor} {name}" if vendor else name
