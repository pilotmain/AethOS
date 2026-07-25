# SPDX-License-Identifier: Apache-2.0
"""Multi-provider LLM routing — Anthropic primary with template fallback."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings


def resolve_llm_provider(*, requested: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    if not getattr(settings, "llm_provider_routing_enabled", True):
        return {"provider": "template", "model": "template", "use_real_llm": False}
    active = (requested or settings.active_provider or "none").strip().lower()
    if active in ("anthropic", "claude") and settings.use_real_llm:
        from aethos_core.llm.model_providers import anthropic_configured

        if anthropic_configured():
            return {
                "provider": "anthropic",
                "model": settings.anthropic_model,
                "use_real_llm": True,
            }
    if active == "openrouter" and str(getattr(settings, "openrouter_api_key", "") or "").strip():
        return {
            "provider": "openrouter",
            "model": str(getattr(settings, "openrouter_model", "openrouter/auto")),
            "use_real_llm": True,
        }
    # §2 — any configured model-API provider can be the active provider.
    from aethos_core.llm.model_providers import model_provider_configured, model_provider_spec

    spec = model_provider_spec(active)
    if spec is not None and model_provider_configured(active):
        return {
            "provider": spec.id,
            "model": str(getattr(settings, spec.model_attr, "") or spec.models[0][0]),
            "use_real_llm": True,
        }
    return {"provider": "template", "model": "template", "use_real_llm": False}


def list_available_llm_providers() -> list[dict[str, Any]]:
    settings = get_settings()
    from aethos_core.llm.model_providers import anthropic_configured

    providers: list[dict[str, Any]] = [{"id": "template", "configured": True}]
    providers.append(
        {
            "id": "anthropic",
            "configured": bool(settings.use_real_llm and anthropic_configured()),
            "model": settings.anthropic_model,
        }
    )
    providers.append(
        {
            "id": "openrouter",
            "configured": bool(str(getattr(settings, "openrouter_api_key", "") or "").strip()),
            "model": str(getattr(settings, "openrouter_model", "openrouter/auto")),
        }
    )
    providers.append(
        {
            "id": "local",
            "configured": bool(
                getattr(settings, "local_llm_enabled", False)
                and str(getattr(settings, "local_llm_base_url", "") or "").strip()
            ),
            "model": str(getattr(settings, "local_llm_default_model", "llama3.2")),
        }
    )
    # §2 — registry model-API providers (configured via .env or the MC vault).
    from aethos_core.llm.model_providers import MODEL_PROVIDERS, model_provider_configured

    for spec in MODEL_PROVIDERS.values():
        providers.append(
            {
                "id": spec.id,
                "configured": model_provider_configured(spec.id),
                "model": str(getattr(settings, spec.model_attr, "") or ""),
            }
        )
    return providers
