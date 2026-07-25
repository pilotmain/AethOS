# SPDX-License-Identifier: Apache-2.0
"""Resolve effective LLM provider + model — session override over .env default."""

from __future__ import annotations

from dataclasses import dataclass

from aethos_core.config import get_settings
from aethos_core.llm.model_catalog import catalog_entry_for_id, default_catalog_entry, env_default_catalog_entry


@dataclass(frozen=True)
class EffectiveModel:
    catalog_id: str
    provider: str
    model: str
    label: str
    source: str  # env | session | turn


class ModelSelectionUnavailable(ValueError):
    """Explicit user selection cannot run — never silently substitute another model."""

    def __init__(self, catalog_id: str, reason: str) -> None:
        self.catalog_id = catalog_id
        self.reason = reason
        super().__init__(reason)


def model_unavailable_reply(catalog_id: str, reason: str) -> str:
    hint = ""
    raw = (catalog_id or "").strip()
    if ":" in raw:
        provider, model = raw.split(":", 1)
        try:
            from aethos_core.llm.model_providers import supported_model_ids_for_provider

            ids = supported_model_ids_for_provider(provider.strip().lower())
            if ids:
                preview = ", ".join(ids[:8])
                if len(ids) > 8:
                    preview += ", …"
                hint = f" Models your key supports: {preview}."
        except Exception:  # noqa: BLE001
            pass
    return (
        f"Model `{catalog_id}` isn't available: {reason}.{hint} "
        "Pick another in the model menu."
    )


def _unavailable_reason_for_entry(entry: dict[str, object]) -> str:
    provider = str(entry.get("provider") or "")
    from aethos_core.llm.model_providers import model_provider_configured, model_provider_spec

    if not model_provider_configured(provider):
        spec = model_provider_spec(provider)
        label = spec.label if spec else provider
        return f"no API key for {label} — add one in Mission Control → Advanced settings → Credentials"
    return "provider credentials could not be resolved for this turn"


def _effective_from_entry(entry: dict[str, object], *, source: str) -> EffectiveModel:
    return EffectiveModel(
        catalog_id=str(entry["id"]),
        provider=str(entry["provider"]),
        model=str(entry["model"]),
        label=str(entry["label"]),
        source=source,
    )


def _resolve_explicit_selection(raw: str, *, source: str) -> EffectiveModel:
    """Honor an explicit catalog id — raise when it cannot run (no silent env fallback)."""
    cleaned = (raw or "").strip()
    if not cleaned or cleaned.lower() in ("default", "env"):
        raise ModelSelectionUnavailable(cleaned or "default", "empty model selection")

    entry = catalog_entry_for_id(cleaned)
    if entry is None:
        reason = "not recognized — check the model id in the menu"
        if ":" in cleaned:
            provider, model = cleaned.split(":", 1)
            from aethos_core.llm.model_providers import model_id_supported_by_provider

            if not model_id_supported_by_provider(provider.strip().lower(), model.strip()):
                reason = "model id not supported by your provider key"
        raise ModelSelectionUnavailable(cleaned, reason)
    if entry.get("configured"):
        return _effective_from_entry(entry, source=source)

    reason = _unavailable_reason_for_entry(entry)
    raise ModelSelectionUnavailable(cleaned, reason)


def resolve_effective_model(
    *,
    session_id: str = "default",
    turn_override: str | None = None,
    prompt: str | None = None,
) -> EffectiveModel:
    """Precedence: per-turn override → session sticky override → cost-routing → .env default.

    Explicit turn/session selections never silently fall back to the env default when
  they cannot run — callers receive ``ModelSelectionUnavailable`` instead. Cost-aware
  routing (Feature 4) only engages on the env-default branch, so an explicit pick always
  wins; ``prompt`` enables it.
    """
    raw_turn = (turn_override or "").strip()
    if raw_turn and raw_turn.lower() not in ("default", "env"):
        return _resolve_explicit_selection(raw_turn, source="turn")

    from aethos_core.llm.session_model_override import get_session_model_override

    session_raw = get_session_model_override(session_id)
    if session_raw and session_raw.lower() not in ("default", "env"):
        return _resolve_explicit_selection(session_raw, source="session")

    # Cost-aware routing: simple turns may use a cheaper model (no explicit pick made).
    if prompt:
        try:
            from aethos_core.llm.cost_router import route_for_prompt

            cheap = route_for_prompt(prompt)
            if cheap:
                return _effective_from_entry(cheap, source="cost_router")
        except Exception:  # noqa: BLE001 — routing must never break completion
            pass

    entry = env_default_catalog_entry()
    return EffectiveModel(
        catalog_id=str(entry["id"]),
        provider=str(entry["provider"]),
        model=str(entry["model"]),
        label=str(entry["label"]),
        source="env",
    )


def local_tool_loop_capable(effective: EffectiveModel) -> bool:
    """True when the selected local model can run the agent tool loop in-place.

    Requires the flag on AND a reachable OpenAI-compatible runtime (served Foundry
    endpoint or configured local LLM base URL). Drives the picker's per-mode gating
    so we never offer a selection the agent would silently ignore.
    """
    settings = get_settings()
    if effective.provider != "local" or not getattr(settings, "local_tool_loop_enabled", True):
        return False
    from aethos_core.provider.completion import local_tool_loop_base_url

    return bool(local_tool_loop_base_url(effective.model))


def effective_model_for_agent_tool_loop(effective: EffectiveModel) -> EffectiveModel | None:
    """Model that will actually drive the agent tool loop.

    Transparency: when the selection is local and the runtime can do tool calling,
    we keep the local model (caller drives the OpenAI-compatible tools API). Any
    swap to a cloud model is returned as a *different* EffectiveModel so the caller
    surfaces the fallback instead of overriding silently.
    """
    settings = get_settings()
    from aethos_core.llm.model_providers import (
        is_registry_provider,
        model_provider_configured,
    )

    # 1) Anthropic selection with a tenant-scoped key → native messages/tools API.
    if effective.provider == "anthropic" and model_provider_configured("anthropic"):
        return effective
    # 2) Local selection → keep local, drive tools over OpenAI-compatible /v1.
    if local_tool_loop_capable(effective):
        return effective
    # 3) OpenRouter selection → honor when multi-provider tool loop is on and a key exists.
    openrouter_key = str(getattr(settings, "openrouter_api_key", "") or "").strip()
    openrouter_ready = openrouter_key or model_provider_configured("openrouter")
    if (
        effective.provider == "openrouter"
        and getattr(settings, "multi_provider_tool_loop_enabled", True)
        and openrouter_ready
    ):
        return effective
    # 4) Registry providers (OpenAI, Gemini, DeepSeek, …) with tenant keys.
    #    OpenRouter is excluded here: it's now a registry provider too, but it has its
    #    own multi_provider_tool_loop-aware handling in steps 3 and 6, so it must not be
    #    short-circuited by this generic branch (which would bypass the disabled-flag fallback).
    if (
        effective.provider != "openrouter"
        and is_registry_provider(effective.provider)
        and model_provider_configured(effective.provider)
    ):
        return effective
    # 5) Local without tool runtime → honest cloud fallback (caller surfaces swap).
    if effective.provider == "local" and not local_tool_loop_capable(effective):
        if model_provider_configured("anthropic"):
            default = default_catalog_entry(provider="anthropic")
            if default is not None:
                return EffectiveModel(
                    catalog_id=str(default["id"]),
                    provider="anthropic",
                    model=str(default["model"]),
                    label=str(default["label"]),
                    source=effective.source,
                )
    # 6) OpenRouter tool loop disabled → cloud fallback when Anthropic is available.
    if (
        effective.provider == "openrouter"
        and not getattr(settings, "multi_provider_tool_loop_enabled", True)
        and model_provider_configured("anthropic")
    ):
        default = default_catalog_entry(provider="anthropic")
        if default is not None:
            return EffectiveModel(
                catalog_id=str(default["id"]),
                provider="anthropic",
                model=str(default["model"]),
                label=str(default["label"]),
                source=effective.source,
            )
    return None
