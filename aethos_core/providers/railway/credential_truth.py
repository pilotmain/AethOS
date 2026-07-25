# SPDX-License-Identifier: Apache-2.0
"""Single Railway credential resolution and validation truth path."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from aethos_core.connections.validation_status import CONFIGURED, VALIDATED
from aethos_core.providers.railway.api_client import RAILWAY_GRAPHQL_URL, list_services_with_status

RailwayCredentialSource = Literal[
    "explicit_credential",
    "validated_vault",
    "environment",
    "none",
]

RAILWAY_VALIDATION_PROBE = "ProjectsAndServices"
RAILWAY_VALIDATION_ENDPOINT = RAILWAY_GRAPHQL_URL


@dataclass(frozen=True)
class RailwayCredentialResolution:
    token: str | None
    source: RailwayCredentialSource
    credential_id: str
    masked_identifier: str
    resolver: str
    detail: str
    vault_validation_status: str = ""
    env_present: bool = False

    @property
    def ok(self) -> bool:
        return bool(self.token)


@dataclass(frozen=True)
class RailwayConnectionValidation:
    ok: bool
    probe: str
    endpoint: str
    detail: str
    service_count: int = 0
    project_count: int = 0
    graphql_error: str = ""
    http_status: int | None = None
    rate_limited: bool = False

    def to_checks_fields(self) -> dict[str, Any]:
        return {
            "railway_api_connection_ok": self.ok,
            "railway_api_connection_detail": self.detail,
            "railway_api_connection_status_code": self.http_status,
            "railway_api_connection_rate_limited": self.rate_limited,
            "railway_validation_probe": self.probe,
            "railway_validation_endpoint": self.endpoint,
            "railway_validation_service_count": self.service_count,
            "railway_validation_project_count": self.project_count,
        }


def resolve_railway_credential(*, credential_id: str | None = None) -> RailwayCredentialResolution:
    """
    Canonical resolver order (all Railway execution paths):

    1. Explicit credential_id (when provided and decryptable)
    2. Validated vault credential (validation_status == validated)
    3. Environment token (settings.railway_api_token / RAILWAY_API_TOKEN)
    """
    from aethos_core.config import get_settings
    from aethos_core.connections.credential_state import resolve_credential_state
    from aethos_core.credentials.provider_alias_resolution import (
        env_token_for_canonical_provider,
        list_credentials_for_canonical,
    )
    from aethos_core.security.credential_vault import get_credential_vault

    settings = get_settings()
    env_token = env_token_for_canonical_provider("railway")
    env_present = bool(env_token or str(getattr(settings, "railway_api_token", "") or "").strip())

    if credential_id:
        resolved = _load_vault_token(credential_id, source="explicit_credential")
        if resolved.ok:
            return resolved

    for rec in list_credentials_for_canonical("railway"):
        if rec.revoked:
            continue
        state = resolve_credential_state(rec.credential_id)
        if not state.get("decryptable"):
            continue
        if str(rec.validation_status or "") != VALIDATED:
            continue
        loaded = _load_vault_token(rec.credential_id, source="validated_vault")
        if loaded.ok:
            return loaded

    for rec in list_credentials_for_canonical("railway"):
        if rec.revoked:
            continue
        state = resolve_credential_state(rec.credential_id)
        if not state.get("decryptable"):
            continue
        if str(rec.validation_status or "") != CONFIGURED:
            continue
        loaded = _load_vault_token(rec.credential_id, source="explicit_credential")
        if loaded.ok:
            return loaded

    if env_token:
        return RailwayCredentialResolution(
            token=env_token,
            source="environment",
            credential_id="",
            masked_identifier=_mask_token(env_token),
            resolver="railway.credential_truth.resolve_railway_credential",
            detail="Environment Railway token resolved.",
            vault_validation_status="",
            env_present=True,
        )

    return RailwayCredentialResolution(
        token=None,
        source="none",
        credential_id=str(credential_id or ""),
        masked_identifier="",
        resolver="railway.credential_truth.resolve_railway_credential",
        detail="No validated vault credential or environment Railway token available.",
        env_present=env_present,
    )


def _load_vault_token(credential_id: str, *, source: RailwayCredentialSource) -> RailwayCredentialResolution:
    from aethos_core.connections.credential_state import resolve_credential_state
    from aethos_core.security.credential_vault import get_credential_vault

    vault = get_credential_vault()
    rec = vault.get(credential_id)
    if not rec or rec.revoked:
        return RailwayCredentialResolution(
            token=None,
            source="none",
            credential_id=credential_id,
            masked_identifier="",
            resolver="railway.credential_truth.resolve_railway_credential",
            detail="Credential not found or revoked.",
        )
    secret = vault.retrieve_secret(credential_id) or {}
    token = str(secret.get("token") or "").strip()
    state = resolve_credential_state(credential_id)
    if not token:
        return RailwayCredentialResolution(
            token=None,
            source="none",
            credential_id=credential_id,
            masked_identifier=rec.masked_identifier or "",
            resolver="railway.credential_truth.resolve_railway_credential",
            detail="Credential secret not decryptable.",
            vault_validation_status=str(rec.validation_status or ""),
        )
    source_label: RailwayCredentialSource = source
    if source == "explicit_credential" and str(rec.validation_status or "") == VALIDATED:
        source_label = "validated_vault"
    return RailwayCredentialResolution(
        token=token,
        source=source_label,
        credential_id=credential_id,
        masked_identifier=rec.masked_identifier or _mask_token(token),
        resolver="railway.credential_truth.resolve_railway_credential",
        detail="ok",
        vault_validation_status=str(rec.validation_status or ""),
    )


def validate_railway_api_connection(token: str) -> RailwayConnectionValidation:
    """Shared probe — same as Connections UI validation (ProjectsAndServices)."""
    if not str(token or "").strip():
        return RailwayConnectionValidation(
            ok=False,
            probe=RAILWAY_VALIDATION_PROBE,
            endpoint=RAILWAY_VALIDATION_ENDPOINT,
            detail="Railway API token missing.",
        )
    inventory = list_services_with_status(token)
    services = list(inventory.get("services") or [])
    project_names = {
        str(s.get("project_name") or "")
        for s in services
        if isinstance(s, dict) and s.get("project_name")
    }
    if inventory.get("ok"):
        return RailwayConnectionValidation(
            ok=True,
            probe=RAILWAY_VALIDATION_PROBE,
            endpoint=RAILWAY_VALIDATION_ENDPOINT,
            detail=f"Railway token validated via {RAILWAY_VALIDATION_PROBE} ({len(services)} service(s)).",
            service_count=len(services),
            project_count=len(project_names),
        )
    err = str(inventory.get("error") or "Railway inventory validation failed.")
    status_code = inventory.get("status_code")
    from aethos_core.provider_e2e_readiness.blocker_mapping import is_rate_limited_detail

    rate_limited = is_rate_limited_detail(err, status_code=status_code)
    return RailwayConnectionValidation(
        ok=False,
        probe=RAILWAY_VALIDATION_PROBE,
        endpoint=RAILWAY_VALIDATION_ENDPOINT,
        detail=err,
        graphql_error=err,
        http_status=status_code if isinstance(status_code, int) else None,
        rate_limited=rate_limited,
    )


def resolve_and_validate_railway_credential(
    *,
    credential_id: str | None = None,
) -> tuple[RailwayCredentialResolution, RailwayConnectionValidation | None]:
    resolution = resolve_railway_credential(credential_id=credential_id)
    if not resolution.ok or not resolution.token:
        return resolution, None
    validation = validate_railway_api_connection(resolution.token)
    return resolution, validation


def credential_source_label(source: RailwayCredentialSource) -> str:
    mapping = {
        "explicit_credential": "Explicit Vault Credential",
        "validated_vault": "Validated Vault Credential",
        "environment": "Environment Token",
        "none": "None",
    }
    return mapping.get(source, source)


def diagnose_railway_credential_truth() -> dict[str, Any]:
    resolution, validation = resolve_and_validate_railway_credential()
    from aethos_core.connections.credential_runtime_gate import check_provider_credential_gate

    gate = check_provider_credential_gate("railway", require_validated=True)
    return {
        "credential_source": resolution.source,
        "credential_source_label": credential_source_label(resolution.source),
        "credential_id": resolution.credential_id,
        "masked_identifier": resolution.masked_identifier,
        "resolver": resolution.resolver,
        "validation_probe": RAILWAY_VALIDATION_PROBE,
        "readiness_probe": RAILWAY_VALIDATION_PROBE,
        "validation_endpoint": RAILWAY_VALIDATION_ENDPOINT,
        "token_resolved": resolution.ok,
        "resolution_detail": resolution.detail,
        "env_present": resolution.env_present,
        "vault_validation_status": resolution.vault_validation_status,
        "provider_gate_validated": bool(gate.get("ok")),
        "provider_gate_state": str(gate.get("credential_state") or ""),
        "connection_validation_ok": bool(validation.ok) if validation else False,
        "connection_validation_detail": validation.detail if validation else "",
        "service_count": validation.service_count if validation else 0,
        "project_count": validation.project_count if validation else 0,
        "trust_aligned": _trust_aligned(resolution, validation, gate),
        "trust_note": _trust_note(resolution, validation, gate),
    }


def _trust_aligned(
    resolution: RailwayCredentialResolution,
    validation: RailwayConnectionValidation | None,
    gate: dict[str, Any],
) -> bool:
    if not resolution.ok:
        return gate.get("credential_state") in {"missing", "invalid", None}
    if not validation:
        return False
    if gate.get("ok") and resolution.source in {"validated_vault", "explicit_credential"}:
        return validation.ok
    if resolution.source == "environment":
        return validation.ok
    return validation.ok


def _trust_note(
    resolution: RailwayCredentialResolution,
    validation: RailwayConnectionValidation | None,
    gate: dict[str, Any],
) -> str:
    if resolution.source == "environment" and gate.get("ok"):
        return (
            "Validated vault credential exists but canonical resolver selected environment token "
            "because no validated vault credential was available at resolution time."
        )
    if gate.get("ok") and validation and not validation.ok:
        return "Vault UI state is validated but live probe failed — token may have changed or been revoked."
    if not gate.get("ok") and validation and validation.ok:
        return "Live probe passed but vault gate is not validated — reconnect or revalidate in Connections."
    if resolution.source == "none":
        return "No Railway credential resolved."
    return "Credential source and live probe are aligned."


def _mask_token(token: str) -> str:
    from aethos_core.security.secret_redaction import mask_secret

    return mask_secret(token, visible=4)


def checks_credential_metadata(resolution: RailwayCredentialResolution, validation: RailwayConnectionValidation | None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "railway_credential_source": resolution.source,
        "railway_credential_source_label": credential_source_label(resolution.source),
        "railway_credential_id": resolution.credential_id,
        "railway_credential_masked_identifier": resolution.masked_identifier,
        "railway_credential_resolver": resolution.resolver,
        "railway_validation_probe": RAILWAY_VALIDATION_PROBE,
    }
    if validation:
        out.update(validation.to_checks_fields())
    return out
