# SPDX-License-Identifier: Apache-2.0
"""Provider readiness snapshot for Mission Control — no secrets exposed."""

from __future__ import annotations

from aethos_core.config import get_settings
from aethos_core.provider.completion import provider_configured


def build_provider_readiness() -> dict[str, object]:
    s = get_settings()
    from aethos_core.llm.model_providers import anthropic_configured, configured_model_providers

    configured = provider_configured()
    key_set = anthropic_configured()
    any_provider = key_set or bool(configured_model_providers())
    real_llm = s.use_real_llm
    provider_name = "Anthropic" if s.active_provider in ("anthropic", "none") else s.active_provider

    if configured:
        status_label = "Ready"
        user_message = (
            "Full reasoning is enabled. Open-ended chat and provider-backed tracked jobs "
            f"(e.g. research competitors) use your configured model providers."
        )
    elif real_llm and not any_provider:
        status_label = "Not configured"
        user_message = (
            "USE_REAL_LLM is on, but no model provider API key is configured. "
            "Add a key in Mission Control → Advanced settings → Credentials."
        )
    elif key_set and not real_llm:
        status_label = "Not configured"
        user_message = "Anthropic API key is set, but USE_REAL_LLM is false. Set USE_REAL_LLM=true and restart the API."
    else:
        status_label = "Not configured"
        user_message = (
            "Full reasoning is not enabled. Capability and project-direction questions still work "
            "without a provider."
        )

    return {
        "full_reasoning": {
            "status": status_label,
            "ready": configured,
            "provider": provider_name,
            "model": s.anthropic_model,
        },
        "flags": {
            "use_real_llm": real_llm,
            "anthropic_key_set": key_set,
            "active_provider": s.active_provider,
        },
        "requirements": [
            {"key": "USE_REAL_LLM", "value": "true", "met": real_llm, "ok": real_llm},
            {
                "key": "Provider API key",
                "value": "Mission Control → Advanced settings → Credentials",
                "met": any_provider,
                "ok": any_provider,
            },
            {
                "key": "API restart",
                "value": "after .env changes",
                "met": configured,
                "ok": configured,
            },
        ],
        "restart_required": not configured,
        "deterministic_note": (
            "AethOS will still answer deterministic capability and setup questions."
        ),
        "template_fallback_note": (
            "Without the provider, open-ended chat and tracked jobs (research, roadmap, etc.) "
            "complete using deterministic fallback templates."
        ),
        "user_message": user_message,
        "setup_steps": [
            "Add a provider API key in Mission Control → Advanced settings → Credentials",
            "Set USE_REAL_LLM=true",
            "Restart the API if you changed .env",
        ],
        # backward-compatible fields
        "use_real_llm": real_llm,
        "active_provider": s.active_provider,
        "configured": configured,
        "model": s.anthropic_model,
        "anthropic_key_set": key_set,
    }
