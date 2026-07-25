# SPDX-License-Identifier: Apache-2.0
"""Startup credential hydration — restore and validate provider auth."""

from __future__ import annotations

import json
import logging
from time import time
from typing import Any

from aethos_core.connections.credential_audit import append_credential_audit_event
from aethos_core.connections.credential_repair import repair_metadata_only_credentials
from aethos_core.connections.credential_state import resolve_credential_state
from aethos_core.connections.credential_validation import validate_all_provider_credentials
from aethos_core.connections.validation_status import MISSING, RECONNECT_REQUIRED, VALIDATED
from aethos_core.security.credential_paths import hydration_report_path
from aethos_core.security.credential_vault import get_credential_vault, get_credential_vault_diagnostics
from aethos_core.security.secret_redaction import redact_text

_log = logging.getLogger(__name__)

_last_hydration: dict[str, Any] | None = None


def last_hydration_report() -> dict[str, Any] | None:
    return dict(_last_hydration) if _last_hydration else None


def reload_credential_runtime(*, validate: bool = True) -> dict[str, Any]:
    """Invalidate in-memory vault cache and re-hydrate provider auth."""
    from aethos_core.security.credential_vault import reload_credential_vault_from_disk

    reload_credential_vault_from_disk()
    return hydrate_credentials_at_startup(validate=validate)


def _provider_hydration_row(*, provider: str, credential_id: str | None) -> dict[str, Any]:
    if not credential_id:
        return {
            "provider": provider,
            "metadata_found": False,
            "encrypted_secret_found": False,
            "decryptable": False,
            "hydrated": False,
            "credential_state": MISSING,
            "status": MISSING,
            "credential_id": None,
            "last_validated_at": None,
            "masked_preview": None,
            "credential_count": 0,
        }
    state = resolve_credential_state(credential_id)
    vault = get_credential_vault()
    rec = vault.get(credential_id)
    return {
        "provider": provider,
        "credential_count": len(vault.list_credentials(provider=provider)),
        "credential_id": credential_id,
        "metadata_found": bool(state.get("metadata_found")),
        "encrypted_secret_found": bool(state.get("encrypted_secret_found")),
        "decryptable": bool(state.get("decryptable")),
        "hydrated": bool(state.get("hydrated")),
        "credential_state": state.get("credential_state"),
        "status": rec.validation_status if rec else state.get("credential_state"),
        "last_validated_at": rec.last_validated_at if rec else None,
        "masked_preview": rec.masked_identifier if rec else None,
        "failure_class": state.get("failure_class"),
        "auth_source": state.get("auth_source"),
    }


def hydrate_credentials_at_startup(*, validate: bool = True) -> dict[str, Any]:
    """Load vault from disk, detect metadata-only drift, optionally validate."""
    global _last_hydration
    from aethos_core.providers.base.provider_registry import ProviderRegistry

    repair_metadata_only_credentials()
    vault_diag = get_credential_vault_diagnostics()
    vault = get_credential_vault()
    active = vault.list_credentials()
    managed_providers = ProviderRegistry.list_credential_managed_names()
    report: dict[str, Any] = {
        "ok": vault_diag.get("available", False),
        "hydrated_at": time(),
        "credential_count": len(active),
        "vault": vault_diag,
        "providers": {},
        "validation": None,
        "repaired_metadata_only": [],
    }

    for provider in managed_providers:
        creds = vault.list_credentials(provider=provider)
        latest = creds[0] if creds else None
        report["providers"][provider] = _provider_hydration_row(
            provider=provider,
            credential_id=latest.credential_id if latest else None,
        )

    if validate and active and vault_diag.get("available"):
        try:
            validation = validate_all_provider_credentials(providers=managed_providers)
        except Exception as exc:
            _log.exception("credential_validation_failed_at_startup")
            validation = {
                "ok": False,
                "validated_count": 0,
                "results": [],
                "startup_error": redact_text(str(exc)),
            }
        report["validation"] = validation
        report["validated_count"] = validation.get("validated_count", 0)
        for provider in managed_providers:
            creds = vault.list_credentials(provider=provider)
            latest = creds[0] if creds else None
            report["providers"][provider] = _provider_hydration_row(
                provider=provider,
                credential_id=latest.credential_id if latest else None,
            )

    _last_hydration = report
    try:
        path = hydration_report_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except OSError:
        _log.exception("hydration_report_write_failed")

    append_credential_audit_event(
        event="startup_hydration",
        provider="system",
        detail=f"credentials={len(active)} validated={report.get('validated_count', 0)}",
        validation_status=VALIDATED if report.get("ok") else MISSING,
    )
    _log.info(
        "credential_hydration_complete count=%s validated=%s",
        len(active),
        report.get("validated_count", 0),
    )
    return report


def build_credential_center_payload() -> dict[str, Any]:
    from aethos_core.providers.base.provider_registry import ProviderRegistry

    repair_metadata_only_credentials()
    vault = get_credential_vault()
    rows: list[dict[str, Any]] = []
    for provider in ProviderRegistry.list_credential_managed_names():
        creds = vault.list_credentials(provider=provider)
        latest = creds[0] if creds else None
        scope_label = ", ".join(latest.scope[:4]) if latest and latest.scope else "—"
        if latest and len(latest.scope) > 4:
            scope_label += "…"
        if latest:
            state = resolve_credential_state(latest.credential_id)
            storage = vault.inspect_secret_storage(latest.credential_id)
            credential_state = str(state.get("credential_state") or latest.validation_status)
            status = credential_state
            if credential_state == RECONNECT_REQUIRED:
                status = RECONNECT_REQUIRED
        else:
            state = {}
            storage = {
                "has_metadata": False,
                "has_encrypted_secret": False,
                "decryptable": False,
                "auth_source": "none",
            }
            credential_state = MISSING
            status = MISSING
        rows.append(
            {
                "provider": provider,
                "status": status,
                "credential_state": credential_state,
                "last_validated_at": latest.last_validated_at if latest else None,
                "last_tested_at": latest.last_tested_at if latest else None,
                "scope": scope_label,
                "masked_preview": latest.masked_identifier if latest else None,
                "credential_id": latest.credential_id if latest else None,
                "credential_count": len(creds),
                "validation_diagnostics": dict(latest.validation_diagnostics) if latest else {},
                "failure_class": (latest.validation_diagnostics or {}).get("failure_class")
                if latest
                else state.get("failure_class"),
                "runtime_usable": bool(state.get("runtime_usable")),
                "actions_allowed": {
                    "revalidate": bool(latest)
                    and storage.get("auth_source") != "metadata_only"
                    and credential_state not in (RECONNECT_REQUIRED, MISSING),
                    "reconnect": credential_state in (RECONNECT_REQUIRED, MISSING, "persistence_failed"),
                    "repair": credential_state in (RECONNECT_REQUIRED, "persistence_failed"),
                },
                **storage,
            }
        )
    return {
        "ok": True,
        "providers": rows,
        "vault": get_credential_vault_diagnostics(),
        "hydration": last_hydration_report(),
    }
