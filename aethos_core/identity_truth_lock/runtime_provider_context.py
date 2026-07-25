# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — runtime provider and model attribution context."""

from __future__ import annotations

from typing import Any


def resolve_runtime_provider_context() -> dict[str, Any]:
    try:
        from aethos_core.config import get_settings

        settings = get_settings()
        provider = (settings.active_provider or "none").strip().lower()
        if provider == "anthropic":
            model = (settings.anthropic_model or "claude").strip()
            display_provider = "Anthropic"
            display_model = "Claude" if "claude" in model.lower() else model
        elif provider == "openai":
            model = getattr(settings, "openai_model", "gpt-4o") or "gpt-4o"
            display_provider = "OpenAI"
            display_model = "GPT" if "gpt" in model.lower() else model
        elif provider in {"", "none", "template"}:
            display_provider = "none (deterministic platform routing)"
            display_model = "platform-composed responses"
            model = "platform-composed"
            provider = "none"
        else:
            display_provider = provider
            display_model = model if (model := getattr(settings, f"{provider}_model", provider)) else provider
    except Exception:
        provider = "none"
        model = "platform-composed"
        display_provider = "none (deterministic platform routing)"
        display_model = "platform-composed responses"

    return {
        "provider": provider,
        "model": model,
        "display_provider": display_provider,
        "display_model": display_model,
    }
