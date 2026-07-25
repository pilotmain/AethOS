# SPDX-License-Identifier: Apache-2.0
"""Readonly Railway deployment readiness checks."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.config import get_settings
from aethos_core.provider_topology.operation_requirement_policy import requires_source_binding
from aethos_core.security.secret_redaction import redact_text

_FOR_REPO_RX = re.compile(
    r"\b(?:for|from|repo(?:sitory)?|using|target(?:ing)?)\s+([a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]+)\b",
    re.I,
)

_CANONICAL_CREDENTIAL_SOURCE = "canonical provider credential resolver"


def extract_github_repo_target(text: str) -> str | None:
    """Extract `owner/repo` from prompts like readiness for pilotmain/aethos."""
    raw = (text or "").strip()
    if not raw:
        return None
    match = _FOR_REPO_RX.search(raw)
    if match:
        return match.group(1).strip()
    from aethos_core.provider_topology.provider_relationships import extract_github_repo_references

    refs = extract_github_repo_references(raw)
    return refs[0].strip() if refs else None


def _github_repo_from_text(text: str) -> str | None:
    return extract_github_repo_target(text)


def _resolve_railway_token_canonical() -> tuple[str | None, str, str]:
    """Resolve Railway token via canonical credential truth path."""
    from aethos_core.providers.railway.credential_truth import (
        credential_source_label,
        resolve_railway_credential,
    )

    resolved = resolve_railway_credential()
    if resolved.ok and resolved.token:
        return (
            resolved.token,
            credential_source_label(resolved.source),
            "ok",
        )
    return None, "canonical railway credential resolver", resolved.detail or "missing Railway API token"


def _probe_github_binding(*, referenced_repo: str | None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "github_credential_ok": False,
        "accessible_repos_count": 0,
        "referenced_repo": referenced_repo or "",
        "referenced_repo_accessible": None,
        "binding_required_for_deploy": True,
        "detail": "",
    }
    try:
        from aethos_core.connections.credential_runtime_gate import check_provider_credential_gate

        gate = check_provider_credential_gate("github", require_validated=True)
        out["github_credential_ok"] = bool(gate.get("ok"))
        if not gate.get("ok"):
            out["detail"] = str(gate.get("detail") or "GitHub credential not validated.")
            return out

        from aethos_core.provider_topology.binding_verifier import _accessible_github_repos

        repos = _accessible_github_repos() or []
        out["accessible_repos_count"] = len(repos)
        if referenced_repo and repos:
            out["referenced_repo_accessible"] = referenced_repo.lower() in {r.lower() for r in repos}
        elif referenced_repo:
            out["referenced_repo_accessible"] = None
            out["detail"] = "Could not list GitHub repos to verify binding."
        else:
            out["detail"] = f"GitHub token can access {len(repos)} repository(ies)."
    except Exception as exc:
        out["detail"] = f"GitHub binding probe failed: {exc}"
    return out


def safe_run_deployment_readiness_checks(
    *,
    user_text: str = "",
    session_id: str = "default",
) -> dict[str, Any]:
    """Run readiness checks without raising."""
    try:
        return run_deployment_readiness_checks(user_text=user_text, session_id=session_id)
    except Exception as exc:
        checks = _minimal_failed_checks(user_text=user_text, error=str(exc))
        checks["check_error"] = str(exc)
        return checks


def _minimal_failed_checks(*, user_text: str, error: str) -> dict[str, Any]:
    repo = extract_github_repo_target(user_text)
    return {
        "execution_mode": "api",
        "referenced_github_repo": repo or "",
        "railway_credential_ok": False,
        "railway_credential_source": _CANONICAL_CREDENTIAL_SOURCE,
        "railway_api_connection_ok": False,
        "railway_credential_detail": error,
        "inventory": {"ok": False, "error": error, "project_count": 0},
        "github_binding": {"github_credential_ok": False, "accessible_repos_count": 0, "detail": error},
        "service_creation": {"graphql_service_create": False},
        "required_env_vars": ["RAILWAY_API_TOKEN (validated Railway API token)"],
        "readonly_readiness_ok": False,
        "mutation_ready": False,
    }


def _soft_pass_rate_limited_connection(
    checks: dict[str, Any],
    inventory_summary: dict[str, Any],
) -> None:
    """A transient Railway rate-limit must never block a token we have prior proof for.

    Mirrors providers/cloud/validators.py: a clean auth rejection (401/403) fails, but a
    429/throttle accepts the stored key. When the live ProjectsAndServices probe is
    rate-limited yet the credential is validated in the vault OR cached inventory is
    available, we mark the connection healthy so greenfield deployment can proceed.
    """
    if checks.get("railway_api_connection_ok"):
        return
    if not checks.get("railway_credential_ok"):
        return

    detail = str(checks.get("railway_api_connection_detail") or "")
    status_code = checks.get("railway_api_connection_status_code")
    from aethos_core.provider_e2e_readiness.blocker_mapping import is_rate_limited_detail

    if not (checks.get("railway_api_connection_rate_limited") or is_rate_limited_detail(detail, status_code=status_code)):
        return

    credential_validated = str(checks.get("railway_credential_source") or "") in {
        "Validated Vault Credential",
        "validated_vault",
        "Explicit Vault Credential",
        "explicit_credential",
    }
    try:
        from aethos_core.connections.credential_runtime_gate import check_provider_credential_gate

        if not credential_validated:
            credential_validated = bool(check_provider_credential_gate("railway", require_validated=True).get("ok"))
    except Exception:
        pass

    cached_inventory_ok = bool(inventory_summary.get("ok")) and (
        inventory_summary.get("project_count")
        or str(inventory_summary.get("freshness") or "") in {"cache", "stale"}
        or inventory_summary.get("stale_cache")
    )

    if not (credential_validated or cached_inventory_ok):
        return

    checks["railway_api_connection_ok"] = True
    checks["railway_api_connection_soft_passed"] = True
    checks["railway_api_connection_soft_pass_reason"] = "rate_limited"
    checks["railway_api_connection_detail"] = (
        "Railway API is rate-limiting the live probe (transient). Credential is already trusted "
        f"({'validated vault credential' if credential_validated else 'recent cached inventory'}), "
        f"so deployment readiness is not blocked. Probe detail: {detail[:160]}"
    )


def run_deployment_readiness_checks(
    *,
    user_text: str = "",
    session_id: str = "default",
) -> dict[str, Any]:
    """Run readonly readiness checks (no mutations)."""
    _ = session_id
    settings = get_settings()
    execution_mode = (settings.railway_execution_mode or "api").strip().lower()
    referenced_repo = _github_repo_from_text(user_text)

    checks: dict[str, Any] = {
        "execution_mode": execution_mode if execution_mode in {"api", "cli"} else "api",
        "canonical_env_var": "RAILWAY_API_TOKEN",
        "required_env_vars": [
            "RAILWAY_API_TOKEN (validated Railway API token)",
            "Optional: RAILWAY_PROJECT_ID / RAILWAY_ENVIRONMENT_ID for default targeting",
            "GitHub credential (Mission Control) when deploy requires source binding",
            "Repository env vars for the new service (set after service exists — not enabled yet)",
        ],
        "referenced_github_repo": referenced_repo or "",
        "binding_required_for_new_deploy": requires_source_binding(
            "railway", "deploy_from_git", execution_mode="deploy_from_source"
        ),
    }

    token, cred_source, cred_detail = _resolve_railway_token_canonical()

    checks["railway_credential_ok"] = bool(token)
    checks["railway_credential_source"] = cred_source
    checks["railway_credential_detail"] = cred_detail if token else cred_detail or "missing Railway API token"

    from aethos_core.providers.railway.credential_truth import (
        RAILWAY_VALIDATION_PROBE,
        checks_credential_metadata,
        resolve_railway_credential,
        validate_railway_api_connection,
    )

    resolution = resolve_railway_credential()
    checks.update(checks_credential_metadata(resolution, None))
    checks["railway_validation_probe"] = RAILWAY_VALIDATION_PROBE

    if token:
        validation = validate_railway_api_connection(token)
        checks.update(validation.to_checks_fields())
        checks.update(checks_credential_metadata(resolution, validation))
        checks["railway_account_email"] = None
    else:
        checks["railway_api_connection_ok"] = False
        checks["railway_account_email"] = None
        checks["railway_api_connection_detail"] = cred_detail or "No Railway token resolved."

    inventory_summary: dict[str, Any] = {
        "ok": False,
        "project_count": 0,
        "environment_count": 0,
        "service_count": 0,
        "projects": [],
        "error": "",
    }
    if token:
        try:
            from aethos_core.providers.railway.discovery import safe_discover_railway_inventory

            inventory = safe_discover_railway_inventory()
            inventory_summary["ok"] = not inventory.error
            if inventory.freshness == "empty" and not inventory.projects:
                inventory_summary["ok"] = True
            inventory_summary["error"] = str(inventory.error or "")
            inventory_summary["freshness"] = inventory.freshness
            inventory_summary["inventory_probe"] = str(
                (inventory.evidence or {}).get("inventory_probe") or "ProjectsEnvironmentsServices"
            )
            inventory_summary["inventory_probe_status"] = str(
                (inventory.evidence or {}).get("inventory_probe_status")
                or ("pass" if inventory_summary["ok"] else "fail")
            )
            inventory_summary["validation_probe"] = checks.get("railway_validation_probe") or "ProjectsAndServices"
            inventory_summary["validation_probe_status"] = (
                "pass" if checks.get("railway_api_connection_ok") else "fail"
            )
            inventory_summary["credential_source"] = checks.get("railway_credential_source_label") or checks.get(
                "railway_credential_source"
            )
            projects_out: list[dict[str, Any]] = []
            env_count = 0
            svc_count = 0
            for project in inventory.projects[:8]:
                envs = []
                for env in project.environments[:6]:
                    env_count += 1
                    services = [svc.name for svc in env.services[:12]]
                    svc_count += len(env.services)
                    envs.append({"id": env.id, "name": env.name, "services": services})
                projects_out.append({"id": project.id, "name": project.name, "environments": envs})
            inventory_summary["project_count"] = len(inventory.projects)
            inventory_summary["environment_count"] = env_count
            inventory_summary["service_count"] = svc_count
            inventory_summary["projects"] = projects_out
            if inventory.error and not inventory.projects:
                inventory_summary["ok"] = False
        except Exception as exc:
            inventory_summary["error"] = redact_text(str(exc))[:240]
            inventory_summary["inventory_probe_status"] = "fail"

    checks["inventory"] = inventory_summary

    _soft_pass_rate_limited_connection(checks, inventory_summary)

    checks["github_binding"] = _probe_github_binding(referenced_repo=referenced_repo)

    checks["service_creation"] = {
        "graphql_service_create": False,
        "graphql_service_create_detail": (
            "No `serviceCreate` / greenfield provision mutation is wired in AethOS Railway API client yet."
        ),
        "governed_mutation_adapter_ops": ["restart", "redeploy"],
        "env_var_writes_enabled": get_settings().provider_env_var_mutations_enabled,
        "cli_railway_up_available": execution_mode == "cli",
        "cli_note": (
            "CLI mode can invoke Railway tooling for linked projects, but governed new-service creation "
            "is not certified in this runtime."
        ),
    }

    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        readiness_check_statuses,
    )

    checks["readonly_readiness_ok"] = all(readiness_check_statuses(checks).values())
    checks["mutation_ready"] = False
    checks["mutation_blockers"] = [
        "Greenfield Railway service creation is not implemented in governed mutation layer.",
        "Env var writes are disabled (`set_env_var` capability off).",
        "Explicit approval is required before any future create/connect/deploy mutation steps.",
    ]

    return checks
