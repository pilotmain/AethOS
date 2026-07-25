# SPDX-License-Identifier: Apache-2.0
"""Provider credential health validation — converged with provider runtime auth."""

from __future__ import annotations

from typing import Any

from aethos_core.connections.credential_audit import append_credential_audit_event
from aethos_core.connections.validation_status import (
    INSUFFICIENT_SCOPE,
    INVALID,
    MISSING,
    RECONNECT_REQUIRED,
    SECRET_MISSING,
    VALIDATED,
)
from aethos_core.operations.orchestration.provider_runtime import (
    resolve_execution_auth,
    resolve_readonly_adapter,
)
from aethos_core.security.credential_vault import get_credential_vault
from aethos_core.security.secret_redaction import redact_text

_READ_ONLY_INVENTORY_OPERATION: dict[str, str] = {
    "github": "workflow_runs",
    "railway": "read_projects",
    "vercel": "read_projects",
}


def validate_provider_credential(*, provider: str, credential_id: str) -> dict[str, Any]:
    from aethos_core.governance.approval_privacy_governance import credential_live_validation_enabled

    vault = get_credential_vault()
    rec = vault.get(credential_id)
    if not rec or rec.provider != provider:
        return {"ok": False, "validation_status": MISSING, "detail": "Credential not found."}

    secret = vault.retrieve_secret(credential_id) or {}
    storage_diag = vault.inspect_secret_storage(credential_id)
    if not str(secret.get("token") or "").strip():
        failure_class = str(storage_diag.get("failure_class") or "secret_missing")
        validation_status = RECONNECT_REQUIRED if failure_class == "encrypted_secret_missing" else SECRET_MISSING
        diagnostics = {
            **_base_diagnostics(provider, credential_id, auth={}),
            **storage_diag,
            "failure_class": failure_class,
            "auth_source": storage_diag.get("auth_source") or "metadata_only",
        }
        result = {
            "ok": False,
            "validation_status": validation_status,
            "detail": "Credential secret missing or not decryptable.",
            "failure_class": failure_class,
            "diagnostics": diagnostics,
        }
        _finalize_validation(provider=provider, credential_id=credential_id, result=result)
        return result

    if not credential_live_validation_enabled():
        result = {
            "ok": True,
            "validation_status": VALIDATED,
            "detail": "Format-only validation (CREDENTIAL_LIVE_VALIDATION_ENABLED=false).",
            "diagnostics": _base_diagnostics(provider, credential_id, auth={"credential_id": credential_id}),
        }
        _finalize_validation(provider=provider, credential_id=credential_id, result=result)
        return result

    operation_type = _READ_ONLY_INVENTORY_OPERATION.get(provider, "read_projects")
    result = _validate_via_runtime(provider=provider, credential_id=credential_id, operation_type=operation_type)
    _finalize_validation(provider=provider, credential_id=credential_id, result=result)
    return result


def validate_all_provider_credentials(*, providers: list[str] | None = None) -> dict[str, Any]:
    from aethos_core.providers.base.provider_registry import ProviderRegistry

    vault = get_credential_vault()
    target_providers = providers or ProviderRegistry.list_credential_managed_names()
    results: list[dict[str, Any]] = []
    for provider in target_providers:
        for rec in vault.list_credentials(provider=provider):
            try:
                out = validate_provider_credential(provider=provider, credential_id=rec.credential_id)
            except Exception as exc:
                out = {
                    "ok": False,
                    "validation_status": INVALID,
                    "detail": redact_text(str(exc)),
                }
            results.append(
                {
                    "provider": provider,
                    "credential_id": rec.credential_id,
                    "masked_identifier": rec.masked_identifier,
                    **out,
                }
            )
    validated = sum(1 for r in results if r.get("ok"))
    return {
        "ok": True,
        "validated_count": validated,
        "total_count": len(results),
        "results": results,
    }


def _finalize_validation(*, provider: str, credential_id: str, result: dict[str, Any]) -> None:
    vault = get_credential_vault()
    status = str(result.get("validation_status") or (VALIDATED if result.get("ok") else INVALID))
    diagnostics = result.get("diagnostics") if isinstance(result.get("diagnostics"), dict) else {}
    if result.get("failure_class") and "failure_class" not in diagnostics:
        diagnostics = {**diagnostics, "failure_class": result.get("failure_class")}
    vault.mark_validation_result(
        credential_id,
        status=status,
        ok=bool(result.get("ok")),
        diagnostics=diagnostics or None,
    )
    append_credential_audit_event(
        event="validation_success" if result.get("ok") else "validation_failed",
        provider=provider,
        credential_id=credential_id,
        validation_status=status,
        detail=str(result.get("failure_class") or result.get("detail") or "")[:120] or None,
    )


def _base_diagnostics(provider: str, credential_id: str, *, auth: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.connections.credential_hydration import last_hydration_report

    hydration = last_hydration_report() or {}
    return {
        "credential_id_tested": credential_id,
        "provider": provider,
        "auth_source": "vault" if auth.get("credential_id") else "unresolved",
        "resolved_credential_id": auth.get("credential_id") or credential_id,
        "auth_method": auth.get("auth_method") or "api_token",
        "hydration_source": "startup_hydration" if hydration else "on_demand",
        "hydrated_at": hydration.get("hydrated_at"),
    }


def _validate_via_runtime(*, provider: str, credential_id: str, operation_type: str) -> dict[str, Any]:
    auth = resolve_execution_auth(
        provider=provider,
        operation_type=operation_type,
        params={"credential_id": credential_id},
    )
    vault = get_credential_vault()
    secret = vault.retrieve_secret(credential_id) or {}
    token = str(secret.get("token") or "").strip()
    diagnostics = _base_diagnostics(provider, credential_id, auth=auth)

    if not token:
        return {
            "ok": False,
            "validation_status": INVALID,
            "detail": "Runtime auth could not resolve API token.",
            "failure_class": "hydration_mismatch",
            "diagnostics": diagnostics,
        }

    if provider == "railway":
        return _validate_railway_runtime(token, diagnostics)
    if provider == "github":
        return _validate_github_runtime(token, auth, diagnostics)
    if provider == "vercel":
        return _validate_vercel_runtime(token, auth, diagnostics)
    return _validate_via_auth_adapter(provider=provider, credential_id=credential_id, diagnostics=diagnostics)


def _validate_via_auth_adapter(*, provider: str, credential_id: str, diagnostics: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.base.provider_registry import ProviderRegistry

    adapter = ProviderRegistry.get_auth_adapter(provider)
    if adapter is None:
        return {
            "ok": False,
            "validation_status": INVALID,
            "detail": f"Unknown provider `{provider}`.",
            "failure_class": "invalid_token",
            "diagnostics": diagnostics,
        }
    diagnostics = {**diagnostics, "validation_path": "auth_adapter_test"}
    try:
        test = adapter.test_credential(credential_id)
    except KeyError:
        return {
            "ok": False,
            "validation_status": MISSING,
            "detail": "Credential not found.",
            "failure_class": "secret_missing",
            "diagnostics": diagnostics,
        }
    except Exception as exc:
        return {
            "ok": False,
            "validation_status": INVALID,
            "detail": redact_text(str(exc)),
            "failure_class": "invalid_token",
            "diagnostics": diagnostics,
        }
    if test.get("ok"):
        return {
            "ok": True,
            "validation_status": VALIDATED,
            "detail": str(test.get("detail") or f"{provider.title()} token validated."),
            "diagnostics": diagnostics,
        }
    return {
        "ok": False,
        "validation_status": INVALID,
        "detail": redact_text(str(test.get("detail") or "Credential test failed.")),
        "failure_class": "invalid_token",
        "diagnostics": diagnostics,
    }


def _validate_railway_runtime(token: str, diagnostics: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.railway.api_client import RAILWAY_GRAPHQL_URL
    from aethos_core.providers.railway.credential_truth import (
        RAILWAY_VALIDATION_PROBE,
        validate_railway_api_connection,
    )

    validation = validate_railway_api_connection(token)
    diagnostics = {
        **diagnostics,
        "endpoint": RAILWAY_GRAPHQL_URL,
        "graphql_operation": RAILWAY_VALIDATION_PROBE,
        "validation_path": "readonly_inventory",
        "readonly_inventory_ok": validation.ok,
        "readonly_inventory_service_count": validation.service_count,
        "readonly_inventory_project_count": validation.project_count,
    }

    if validation.ok:
        return {
            "ok": True,
            "validation_status": VALIDATED,
            "detail": validation.detail,
            "diagnostics": diagnostics,
        }

    err = validation.detail
    failure_class = "invalid_token" if "auth" in err.lower() or "unauthorized" in err.lower() else "invalid_validation_query"
    if validation.service_count == 0 and "scope" in err.lower():
        failure_class = "insufficient_scope"
    return {
        "ok": False,
        "validation_status": INSUFFICIENT_SCOPE if failure_class == "insufficient_scope" else INVALID,
        "detail": err,
        "failure_class": failure_class,
        "diagnostics": {**diagnostics, "graphql_errors": [validation.graphql_error] if validation.graphql_error else []},
    }


def _validate_github_runtime(token: str, auth: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.github.api_client import list_repositories, test_connection

    diagnostics = {**diagnostics, "validation_path": "provider_runtime", "endpoint": "https://api.github.com/user"}
    conn = test_connection(token)
    diagnostics["http_status"] = 200 if conn.get("ok") else 401
    if not conn.get("ok"):
        return {
            "ok": False,
            "validation_status": INVALID,
            "detail": redact_text(str(conn.get("detail") or "GitHub auth failed.")),
            "failure_class": "invalid_token",
            "diagnostics": diagnostics,
        }

    adapter = resolve_readonly_adapter(provider="github", auth=auth)
    diagnostics["readonly_adapter_available"] = adapter is not None
    listed = list_repositories(token)
    diagnostics["repository_access"] = bool(listed.get("ok"))
    if not listed.get("ok"):
        return {
            "ok": False,
            "validation_status": INSUFFICIENT_SCOPE,
            "detail": redact_text(str(listed.get("error") or "Repository list failed.")),
            "failure_class": "insufficient_scope",
            "diagnostics": diagnostics,
        }
    return {
        "ok": True,
        "validation_status": VALIDATED,
        "detail": str(conn.get("detail") or "GitHub token validated."),
        "diagnostics": diagnostics,
        "account_login": conn.get("account_login"),
    }


def _validate_vercel_runtime(token: str, auth: dict[str, Any], diagnostics: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.vercel.api_client import test_connection

    diagnostics = {**diagnostics, "validation_path": "provider_runtime", "endpoint": "https://api.vercel.com/v2/user"}
    try:
        conn = test_connection(token)
    except Exception as exc:
        return {
            "ok": False,
            "validation_status": INVALID,
            "detail": redact_text(str(exc)),
            "failure_class": "invalid_token",
            "diagnostics": diagnostics,
        }
    diagnostics["http_status"] = 200 if conn.get("ok") else 401
    diagnostics["readonly_adapter_available"] = resolve_readonly_adapter(provider="vercel", auth=auth) is not None
    if not conn.get("ok"):
        return {
            "ok": False,
            "validation_status": INVALID,
            "detail": redact_text(str(conn.get("detail") or "Vercel auth failed.")),
            "failure_class": "invalid_token",
            "diagnostics": diagnostics,
        }
    return {
        "ok": True,
        "validation_status": VALIDATED,
        "detail": str(conn.get("detail") or "Vercel token validated."),
        "diagnostics": diagnostics,
    }


def _safe_graphql_errors(errors: Any) -> list[str]:
    if not isinstance(errors, list):
        return []
    out: list[str] = []
    for row in errors[:3]:
        if isinstance(row, dict):
            out.append(redact_text(str(row.get("message") or row))[:180])
        else:
            out.append(redact_text(str(row))[:180])
    return out
