# SPDX-License-Identifier: Apache-2.0
"""FIX 303 — provider connection readiness evaluation."""

from __future__ import annotations

import shutil
from typing import Any

from aethos_core.connections.credential_runtime_gate import check_provider_credential_gate
from aethos_core.credentials.provider_alias_resolution import env_token_for_canonical_provider
from aethos_core.provider_discovery.provider_capabilities import capabilities_public_dict


def _canonical(provider: str) -> str:
    return (provider or "").strip().lower()


def evaluate_provider_readiness(*, provider: str, matrix_row: dict[str, Any] | None = None) -> dict[str, Any]:
    canonical = _canonical(provider)
    row = matrix_row or {}
    token = env_token_for_canonical_provider(canonical) if canonical in {"github", "railway", "vercel"} else None
    cli_ready = canonical == "vercel" and shutil.which("vercel") is not None
    credentials_present = bool(token) or cli_ready

    gate: dict[str, Any] = {"ok": False, "credential_state": "missing"}
    if canonical in {"github", "railway", "vercel"}:
        try:
            gate = check_provider_credential_gate(canonical, require_validated=False)
        except Exception:
            gate = {"ok": False, "credential_state": "unknown", "detail": "Credential gate unavailable."}

    vault_configured = bool(gate.get("ok"))
    permissions_sufficient = vault_configured or credentials_present
    scopes_sufficient = permissions_sufficient
    provider_reachable = credentials_present and (
        vault_configured or bool(token) or cli_ready or row.get("readiness") == "ready"
    )

    if canonical in {"aws", "azure", "gcp", "kubernetes"}:
        return {
            "provider": provider,
            "phase": "phase_2",
            "status": "PLANNED",
            "readiness": "planned",
            "credentials_present": False,
            "permissions_sufficient": False,
            "scopes_sufficient": False,
            "provider_reachable": False,
            "connection_flow_available": False,
            "read_only": True,
        }

    readiness = "ready" if provider_reachable else ("not_configured" if not credentials_present else "partial")
    return {
        "provider": provider,
        "phase": "phase_1",
        "status": row.get("status") or ("OPERATIONAL" if provider_reachable else "EXPERIMENTAL"),
        "readiness": row.get("readiness") or readiness,
        "credentials_present": credentials_present,
        "permissions_sufficient": permissions_sufficient,
        "scopes_sufficient": scopes_sufficient,
        "provider_reachable": provider_reachable,
        "token_configured": bool(token),
        "cli_available": cli_ready,
        "credential_gate_ok": vault_configured,
        "credential_state": gate.get("credential_state"),
        "connection_flow_available": True,
        "provider_mutation_authority": False,
        "read_only": True,
    }


def build_provider_connection_report(
    *,
    provider: str,
    matrix_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
        PROVIDER_CAPABILITY_UNLOCKS,
        PROVIDER_PERMISSION_REQUIREMENTS,
        PROVIDER_SETUP_GUIDANCE,
    )

    readiness = evaluate_provider_readiness(provider=provider, matrix_row=matrix_row)
    canonical = _canonical(provider)
    caps = capabilities_public_dict(canonical) if canonical in {"github", "railway", "vercel"} else {}
    unlocks = dict(PROVIDER_CAPABILITY_UNLOCKS).get(provider, ())
    permissions = dict(PROVIDER_PERMISSION_REQUIREMENTS).get(provider, ())
    guidance = dict(PROVIDER_SETUP_GUIDANCE).get(provider, "")

    base = {
        "report_id": f"{canonical}-connection-report",
        "provider": provider,
        "readiness": readiness,
        "capability_unlocks": list(unlocks),
        "permission_requirements": list(permissions),
        "setup_guidance": guidance,
        "secret_collection_in_chat_forbidden": True,
        "automatic_provider_connection_enabled": False,
        "read_only": True,
    }

    if provider == "GitHub":
        base.update(
            {
                "connection_readiness": readiness["readiness"],
                "repository_visibility": "readonly_when_connected",
                "workflow_visibility": list(caps.get("readonly") or [])[:6],
                "operations": caps,
            }
        )
    elif provider == "Railway":
        base.update(
            {
                "project_visibility": "readonly_when_connected",
                "service_visibility": list(caps.get("readonly") or [])[:6],
                "deployment_visibility": "readonly_inventory_and_logs",
                "operations": caps,
            }
        )
    elif provider == "Vercel":
        base.update(
            {
                "project_visibility": "readonly_when_connected",
                "deployment_visibility": list(caps.get("readonly") or [])[:6],
                "environment_visibility": "readonly_env_metadata",
                "operations": caps,
            }
        )
    else:
        base["status"] = "PLANNED"
        base["connection_flow_available"] = False

    return base
