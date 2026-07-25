# SPDX-License-Identifier: Apache-2.0
"""Railway environmentStageChanges + commit (skipDeploys) for GitHub source binding."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import graphql_query
from aethos_core.security.secret_redaction import redact_text

# FIX 109B — commit path must never trigger deploy during source binding.
COMMIT_SKIP_DEPLOYS_ENFORCED: bool = True

STAGE_ENVIRONMENT_CHANGES_MUTATION = """
mutation stageEnvironmentChanges(
  $environmentId: String!
  $input: EnvironmentConfig!
  $merge: Boolean
) {
  environmentStageChanges(environmentId: $environmentId, input: $input, merge: $merge) {
    id
  }
}
"""

COMMIT_STAGED_SKIP_DEPLOY_MUTATION = """
mutation environmentPatchCommitStaged(
  $environmentId: String!
  $commitMessage: String
  $skipDeploys: Boolean
) {
  environmentPatchCommitStaged(
    environmentId: $environmentId
    commitMessage: $commitMessage
    skipDeploys: $skipDeploys
  )
}
"""

ENVIRONMENT_CONFIG_SOURCE_QUERY = """
query EnvironmentConfigSource($environmentId: String!) {
  environment(id: $environmentId) {
    id
    config
  }
}
"""

_FORBIDDEN_STAGE_KEYS = frozenset({"variables", "sharedVariables", "sharedvariables"})


def validate_stage_input_source_disconnect_only(input_payload: dict[str, Any]) -> list[str]:
    """Ensure staged disconnect patch clears source only (no env writes)."""
    errors: list[str] = []
    if not isinstance(input_payload, dict):
        return ["stage input must be an object"]
    for key in input_payload:
        if key.lower() in _FORBIDDEN_STAGE_KEYS:
            errors.append(f"forbidden staged key `{key}` (env writes not permitted in FIX 111)")
    services = input_payload.get("services")
    if not isinstance(services, dict):
        errors.append("stage input.services must be an object")
        return errors
    for service_id, service_cfg in services.items():
        if not isinstance(service_cfg, dict):
            errors.append(f"service `{service_id}` config must be an object")
            continue
        extra = set(service_cfg.keys()) - {"source"}
        if extra:
            errors.append(
                f"service `{service_id}` may only include `source` (found: {', '.join(sorted(extra))})"
            )
        if "source" not in service_cfg:
            errors.append(f"service `{service_id}` requires source key for disconnect")
            continue
        source = service_cfg.get("source")
        if source is not None and source != {}:
            if isinstance(source, dict) and (source.get("repo") or source.get("branch")):
                errors.append(
                    f"service `{service_id}` disconnect source must be empty/null, not a repo binding"
                )
            elif not isinstance(source, dict):
                errors.append(f"service `{service_id}` disconnect source must be null or {{}}")
    return errors


def validate_stage_input_source_only(input_payload: dict[str, Any]) -> list[str]:
    """Ensure staged environment patch contains only per-service source fields."""
    errors: list[str] = []
    if not isinstance(input_payload, dict):
        return ["stage input must be an object"]
    for key in input_payload:
        if key.lower() in _FORBIDDEN_STAGE_KEYS:
            errors.append(f"forbidden staged key `{key}` (env writes not permitted in FIX 109)")
    services = input_payload.get("services")
    if not isinstance(services, dict):
        errors.append("stage input.services must be an object")
        return errors
    for service_id, service_cfg in services.items():
        if not isinstance(service_cfg, dict):
            errors.append(f"service `{service_id}` config must be an object")
            continue
        extra = set(service_cfg.keys()) - {"source"}
        if extra:
            errors.append(
                f"service `{service_id}` may only include `source` (found: {', '.join(sorted(extra))})"
            )
        source = service_cfg.get("source")
        if not isinstance(source, dict):
            errors.append(f"service `{service_id}` requires source object")
            continue
        source_extra = set(source.keys()) - {"repo", "branch", "rootDirectory"}
        if source_extra:
            errors.append(
                f"service `{service_id}` source may only include repo/branch/rootDirectory "
                f"(found: {', '.join(sorted(source_extra))})"
            )
    return errors


def _graphql_error_detail(out: dict[str, Any], *, fallback: str) -> str:
    errors = out.get("errors") or []
    if errors:
        return "; ".join(redact_text(str(item.get("message") or item)) for item in errors if item)
    return fallback


def _extract_services_config(config_raw: Any) -> dict[str, Any]:
    if isinstance(config_raw, dict):
        services = config_raw.get("services")
        return services if isinstance(services, dict) else {}
    return {}


def read_service_source_binding(
    token: str,
    *,
    environment_id: str,
    service_id: str,
) -> dict[str, Any]:
    """Read-only: resolve repo/branch bound to a service in an environment."""
    out = graphql_query(token, ENVIRONMENT_CONFIG_SOURCE_QUERY, {"environmentId": environment_id})
    if not out.get("ok"):
        return {
            "ok": False,
            "detail": _graphql_error_detail(out, fallback="environment config query failed"),
        }
    environment = (out.get("data") or {}).get("environment") or {}
    services = _extract_services_config(environment.get("config"))
    service_cfg = services.get(service_id) if isinstance(services, dict) else None
    if not isinstance(service_cfg, dict):
        return {
            "ok": True,
            "bound": False,
            "repository": "",
            "branch": "",
            "detail": "no service config found for service_id in environment",
        }
    source = service_cfg.get("source") if isinstance(service_cfg.get("source"), dict) else {}
    repo = str(source.get("repo") or "").strip()
    branch = str(source.get("branch") or "").strip()
    return {
        "ok": True,
        "bound": bool(repo),
        "repository": repo,
        "branch": branch or "main",
        "detail": "source binding read from environment config",
    }


def stage_github_source_binding(
    token: str,
    *,
    environment_id: str,
    service_id: str,
    repo: str,
    branch: str,
    root_directory: str = "",
) -> dict[str, Any]:
    """Stage GitHub repo source on a service (no env writes, no deploy)."""
    source: dict[str, str] = {"repo": repo, "branch": branch}
    root = (root_directory or "").strip().strip("/")
    if root:
        source["rootDirectory"] = root
    input_payload = {
        "services": {
            service_id: {
                "source": source,
            }
        }
    }
    validation_errors = validate_stage_input_source_only(input_payload)
    if validation_errors:
        return {"ok": False, "detail": "; ".join(validation_errors)}

    variables = {
        "environmentId": environment_id,
        "merge": True,
        "input": input_payload,
    }
    out = graphql_query(token, STAGE_ENVIRONMENT_CHANGES_MUTATION, variables)
    if not out.get("ok"):
        return {"ok": False, "detail": _graphql_error_detail(out, fallback="environmentStageChanges failed")}
    staged = ((out.get("data") or {}).get("environmentStageChanges")) or {}
    return {
        "ok": True,
        "detail": "environmentStageChanges succeeded (source only)",
        "staged_change_id": str(staged.get("id") or ""),
        "skip_deploys_enforced": COMMIT_SKIP_DEPLOYS_ENFORCED,
    }


def stage_github_source_disconnect(
    token: str,
    *,
    environment_id: str,
    service_id: str,
) -> dict[str, Any]:
    """Stage removal of GitHub repo source on a service (no env writes, no deploy)."""
    input_payload: dict[str, Any] = {
        "services": {
            service_id: {
                "source": None,
            }
        }
    }
    validation_errors = validate_stage_input_source_disconnect_only(input_payload)
    if validation_errors:
        return {"ok": False, "detail": "; ".join(validation_errors)}

    variables = {
        "environmentId": environment_id,
        "merge": True,
        "input": input_payload,
    }
    out = graphql_query(token, STAGE_ENVIRONMENT_CHANGES_MUTATION, variables)
    if not out.get("ok"):
        return {"ok": False, "detail": _graphql_error_detail(out, fallback="environmentStageChanges failed")}
    staged = ((out.get("data") or {}).get("environmentStageChanges")) or {}
    return {
        "ok": True,
        "detail": "environmentStageChanges succeeded (source cleared)",
        "staged_change_id": str(staged.get("id") or ""),
        "skip_deploys_enforced": COMMIT_SKIP_DEPLOYS_ENFORCED,
    }


def commit_staged_changes_skip_deploy(
    token: str,
    *,
    environment_id: str,
    commit_message: str = "AethOS governed GitHub source binding (FIX 109)",
) -> dict[str, Any]:
    """Commit staged environment changes without triggering a deployment."""
    if not COMMIT_SKIP_DEPLOYS_ENFORCED:
        return {"ok": False, "detail": "skipDeploys enforcement disabled — commit blocked"}

    skip_deploys = True
    variables = {
        "environmentId": environment_id,
        "commitMessage": commit_message,
        "skipDeploys": skip_deploys,
    }
    out = graphql_query(token, COMMIT_STAGED_SKIP_DEPLOY_MUTATION, variables)
    if not out.get("ok"):
        return {
            "ok": False,
            "detail": _graphql_error_detail(out, fallback="environmentPatchCommitStaged failed"),
            "skip_deploys": skip_deploys,
        }
    return {
        "ok": True,
        "detail": "environmentPatchCommitStaged succeeded (skipDeploys=true)",
        "skip_deploys": skip_deploys,
        "skip_deploys_enforced": COMMIT_SKIP_DEPLOYS_ENFORCED,
    }
