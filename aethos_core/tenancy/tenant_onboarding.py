# SPDX-License-Identifier: Apache-2.0
"""Per-tenant first-run setup wizard (Phase 6).

Tracks whether a tenant has completed BYOK onboarding: vault credentials, model
selection, and feature toggles — all via existing tenant-scoped APIs (vault,
runtime config, model selection). No secrets in onboarding state.
"""

from __future__ import annotations

import time
from typing import Any

_NS = "tenant_onboarding"

_STEPS: tuple[dict[str, Any], ...] = (
    {"id": "credentials", "title": "Add provider keys", "hint": "Store API keys in the encrypted vault — never in chat or .env."},
    {"id": "models", "title": "Choose models", "hint": "Pick which models each connected provider exposes."},
    {"id": "features", "title": "Enable intelligence", "hint": "Turn on LLM reasoning for chat and the arbiter."},
)


def _settings() -> Any:
    from aethos_core.config import get_settings

    return get_settings()


def _tenant() -> str:
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

    return resolve_data_tenant()


def _operator_exempt() -> bool:
    from aethos_core.tenancy import DEFAULT_TENANT

    return _tenant() == DEFAULT_TENANT


def _vault_model_provider_ids() -> tuple[str, ...]:
    """Model providers tenants connect via the vault (incl. native Anthropic/OpenRouter)."""
    from aethos_core.llm.model_providers import MODEL_PROVIDERS

    return tuple(dict.fromkeys(("anthropic", "openrouter", *MODEL_PROVIDERS.keys())))


def _tenant_has_model_provider_key(provider: str) -> bool:
    from aethos_core.llm.model_providers import model_provider_configured, model_provider_spec

    pid = (provider or "").strip().lower()
    if model_provider_spec(pid) is not None:
        return model_provider_configured(pid)
    from aethos_core.llm.model_providers import _vault_key

    return bool(_vault_key(pid))


def _step_credentials_done() -> bool:
    return any(_tenant_has_model_provider_key(pid) for pid in _vault_model_provider_ids())


def _step_models_done() -> bool:
    from aethos_core.llm.model_providers import configured_model_providers
    from aethos_core.llm.model_selection import enabled_models_for_provider

    for spec in configured_model_providers():
        if enabled_models_for_provider(spec):
            return True
    # Vault-only native providers use catalog defaults — no per-tenant picker row required.
    for pid in ("anthropic", "openrouter"):
        if _tenant_has_model_provider_key(pid):
            return True
    return False


def _step_features_done() -> bool:
    from aethos_core.runtime_config.effective_settings import effective_bool

    return effective_bool("USE_REAL_LLM")


def _step_done(step_id: str) -> bool:
    if step_id == "credentials":
        return _step_credentials_done()
    if step_id == "models":
        return _step_models_done()
    if step_id == "features":
        return _step_features_done()
    return False


def _stored_state() -> dict[str, Any]:
    from aethos_core.tenancy.tenant_data_store import get_record

    raw = get_record(_NS, "state", default={})
    return raw if isinstance(raw, dict) else {}


def mark_onboarding_complete() -> dict[str, Any]:
    from aethos_core.tenancy.tenant_data_store import set_record

    payload = {"complete": True, "completed_at": time.time()}
    set_record(_NS, "state", payload)
    return payload


def build_tenant_onboarding_state() -> dict[str, Any]:
    """Wizard progress for the current tenant (no-op when single-tenant)."""
    s = _settings()
    if not s.multi_tenant_enabled:
        return {"ok": True, "enabled": False, "required": False, "complete": True}

    if _operator_exempt():
        return {
            "ok": True,
            "enabled": True,
            "required": False,
            "complete": True,
            "tenant_id": _tenant(),
            "operator_exempt": True,
        }

    stored = _stored_state()
    steps: list[dict[str, Any]] = []
    done_count = 0
    for step in _STEPS:
        done = _step_done(str(step["id"]))
        if done:
            done_count += 1
        steps.append({**step, "completed": done, "status": "done" if done else "pending"})

    auto_complete = done_count == len(_STEPS)
    manually_complete = bool(stored.get("complete"))
    complete = manually_complete or auto_complete
    total = len(_STEPS)

    return {
        "ok": True,
        "enabled": True,
        "required": not complete,
        "complete": complete,
        "tenant_id": _tenant(),
        "steps": steps,
        "progress": round(done_count / max(total, 1), 3),
        "completed_count": done_count,
        "total_steps": total,
        "next_step": next((st for st in steps if not st["completed"]), None),
        "completed_at": stored.get("completed_at"),
    }
