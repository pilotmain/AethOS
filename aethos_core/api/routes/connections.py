# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

from aethos_core.connections.credential_audit import append_credential_audit_event
from aethos_core.connections.models import AuthMethod
from aethos_core.connections.service_registry import get_auth_adapter, get_connection, list_connections
from aethos_core.security.credential_vault import get_credential_vault, get_credential_vault_diagnostics
from aethos_core.security.secret_redaction import redact_text

_log = logging.getLogger(__name__)

router = APIRouter(tags=["connections"])


class StoreCredentialIn(BaseModel):
    type: str = Field(default="api_token", max_length=32)
    label: str = Field(default="", max_length=120)
    token: str = Field(default="", max_length=65536)
    secret: str = Field(default="", max_length=65536)
    scope: list[str] = Field(default_factory=lambda: ["read_projects", "read_logs"])
    write_allowed: bool = False

    @model_validator(mode="after")
    def _require_token(self) -> StoreCredentialIn:
        resolved = (self.token or self.secret or "").strip()
        if len(resolved) < 8:
            raise ValueError("Token must be at least 8 characters.")
        self.token = resolved
        return self

    def resolved_token(self) -> str:
        return (self.token or self.secret or "").strip()


class PreferredAuthIn(BaseModel):
    preferred_method: str = Field(min_length=3, max_length=32)


class DeploymentEnvValuesIn(BaseModel):
    repo: str = Field(default="", max_length=200)
    project: str = Field(default="", max_length=120)
    environment: str = Field(default="", max_length=64)
    service_name: str = Field(default="", max_length=120)
    target_key: str = Field(default="", max_length=240)
    values: dict[str, str] = Field(default_factory=dict)


def _structured_error(
    *,
    code: str,
    detail: str,
    status_code: int = 400,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "code": code,
            "detail": redact_text(detail),
        },
    )


def _connection_payload(provider: str) -> dict[str, Any]:
    try:
        return get_connection(provider).to_dict()
    except Exception as exc:
        _log.exception("connection_status_failed provider=%s", provider)
        return {"provider": provider, "error": redact_text(str(exc))}


@router.get("/connections/credential-center")
def get_credential_center() -> dict[str, Any]:
    from aethos_core.connections.credential_hydration import build_credential_center_payload

    return build_credential_center_payload()


@router.get("/connections/deployment-env-values/context")
def get_deployment_env_values_context(
    repo: str = "",
    project: str = "",
    environment: str = "",
    service_name: str = "",
    target_key: str = "",
    required_names: str = "",
) -> dict[str, Any]:
    from aethos_core.providers.railway.env_value_readiness.deployment_env_guidance import (
        assess_deployment_env_for_plan,
    )
    from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import (
        build_target_key_for_plan,
    )

    plan = {
        "repo": (repo or "").strip(),
        "project": (project or "").strip(),
        "environment": (environment or "").strip(),
        "service_name": (service_name or "").strip(),
    }
    if (target_key or "").strip():
        parts = (target_key or "").split("|")
        if len(parts) >= 4:
            plan = {
                "repo": parts[0],
                "project": parts[1],
                "environment": parts[2],
                "service_name": parts[3],
            }
    resolved_key = (target_key or "").strip() or build_target_key_for_plan(plan)
    names = [n.strip().upper() for n in (required_names or "").split(",") if n.strip()]
    assessment = assess_deployment_env_for_plan(
        plan=plan,
        env_report={"required_env_var_names": names},
    )
    payload = assessment.to_dict()
    payload["target_key"] = resolved_key
    payload["ok"] = True
    return payload


@router.post("/connections/deployment-env-values")
def post_deployment_env_values(body: DeploymentEnvValuesIn) -> dict[str, Any]:
    from aethos_core.providers.railway.env_value_readiness.deployment_env_store import (
        register_deployment_env_values,
    )
    from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import (
        build_target_key_for_plan,
    )

    plan = {
        "repo": body.repo.strip(),
        "project": body.project.strip(),
        "environment": body.environment.strip(),
        "service_name": body.service_name.strip(),
    }
    target_key = body.target_key.strip() or build_target_key_for_plan(plan)
    if not target_key.replace("|", "").strip():
        return _structured_error(
            code="DEPLOYMENT_TARGET_REQUIRED",
            detail="repo, project, environment, and service_name (or target_key) are required.",
        )
    if not body.values:
        return _structured_error(code="VALUES_REQUIRED", detail="At least one env value is required.")
    registered = register_deployment_env_values(target_key=target_key, values=body.values)
    append_credential_audit_event(
        {
            "event_type": "deployment_env_values_stored",
            "target_key": target_key,
            "registered_names": registered,
            "count": len(registered),
        }
    )
    return {
        "ok": True,
        "target_key": target_key,
        "registered_names": registered,
        "count": len(registered),
    }


@router.post("/connections/hydrate")
def post_hydrate_credentials() -> dict[str, Any]:
    from aethos_core.connections.credential_hydration import reload_credential_runtime

    report = reload_credential_runtime(validate=True)
    return {"ok": True, "hydration": report}


@router.get("/connections/diagnostics")
def get_connections_diagnostics() -> dict[str, Any]:
    vault = get_credential_vault_diagnostics()
    return {"credential_vault": vault, "ok": vault.get("available", False)}


@router.get("/connections")
def get_connections() -> dict[str, Any]:
    payload = list_connections()
    payload["credential_vault"] = get_credential_vault_diagnostics()
    return payload


@router.get("/connections/{provider}")
def get_provider_connection(provider: str) -> dict[str, Any]:
    if provider == "diagnostics":
        return get_connections_diagnostics()
    if provider == "credential-center":
        return get_credential_center()
    try:
        data = get_connection(provider).to_dict()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown provider") from exc
    data["credential_vault"] = get_credential_vault_diagnostics()
    return data


@router.post("/connections/{provider}/credentials", response_model=None)
def post_store_credential(provider: str, body: StoreCredentialIn):
    adapter = get_auth_adapter(provider)
    if adapter is None:
        return _structured_error(code="UNKNOWN_PROVIDER", detail="Unknown provider", status_code=404)
    if body.type != "api_token":
        return _structured_error(
            code="UNSUPPORTED_CREDENTIAL_TYPE",
            detail="Only api_token is supported.",
            status_code=422,
        )

    vault_diag = get_credential_vault_diagnostics()
    if not vault_diag.get("available"):
        deps = vault_diag.get("dependencies") or {}
        if deps.get("cryptography") != "installed":
            return _structured_error(
                code="CREDENTIAL_VAULT_UNAVAILABLE",
                detail="Credential vault dependency missing (`cryptography`). Install it in the API runtime venv.",
                status_code=503,
            )
        return _structured_error(
            code="CREDENTIAL_VAULT_UNAVAILABLE",
            detail="Credential vault storage is not writable. Check data/credentials permissions.",
            status_code=503,
        )

    try:
        vault = get_credential_vault()
        record = vault.store_api_token(
            provider=provider,
            label=body.label or f"{provider.title()} API token",
            token=body.resolved_token(),
            scope=body.scope,
            write_allowed=body.write_allowed,
        )
        append_credential_audit_event(
            event="provider_connected",
            provider=provider,
            credential_id=record.credential_id,
        )
    except ValueError as exc:
        return _structured_error(code="INVALID_CREDENTIAL_PAYLOAD", detail=str(exc), status_code=422)
    except Exception as exc:
        from aethos_core.security.credential_vault import CredentialPersistenceError

        if isinstance(exc, CredentialPersistenceError):
            return _structured_error(
                code="CREDENTIAL_PERSISTENCE_FAILED",
                detail=str(exc),
                status_code=500,
            )
        _log.exception("credential_save_failed provider=%s", provider)
        return _structured_error(
            code="CREDENTIAL_SAVE_FAILED",
            detail=str(exc),
            status_code=500,
        )

    from aethos_core.connections.credential_validation import validate_provider_credential

    test_result = validate_provider_credential(provider=provider, credential_id=record.credential_id)
    if test_result.get("ok"):
        vault.set_preferred_method(provider, "api_token")

    from aethos_core.connections.credential_hydration import reload_credential_runtime

    reload_credential_runtime(validate=True)

    from aethos_core.llm.model_providers import refresh_live_models_for_provider

    try:
        refresh_live_models_for_provider(provider, force=True)
    except Exception:  # noqa: BLE001
        _log.debug("live_model_refresh_skipped provider=%s", provider)

    return {
        "ok": True,
        "credential": record.to_public_dict(),
        "test": test_result,
        "connection": _connection_payload(provider),
        "credential_vault": get_credential_vault_diagnostics(),
    }


@router.post("/connections/{provider}/credentials/{credential_id}/test", response_model=None)
def post_test_credential(provider: str, credential_id: str):
    adapter = get_auth_adapter(provider)
    if adapter is None:
        return _structured_error(code="UNKNOWN_PROVIDER", detail="Unknown provider", status_code=404)
    try:
        result = adapter.test_credential(credential_id)
    except KeyError:
        return _structured_error(code="CREDENTIAL_NOT_FOUND", detail="Credential not found", status_code=404)
    except Exception as exc:
        _log.exception("credential_test_failed id=%s", credential_id)
        return _structured_error(code="CREDENTIAL_TEST_FAILED", detail=str(exc), status_code=500)
    return {"ok": True, "test": result, "connection": _connection_payload(provider)}


@router.post("/connections/{provider}/credentials/{credential_id}/revalidate", response_model=None)
def post_revalidate_credential(provider: str, credential_id: str):
    if get_auth_adapter(provider) is None:
        return _structured_error(code="UNKNOWN_PROVIDER", detail="Unknown provider", status_code=404)
    from aethos_core.connections.credential_runtime_gate import check_credential_gate

    gate = check_credential_gate(credential_id, provider=provider, require_validated=False)
    if gate.get("auth_source") == "metadata_only" or not gate.get("decryptable"):
        return _structured_error(
            code="CREDENTIAL_RECONNECT_REQUIRED",
            detail=gate.get("detail") or "Encrypted secret is missing. Reconnect the credential.",
            status_code=409,
        )
    from aethos_core.connections.credential_validation import validate_provider_credential

    result = validate_provider_credential(provider=provider, credential_id=credential_id)
    from aethos_core.connections.credential_hydration import reload_credential_runtime

    reload_credential_runtime(validate=True)
    return {
        "ok": bool(result.get("ok")),
        "validation": result,
        "connection": _connection_payload(provider),
    }


@router.post("/connections/{provider}/credentials/{credential_id}/rotate", response_model=None)
def post_rotate_credential(provider: str, credential_id: str, body: StoreCredentialIn):
    adapter = get_auth_adapter(provider)
    if adapter is None:
        return _structured_error(code="UNKNOWN_PROVIDER", detail="Unknown provider", status_code=404)
    vault = get_credential_vault()
    rec = vault.get(credential_id)
    if not rec or rec.provider != provider:
        return _structured_error(code="CREDENTIAL_NOT_FOUND", detail="Credential not found", status_code=404)
    try:
        vault.rotate_api_token(credential_id, token=body.resolved_token())
    except ValueError as exc:
        return _structured_error(code="INVALID_CREDENTIAL_PAYLOAD", detail=str(exc), status_code=422)
    except Exception as exc:
        from aethos_core.security.credential_vault import CredentialPersistenceError

        if isinstance(exc, CredentialPersistenceError):
            return _structured_error(
                code="CREDENTIAL_PERSISTENCE_FAILED",
                detail=str(exc),
                status_code=500,
            )
        raise
    append_credential_audit_event(
        event="token_rotated",
        provider=provider,
        credential_id=credential_id,
    )
    from aethos_core.connections.credential_validation import validate_provider_credential

    validation = validate_provider_credential(provider=provider, credential_id=credential_id)
    from aethos_core.connections.credential_hydration import reload_credential_runtime

    reload_credential_runtime(validate=True)
    return {
        "ok": True,
        "rotated": True,
        "credential_id": credential_id,
        "validation": validation,
        "connection": _connection_payload(provider),
    }


@router.post("/connections/{provider}/repair", response_model=None)
def post_repair_credential(provider: str, body: StoreCredentialIn):
    if get_auth_adapter(provider) is None:
        return _structured_error(code="UNKNOWN_PROVIDER", detail="Unknown provider", status_code=404)
    vault_diag = get_credential_vault_diagnostics()
    if not vault_diag.get("available"):
        return _structured_error(
            code="CREDENTIAL_VAULT_UNAVAILABLE",
            detail="Credential vault storage is not writable.",
            status_code=503,
        )
    from aethos_core.connections.credential_repair import repair_provider_credential

    try:
        result = repair_provider_credential(
            provider=provider,
            token=body.resolved_token(),
            label=body.label or f"{provider.title()} API token",
            scope=body.scope,
            write_allowed=body.write_allowed,
        )
    except Exception as exc:
        from aethos_core.security.credential_vault import CredentialPersistenceError

        if isinstance(exc, CredentialPersistenceError):
            return _structured_error(
                code="CREDENTIAL_PERSISTENCE_FAILED",
                detail=str(exc),
                status_code=500,
            )
        _log.exception("credential_repair_failed provider=%s", provider)
        return _structured_error(code="CREDENTIAL_REPAIR_FAILED", detail=str(exc), status_code=500)

    append_credential_audit_event(
        event="credential_repaired",
        provider=provider,
        credential_id=result.get("credential_id"),
        validation_status=str((result.get("validation") or {}).get("validation_status") or ""),
    )
    return {
        "ok": bool(result.get("runtime_usable")),
        "repair": result,
        "connection": _connection_payload(provider),
        "credential_vault": get_credential_vault_diagnostics(),
    }


@router.post("/connections/{provider}/credentials/{credential_id}/revoke", response_model=None)
def post_revoke_credential(provider: str, credential_id: str):
    adapter = get_auth_adapter(provider)
    if adapter is None:
        return _structured_error(code="UNKNOWN_PROVIDER", detail="Unknown provider", status_code=404)
    if not adapter.revoke_credential(credential_id):
        return _structured_error(code="CREDENTIAL_NOT_FOUND", detail="Credential not found", status_code=404)
    append_credential_audit_event(
        event="provider_removed",
        provider=provider,
        credential_id=credential_id,
    )
    from aethos_core.connections.credential_hydration import reload_credential_runtime

    reload_credential_runtime(validate=True)
    return {
        "ok": True,
        "revoked": True,
        "credential_id": credential_id,
        "connection": _connection_payload(provider),
    }


@router.post("/connections/{provider}/preferred-auth", response_model=None)
def post_preferred_auth(provider: str, body: PreferredAuthIn):
    if get_auth_adapter(provider) is None:
        return _structured_error(code="UNKNOWN_PROVIDER", detail="Unknown provider", status_code=404)
    try:
        method = AuthMethod(body.preferred_method)
    except ValueError:
        return _structured_error(code="INVALID_PREFERRED_METHOD", detail="Invalid preferred_method", status_code=422)
    get_credential_vault().set_preferred_method(provider, method.value)
    return {
        "ok": True,
        "preferred_method": method.value,
        "connection": _connection_payload(provider),
    }


@router.get("/connections/{provider}/resolve-auth", response_model=None)
def get_resolve_auth(provider: str, operation: str = "read_projects"):
    adapter = get_auth_adapter(provider)
    if adapter is None:
        return _structured_error(code="UNKNOWN_PROVIDER", detail="Unknown provider", status_code=404)
    resolved = adapter.resolve_best_auth_method(operation=operation)
    if resolved.get("detail"):
        resolved["detail"] = redact_text(str(resolved["detail"]))
    return resolved
