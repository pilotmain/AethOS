# SPDX-License-Identifier: Apache-2.0
"""Railway environmentStageChanges (variables only) + commit (skipDeploys) for FIX 112."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import graphql_query
from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
    COMMIT_SKIP_DEPLOYS_ENFORCED,
    commit_staged_changes_skip_deploy,
)
from aethos_core.security.secret_redaction import redact_text

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

ENVIRONMENT_CONFIG_VARIABLES_QUERY = """
query EnvironmentConfigVariables($environmentId: String!) {
  environment(id: $environmentId) {
    id
    config
  }
}
"""

_FORBIDDEN_STAGE_KEYS = frozenset({"sharedVariables", "sharedvariables"})
_FORBIDDEN_SERVICE_KEYS = frozenset({"source"})


def _railway_variables_payload(variables: dict[str, str]) -> dict[str, Any]:
    return {str(key).strip().upper(): {"value": str(value)} for key, value in variables.items()}


def validate_stage_input_env_only(input_payload: dict[str, Any]) -> list[str]:
    """Ensure staged patch contains only per-service variables (no source, no shared env)."""
    errors: list[str] = []
    if not isinstance(input_payload, dict):
        return ["stage input must be an object"]
    for key in input_payload:
        if key.lower() in _FORBIDDEN_STAGE_KEYS:
            errors.append(f"forbidden staged key `{key}` (shared env writes not permitted in FIX 112)")
    services = input_payload.get("services")
    if not isinstance(services, dict):
        errors.append("stage input.services must be an object")
        return errors
    for service_id, service_cfg in services.items():
        if not isinstance(service_cfg, dict):
            errors.append(f"service `{service_id}` config must be an object")
            continue
        extra = set(service_cfg.keys()) - {"variables"}
        if extra:
            errors.append(
                f"service `{service_id}` may only include `variables` "
                f"(found: {', '.join(sorted(extra))})"
            )
        variables = service_cfg.get("variables")
        if not isinstance(variables, dict) or not variables:
            errors.append(f"service `{service_id}` requires non-empty variables object")
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


def read_service_env_var_names(
    token: str,
    *,
    environment_id: str,
    service_id: str,
) -> dict[str, Any]:
    """Read-only: env var names present on a service (never returns values)."""
    out = graphql_query(token, ENVIRONMENT_CONFIG_VARIABLES_QUERY, {"environmentId": environment_id})
    if not out.get("ok"):
        return {
            "ok": False,
            "names": [],
            "detail": _graphql_error_detail(out, fallback="environment config query failed"),
        }
    environment = (out.get("data") or {}).get("environment") or {}
    services = _extract_services_config(environment.get("config"))
    service_cfg = services.get(service_id) if isinstance(services, dict) else None
    if not isinstance(service_cfg, dict):
        return {
            "ok": True,
            "names": [],
            "detail": "no service config found for service_id in environment",
        }
    variables = service_cfg.get("variables")
    if not isinstance(variables, dict):
        return {"ok": True, "names": [], "detail": "no variables on service config"}
    names = sorted(str(key).strip() for key in variables if str(key).strip())
    return {
        "ok": True,
        "names": names,
        "detail": "env var names read from environment config (values not returned)",
    }


def stage_service_env_unset(
    token: str,
    *,
    environment_id: str,
    service_id: str,
    env_names: list[str],
) -> dict[str, Any]:
    """Stage removal of service-scoped variables (names only; values sent as null)."""
    names = [str(n).strip().upper() for n in env_names if str(n).strip()]
    if not names:
        return {"ok": False, "detail": "no env names provided for unset"}
    variables_payload = {name: None for name in names}
    input_payload = {
        "services": {
            service_id: {
                "variables": variables_payload,
            }
        }
    }
    validation_errors = validate_stage_input_env_only(input_payload)
    if validation_errors:
        return {"ok": False, "detail": "; ".join(validation_errors)}

    out = graphql_query(
        token,
        STAGE_ENVIRONMENT_CHANGES_MUTATION,
        {
            "environmentId": environment_id,
            "merge": True,
            "input": input_payload,
        },
    )
    if not out.get("ok"):
        return {"ok": False, "detail": _graphql_error_detail(out, fallback="environmentStageChanges unset failed")}
    staged = ((out.get("data") or {}).get("environmentStageChanges")) or {}
    return {
        "ok": True,
        "detail": "environmentStageChanges unset staged (variables only)",
        "staged_change_id": str(staged.get("id") or ""),
        "variable_count": len(names),
        "env_names_unset": names,
        "skip_deploys_enforced": COMMIT_SKIP_DEPLOYS_ENFORCED,
    }


def stage_service_env_variables(
    token: str,
    *,
    environment_id: str,
    service_id: str,
    variables: dict[str, str],
) -> dict[str, Any]:
    """Stage service-scoped variables only (no deploy until commit with skipDeploys)."""
    input_payload = {
        "services": {
            service_id: {
                "variables": _railway_variables_payload(dict(variables)),
            }
        }
    }
    validation_errors = validate_stage_input_env_only(input_payload)
    if validation_errors:
        return {"ok": False, "detail": "; ".join(validation_errors)}

    variables_out = {
        "environmentId": environment_id,
        "merge": True,
        "input": input_payload,
    }
    out = graphql_query(token, STAGE_ENVIRONMENT_CHANGES_MUTATION, variables_out)
    if not out.get("ok"):
        return {"ok": False, "detail": _graphql_error_detail(out, fallback="environmentStageChanges failed")}
    staged = ((out.get("data") or {}).get("environmentStageChanges")) or {}
    return {
        "ok": True,
        "detail": "environmentStageChanges succeeded (variables only)",
        "staged_change_id": str(staged.get("id") or ""),
        "variable_count": len(variables),
        "skip_deploys_enforced": COMMIT_SKIP_DEPLOYS_ENFORCED,
    }


def commit_staged_env_changes_skip_deploy(
    token: str,
    *,
    environment_id: str,
    commit_message: str,
) -> dict[str, Any]:
    """Commit staged env changes without triggering deployment."""
    return commit_staged_changes_skip_deploy(
        token,
        environment_id=environment_id,
        commit_message=commit_message,
    )
