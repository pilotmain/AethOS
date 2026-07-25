# SPDX-License-Identifier: Apache-2.0
"""Per-provider model selection — which models a connected provider exposes.

Users pick exactly which of a provider's models to enable (default: its flagship
shortlist on) and can add custom model ids by typing them (e.g. ``o3``,
``deepseek-reasoner``). The choice persists in the runtime config store (not .env),
keyed per provider. ``model_catalog.list_available_models`` reads the enabled set
from here so the picker + arbiter show exactly the user's models.
"""

from __future__ import annotations

import json
from typing import Any

from aethos_core.llm.model_providers import (
    model_provider_configured,
    model_provider_rows,
    model_provider_spec,
)
from aethos_core.runtime_config.runtime_config_store import get_runtime_value, set_runtime_value


def _key(provider: str) -> str:
    return f"model_selection:{(provider or '').strip().lower()}"


def _load(provider: str) -> dict[str, list[str]]:
    raw = get_runtime_value(_key(provider))
    if not raw:
        return {"disabled": [], "custom": []}
    try:
        data = json.loads(raw)
        return {
            "disabled": [str(x) for x in (data.get("disabled") or [])],
            "custom": [str(x) for x in (data.get("custom") or [])],
        }
    except (ValueError, TypeError):
        return {"disabled": [], "custom": []}


def enabled_models_for_provider(spec: Any) -> list[tuple[str, str]]:
    """(model_id, label) rows the user has enabled for this provider.

    Default = the provider's flagship shortlist (all on). Disabled ids are removed;
    custom ids are appended. Used by the catalog so only enabled models surface.
    """
    sel = _load(spec.id)
    disabled = set(sel["disabled"])
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()
    for model_id, label in model_provider_rows(spec):
        seen.add(model_id)
        if model_id in disabled:
            continue
        rows.append((model_id, label))
    for model_id in sel["custom"]:
        model_id = model_id.strip()
        if not model_id or model_id in seen or model_id in disabled:
            continue
        seen.add(model_id)
        rows.append((model_id, f"{spec.label} · {model_id}"))
    return rows


def get_provider_model_selection(provider: str) -> dict[str, Any] | None:
    """Full selection state for a provider (for the Connections model picker)."""
    spec = model_provider_spec(provider)
    if spec is None:
        return None
    sel = _load(spec.id)
    disabled = set(sel["disabled"])
    models: list[dict[str, Any]] = []
    seen: set[str] = set()
    for model_id, label in model_provider_rows(spec):
        seen.add(model_id)
        models.append(
            {"model_id": model_id, "label": label, "enabled": model_id not in disabled, "custom": False}
        )
    for model_id in sel["custom"]:
        model_id = model_id.strip()
        if not model_id or model_id in seen:
            continue
        seen.add(model_id)
        models.append(
            {
                "model_id": model_id,
                "label": f"{spec.label} · {model_id}",
                "enabled": model_id not in disabled,
                "custom": True,
            }
        )
    return {
        "provider": spec.id,
        "label": spec.label,
        "configured": model_provider_configured(spec.id),
        "models": models,
        "api_key_url": spec.api_key_url,
    }


def set_provider_model_selection(
    provider: str, *, enabled_ids: list[str], custom_ids: list[str], actor: str | None = None
) -> dict[str, Any]:
    """Persist the enabled set + custom ids. ``enabled_ids`` is the full ON set."""
    spec = model_provider_spec(provider)
    if spec is None:
        raise ValueError(f"{provider} is not a known model provider.")

    flagship_ids = [m for m, _ in model_provider_rows(spec)]
    clean_custom: list[str] = []
    seen_custom: set[str] = set()
    for cid in custom_ids:
        cid = str(cid).strip()
        if not cid or cid in flagship_ids or cid in seen_custom:
            continue
        seen_custom.add(cid)
        clean_custom.append(cid)

    known_ids = set(flagship_ids) | seen_custom
    enabled = {str(x).strip() for x in enabled_ids if str(x).strip()}
    disabled = sorted(known_ids - enabled)

    before = _load(spec.id)
    set_runtime_value(_key(spec.id), json.dumps({"disabled": disabled, "custom": clean_custom}))
    _audit(spec.id, before, {"disabled": disabled, "custom": clean_custom}, actor=actor)
    return get_provider_model_selection(spec.id) or {}


def list_provider_model_selections() -> list[dict[str, Any]]:
    """Selection state for every configured model provider (Connections UI)."""
    from aethos_core.llm.model_providers import configured_model_providers

    out: list[dict[str, Any]] = []
    for spec in configured_model_providers():
        sel = get_provider_model_selection(spec.id)
        if sel is not None:
            out.append(sel)
    return out


def _audit_actor(actor: str | None) -> str:
    if actor:
        return actor
    from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

    tenant = get_current_tenant()
    return tenant if tenant != DEFAULT_TENANT else "operator"


def _audit(provider: str, before: Any, after: Any, *, actor: str | None = None) -> None:
    try:
        from aethos_core.observability.audit_ledger import record_audit_event

        record_audit_event(
            action="model_selection.set",
            actor=_audit_actor(actor),
            target=provider,
            before=before,
            after=after,
            metadata={"source": "runtime_config"},
        )
    except Exception:
        pass
