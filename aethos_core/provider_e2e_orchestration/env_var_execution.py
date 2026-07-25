# SPDX-License-Identifier: Apache-2.0
"""Governed env var application — names in reports, never values."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_e2e_orchestration.job_model import ProviderE2EJobModel


def apply_env_vars(
    model: ProviderE2EJobModel,
    *,
    params: dict[str, Any],
    mutation_execution_approved: bool,
) -> dict[str, Any]:
    if not mutation_execution_approved:
        return {
            "ok": False,
            "skipped": True,
            "reason": "missing_approval",
            "applied_names": [],
            "failed_names": [],
        }

    names = list(model.env_var_names or [])
    if not names:
        return {
            "ok": True,
            "skipped": True,
            "reason": "no_env_vars_configured",
            "applied_names": [],
            "failed_names": [],
            "detail": "No env vars configured for this orchestration — step skipped.",
        }

    test_values = params.get("_test_env_values")
    if isinstance(test_values, dict) and test_values:
        return _apply_test_env_values(model, names, test_values)

    if model.provider == "railway":
        return _apply_railway_env_vars(model, params, names)
    if model.provider == "vercel":
        return _apply_vercel_env_vars(model, params, names)
    return {"ok": False, "reason": "unsupported_provider", "applied_names": [], "failed_names": names}


def _apply_test_env_values(model: ProviderE2EJobModel, names: list[str], values: dict[str, Any]) -> dict[str, Any]:
    applied: list[str] = []
    failed: list[str] = []
    for name in names:
        if str(values.get(name) or values.get(name.upper()) or "").strip():
            applied.append(name)
        else:
            failed.append(name)
    if failed:
        return {
            "ok": False,
            "applied_names": applied,
            "failed_names": failed,
            "detail": f"Missing test values for: {', '.join(failed)}",
        }
    return {
        "ok": True,
        "applied_names": applied,
        "failed_names": [],
        "detail": f"Resolved {len(applied)} env var(s) from test harness (values not logged).",
        "test_mode": True,
    }


def _apply_railway_env_vars(model: ProviderE2EJobModel, params: dict[str, Any], names: list[str]) -> dict[str, Any]:
    from aethos_core.providers.railway.mutations import execute_railway_set_env_var, resolve_railway_mutation_credentials
    from aethos_core.providers.railway.target_resolver import ProviderTarget
    from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import resolve_env_var_from_secure_store

    plan = {
        "repo": str(params.get("referenced_github_repo") or ""),
        "project": model.project_name,
        "environment": model.environment,
        "service_name": model.service_name,
    }
    applied: list[str] = []
    failed: list[str] = []
    errors: list[str] = []

    for name in names:
        resolved = resolve_env_var_from_secure_store(name, plan=plan)
        if not resolved.ok or not resolved.value:
            failed.append(name)
            errors.extend(resolved.errors or [resolved.blocked_reason or "secure store miss"])
            continue
        target = ProviderTarget(
            provider="railway",
            service_name=model.service_name,
            project_name=model.project_name,
            environment=model.environment,
            resolved=True,
        )
        exec_params = {
            "target_name": model.service_name,
            "target": target.to_dict(),
            "env_var_name": name,
            "env_var_value": resolved.value,
            "mutation_execution_approved": True,
        }
        result = execute_railway_set_env_var(params=exec_params, request_id=str(params.get("approval_id") or "e2e"), target=target)
        if result.get("ok"):
            applied.append(name)
        else:
            failed.append(name)
            errors.append(str(result.get("detail") or "apply failed"))

    _ = resolve_railway_mutation_credentials()
    return {
        "ok": not failed,
        "applied_names": applied,
        "failed_names": failed,
        "errors": errors[:8],
        "detail": f"Applied {len(applied)} Railway env var name(s); failed {len(failed)}.",
    }


def _apply_vercel_env_vars(model: ProviderE2EJobModel, params: dict[str, Any], names: list[str]) -> dict[str, Any]:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter
    from aethos_core.providers.vercel.operations.mutations_api import upsert_env_var
    from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import resolve_env_var_from_secure_store

    credential_id = model.credential_id or str(params.get("credential_id") or "")
    token = VercelAuthAdapter().get_api_token(credential_id) if credential_id else None
    if not token:
        auth = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
        credential_id = str(auth.get("credential_id") or "")
        token = VercelAuthAdapter().get_api_token(credential_id) if credential_id else None
    if not token:
        return {"ok": False, "applied_names": [], "failed_names": names, "detail": "Vercel token unavailable."}

    plan = {
        "repo": str(params.get("referenced_github_repo") or ""),
        "project": model.project_name,
        "environment": model.environment,
        "provider": "vercel",
    }
    applied: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    for name in names:
        resolved = resolve_env_var_from_secure_store(name, plan=plan)
        if not resolved.ok or not resolved.value:
            failed.append(name)
            errors.append(resolved.blocked_reason or f"missing `{name}`")
            continue
        result = upsert_env_var(token, target_name=model.project_name, key=name, value=resolved.value)
        if result.get("ok"):
            applied.append(name)
        else:
            failed.append(name)
            errors.append(str(result.get("detail") or "upsert failed"))

    return {
        "ok": not failed,
        "applied_names": applied,
        "failed_names": failed,
        "skipped_names": skipped,
        "errors": errors[:8],
        "detail": f"Upserted {len(applied)} Vercel env key(s); failed {len(failed)}.",
    }
