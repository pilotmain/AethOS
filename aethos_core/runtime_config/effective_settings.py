# SPDX-License-Identifier: Apache-2.0
"""Effective settings resolver — runtime store -> .env/Settings -> default.

This is the single entry point for reading and writing user-controllable config.
Writes go through the allowlist (settings_registry), persist to the tenant-scoped
SQLite runtime store, and are written to the audit ledger.

Single-tenant (default): overrides are also applied to the live Settings singleton
so existing ``get_settings()`` reads honor UI changes without per-call-site edits.

Multi-tenant: each tenant has its own runtime store partition. Only the
operator/default tenant's overrides are applied to the singleton at boot (operator
boot config). Non-operator tenants must read via ``effective_setting()`` /
``effective_attr()`` — never via the mutated singleton.

Secrets and dangerous/governance flags are rejected here — vault/operator only.
"""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_config.runtime_config_store import (
    all_runtime_values,
    delete_runtime_value,
    get_runtime_value,
    set_runtime_value,
)
from aethos_core.runtime_config.settings_registry import (
    SettingSpec,
    get_setting_spec,
    get_setting_spec_by_attr,
    is_dangerous_key,
    list_setting_specs,
    looks_like_secret_key,
    normalize_key,
)


class ConfigWriteError(ValueError):
    """Raised when a runtime config write is rejected (unknown/secret/dangerous/invalid)."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _settings() -> Any:
    from aethos_core.config import get_settings

    return get_settings()


def _should_sync_singleton() -> bool:
    """Whether a write should also patch the live Settings singleton."""
    from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

    s = _settings()
    if not s.multi_tenant_enabled:
        return True
    return get_current_tenant() == DEFAULT_TENANT


def _coerce(spec: SettingSpec, raw: str) -> Any:
    if spec.kind == "bool":
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}
    if spec.kind == "int":
        return int(str(raw).strip())
    if spec.kind == "float":
        return float(str(raw).strip())
    return str(raw)


def _to_storage_str(spec: SettingSpec, value: Any) -> str:
    if spec.kind == "bool":
        return "true" if (value is True or str(value).strip().lower() in {"1", "true", "yes", "on"}) else "false"
    return str(value)


def _validate(spec: SettingSpec, value: Any) -> Any:
    try:
        coerced = _coerce(spec, str(value))
    except (TypeError, ValueError) as exc:
        raise ConfigWriteError("invalid_value", f"{spec.key} expects {spec.kind}: {exc}") from exc
    if spec.kind == "enum" and spec.options and str(coerced) not in spec.options:
        raise ConfigWriteError(
            "invalid_value",
            f"{spec.key} must be one of: {', '.join(spec.options)}",
        )
    return coerced


def effective_setting(key: str, *, tenant_id: str | None = None) -> Any:
    """Resolve a user-settable key: tenant runtime store -> Settings(.env) -> default."""
    spec = get_setting_spec(key)
    if spec is None:
        return getattr(_settings(), (key or "").strip().lower(), None)
    stored = get_runtime_value(spec.key, tenant_id=tenant_id)
    if stored is not None:
        try:
            return _coerce(spec, stored)
        except (TypeError, ValueError):
            pass
    return getattr(_settings(), spec.attr, None)


def effective_attr(attr: str, default: Any = None, *, tenant_id: str | None = None) -> Any:
    """Read a Settings attribute with tenant-aware overlay for user-settable keys."""
    spec = get_setting_spec_by_attr(attr)
    if spec is not None:
        return effective_setting(spec.key, tenant_id=tenant_id)
    return getattr(_settings(), attr, default)


def effective_bool(key: str, *, tenant_id: str | None = None) -> bool:
    return bool(effective_setting(key, tenant_id=tenant_id))


def effective_str(key: str, *, tenant_id: str | None = None) -> str:
    val = effective_setting(key, tenant_id=tenant_id)
    return "" if val is None else str(val)


def setting_source(key: str, *, tenant_id: str | None = None) -> str:
    spec = get_setting_spec(key)
    if spec is None:
        return "settings"
    return "runtime_store" if get_runtime_value(spec.key, tenant_id=tenant_id) is not None else "env_default"


def set_effective_setting(key: str, value: Any, *, actor: str = "operator") -> dict[str, Any]:
    """Validate, persist to the current tenant's store, optionally sync singleton, audit."""
    k = normalize_key(key)
    spec = get_setting_spec(k)
    if spec is None:
        if looks_like_secret_key(k):
            raise ConfigWriteError(
                "secret_not_allowed",
                f"{k} is a secret — store it in the credential vault (Connections), not runtime config.",
            )
        if is_dangerous_key(k):
            raise ConfigWriteError(
                "operator_only",
                f"{k} is an operator-only governance/safety flag and cannot be set from the UI.",
            )
        raise ConfigWriteError("unknown_key", f"{k} is not a user-settable setting.")

    coerced = _validate(spec, value)
    before = effective_setting(spec.key)
    set_runtime_value(spec.key, _to_storage_str(spec, coerced))
    if _should_sync_singleton():
        _apply_one(spec, coerced)
    _audit(spec.key, before, coerced, actor=actor, action="runtime_config.set")
    _post_write_hook(spec)
    return {
        "ok": True,
        "key": spec.key,
        "value": coerced,
        "source": "runtime_store",
        "restart_required": spec.restart_required,
    }


def revert_effective_setting(key: str, *, actor: str = "operator") -> dict[str, Any]:
    """Remove a runtime override for the current tenant; fall back to .env/default."""
    spec = get_setting_spec(key)
    if spec is None:
        raise ConfigWriteError("unknown_key", f"{normalize_key(key)} is not a user-settable setting.")
    before = effective_setting(spec.key)
    removed = delete_runtime_value(spec.key)
    from aethos_core.config import Settings

    env_default = getattr(Settings(), spec.attr, None)
    if _should_sync_singleton():
        _apply_one(spec, env_default)
    if removed:
        _audit(spec.key, before, env_default, actor=actor, action="runtime_config.revert")
    return {"ok": True, "key": spec.key, "reverted": removed, "value": env_default, "source": "env_default"}


def _apply_one(spec: SettingSpec, value: Any) -> None:
    try:
        setattr(_settings(), spec.attr, value)
    except Exception:
        pass


def apply_runtime_overrides(settings_obj: Any) -> None:
    """Apply persisted runtime overrides onto a freshly-built Settings object.

    Called once from ``get_settings()`` after Settings() is constructed.

    Single-tenant: all default-tenant overrides are applied (unchanged behavior).

    Multi-tenant: only the operator/default tenant's overrides are applied so the
    singleton holds operator boot config; per-tenant values are read via
    ``effective_setting()`` at request time.
    """
    from aethos_core.tenancy import DEFAULT_TENANT

    stored = all_runtime_values(tenant_id=DEFAULT_TENANT)
    if not stored:
        return
    for spec in list_setting_specs():
        raw = stored.get(spec.key)
        if raw is None:
            continue
        try:
            setattr(settings_obj, spec.attr, _coerce(spec, raw))
        except Exception:
            continue


def _post_write_hook(spec: SettingSpec) -> None:
    if spec.attr == "conversation_memory_enabled":
        return
    if spec.attr in {"arbiter_model_pool", "arbiter_blind_critique", "arbiter_enabled"}:
        return


def _audit(key: str, before: Any, after: Any, *, actor: str, action: str) -> None:
    try:
        from aethos_core.observability.audit_ledger import record_audit_event

        record_audit_event(
            action=action,
            actor=actor,
            target=key,
            before=before,
            after=after,
            metadata={"source": "runtime_config"},
        )
    except Exception:
        pass


def list_effective_settings() -> dict[str, Any]:
    """Grouped current effective values + metadata for the Settings UI."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for spec in list_setting_specs():
        groups.setdefault(spec.group, []).append(
            {
                "key": spec.key,
                "label": spec.label,
                "description": spec.description,
                "kind": spec.kind,
                "options": list(spec.options),
                "value": effective_setting(spec.key),
                "source": setting_source(spec.key),
                "restart_required": spec.restart_required,
            }
        )
    return {
        "ok": True,
        "groups": [{"group": name, "settings": items} for name, items in groups.items()],
    }
