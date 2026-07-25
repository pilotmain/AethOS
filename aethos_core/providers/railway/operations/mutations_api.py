# SPDX-License-Identifier: Apache-2.0
"""Railway governed mutations — restart and redeploy."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.api_client import (
    find_service_by_name,
    graphql_query,
    list_service_deployments,
)
from aethos_core.security.secret_redaction import redact_text

PROJECT_ENVIRONMENTS_QUERY = """
query ProjectEnvironments($projectId: String!) {
  project(id: $projectId) {
    environments {
      edges {
        node {
          id
          name
        }
      }
    }
  }
}
"""

DEPLOYMENT_RESTART_MUTATION = """
mutation deploymentRestart($id: String!) {
  deploymentRestart(id: $id)
}
"""

DEPLOYMENT_STOP_MUTATION = """
mutation deploymentStop($id: String!) {
  deploymentStop(id: $id)
}
"""

SERVICE_INSTANCE_REDEPLOY_MUTATION = """
mutation serviceInstanceRedeploy($environmentId: String!, $serviceId: String!) {
  serviceInstanceRedeploy(environmentId: $environmentId, serviceId: $serviceId)
}
"""


def _resolve_environment_id(token: str, *, project_id: str) -> str | None:
    resolved = resolve_environment_id(token, project_id=project_id)
    if not resolved:
        return None
    return resolved.get("environment_id")


def resolve_environment_id(
    token: str,
    *,
    project_id: str,
    preferred_name: str = "production",
) -> dict[str, str] | None:
    """Return {environment_id, environment_name} for a project."""
    from aethos_core.config import get_settings

    settings = get_settings()
    override = str(settings.railway_environment_id or "").strip()
    if override:
        return {"environment_id": override, "environment_name": preferred_name or "production"}

    out = graphql_query(token, PROJECT_ENVIRONMENTS_QUERY, {"projectId": project_id})
    if not out.get("ok"):
        return None
    edges = (((out.get("data") or {}).get("project") or {}).get("environments") or {}).get("edges") or []
    envs: list[dict[str, str]] = []
    for edge in edges:
        node = edge.get("node") if isinstance(edge, dict) else {}
        if isinstance(node, dict):
            envs.append({"id": str(node.get("id") or ""), "name": str(node.get("name") or "")})
    preferred = (preferred_name or "production").strip().lower()
    for env in envs:
        if env["name"].lower() == preferred:
            return {"environment_id": env["id"], "environment_name": env["name"]}
    if envs:
        return {"environment_id": envs[0]["id"], "environment_name": envs[0]["name"]}
    return None


def _graphql_mutation_confirmed(mutation_data: dict[str, Any], response_key: str) -> bool:
    value = mutation_data.get(response_key)
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return bool(value.strip())
    return True


def submit_service_instance_redeploy(
    token: str,
    *,
    environment_id: str,
    service_id: str,
) -> dict[str, Any]:
    out = graphql_query(
        token,
        SERVICE_INSTANCE_REDEPLOY_MUTATION,
        {"environmentId": environment_id, "serviceId": service_id},
    )
    mutation_data = out.get("data") if isinstance(out.get("data"), dict) else {}
    command_submitted = bool(out.get("ok")) and _graphql_mutation_confirmed(mutation_data, "serviceInstanceRedeploy")
    provider_request_id = str(mutation_data.get("serviceInstanceRedeploy") or service_id)
    return {
        "ok": command_submitted,
        "graphql_ok": bool(out.get("ok")),
        "restart_command_submitted": command_submitted,
        "graphql_operation": "serviceInstanceRedeploy",
        "mutation_variables": {"environmentId": environment_id, "serviceId": service_id},
        "provider_request_id": provider_request_id if command_submitted else None,
        "railway_response": mutation_data,
        "graphql_errors": out.get("errors"),
        "detail": (
            f"serviceInstanceRedeploy submitted for service `{service_id}` in environment `{environment_id}`."
            if command_submitted
            else redact_text(str(((out.get("errors") or [{}])[0] or {}).get("message", "serviceInstanceRedeploy not confirmed")))
        ),
    }


def submit_deployment_restart(token: str, *, deployment_id: str) -> dict[str, Any]:
    out = graphql_query(token, DEPLOYMENT_RESTART_MUTATION, {"id": deployment_id})
    mutation_data = out.get("data") if isinstance(out.get("data"), dict) else {}
    command_submitted = bool(out.get("ok")) and _graphql_mutation_confirmed(mutation_data, "deploymentRestart")
    provider_request_id = str(mutation_data.get("deploymentRestart") or deployment_id)
    return {
        "ok": command_submitted,
        "graphql_ok": bool(out.get("ok")),
        "restart_command_submitted": command_submitted,
        "graphql_operation": "deploymentRestart",
        "mutation_variables": {"id": deployment_id},
        "provider_request_id": provider_request_id if command_submitted else None,
        "deployment_id": deployment_id,
        "railway_response": mutation_data,
        "graphql_errors": out.get("errors"),
        "detail": (
            f"deploymentRestart submitted for deployment `{deployment_id}`."
            if command_submitted
            else redact_text(str(((out.get("errors") or [{}])[0] or {}).get("message", "deploymentRestart not confirmed")))
        ),
    }


def _resolve_service(token: str, *, target_name: str) -> dict[str, Any] | None:
    svc = find_service_by_name(token, target_name)
    if not svc:
        return None
    return svc


def restart_service(token: str, *, target_name: str) -> dict[str, Any]:
    svc = _resolve_service(token, target_name=target_name)
    if not svc:
        return {"ok": False, "detail": f"Railway service `{target_name}` not found."}
    service_id = str(svc.get("service_id") or "")
    deployments = list_service_deployments(token, service_id=service_id, limit=5)
    if not deployments:
        return {"ok": False, "detail": "No deployments found to restart."}
    deployment_id = str(deployments[0].get("id") or "")
    deployment_state = str(deployments[0].get("state") or "unknown")
    deployment_created_at = deployments[0].get("created_at")
    if not deployment_id:
        return {"ok": False, "detail": "Latest deployment id unavailable."}
    deployment_state_before = deployment_state
    restart_timestamp = None
    out = graphql_query(token, DEPLOYMENT_RESTART_MUTATION, {"id": deployment_id})
    if not out.get("ok"):
        err = ((out.get("errors") or [{}])[0] or {}).get("message", "restart failed")
        return {
            "ok": False,
            "detail": redact_text(str(err)),
            "deployment_id": deployment_id,
            "failure_type": "provider_auth_failure" if "auth" in str(err).lower() else "mutation_failed",
        }
    from time import time

    restart_timestamp = time()
    mutation_data = out.get("data") if isinstance(out.get("data"), dict) else {}
    after_deployments = list_service_deployments(token, service_id=service_id, limit=3)
    deployment_state_after = deployment_state_before
    if after_deployments:
        deployment_state_after = str(after_deployments[0].get("state") or deployment_state_before)
    return {
        "ok": True,
        "detail": f"Restart triggered for deployment `{deployment_id}`.",
        "service_id": service_id,
        "service_name": svc.get("service_name"),
        "deployment_id": deployment_id,
        "deployment_or_restart_id": deployment_id,
        "deployment_state": deployment_state_after,
        "deployment_state_before": deployment_state_before,
        "deployment_state_after": deployment_state_after,
        "deployment_created_at": deployment_created_at,
        "restart_timestamp": restart_timestamp,
        "restart_requested_at": restart_timestamp,
        "operation": "restart",
        "graphql_operation": "deploymentRestart",
        "http_status": 200,
        "railway_response": mutation_data,
        "evidence": {
            "provider": "railway",
            "operation": "restart",
            "executed": True,
            "service_name": svc.get("service_name"),
            "deployment_id": deployment_id,
            "deployment_or_restart_id": deployment_id,
            "deployment_state_before": deployment_state_before,
            "deployment_state_after": deployment_state_after,
            "restart_timestamp": restart_timestamp,
            "restart_requested_at": restart_timestamp,
            "graphql_operation": "deploymentRestart",
            "http_status": 200,
        },
        "rollback_metadata": {
            "deployment_id": deployment_id,
            "deployment_state_before": deployment_state_before,
            "deployment_state_after": deployment_state_after,
            "restart_timestamp": restart_timestamp,
            "recovery_guidance": [
                "Redeploy prior deployment if service remains unhealthy",
                "Inspect Railway deployment logs and failed deployment history",
                "Inspect readonly list_deployments verification evidence",
            ],
        },
    }


def stop_service(token: str, *, target_name: str) -> dict[str, Any]:
    """Stop the active Railway deployment without deleting the service."""
    svc = _resolve_service(token, target_name=target_name)
    if not svc:
        return {"ok": False, "detail": f"Railway service `{target_name}` not found."}
    service_id = str(svc.get("service_id") or "")
    deployments = list_service_deployments(token, service_id=service_id, limit=5)
    if not deployments:
        return {"ok": False, "detail": "No deployments found to stop."}
    deployment_id = str(deployments[0].get("id") or "")
    deployment_state_before = str(deployments[0].get("state") or "unknown")
    if not deployment_id:
        return {"ok": False, "detail": "Latest deployment id unavailable."}
    out = graphql_query(token, DEPLOYMENT_STOP_MUTATION, {"id": deployment_id})
    if not out.get("ok"):
        err = ((out.get("errors") or [{}])[0] or {}).get("message", "stop failed")
        return {
            "ok": False,
            "detail": redact_text(str(err)),
            "deployment_id": deployment_id,
            "failure_type": "provider_auth_failure" if "auth" in str(err).lower() else "mutation_failed",
        }
    mutation_data = out.get("data") if isinstance(out.get("data"), dict) else {}
    stop_confirmed = _graphql_mutation_confirmed(mutation_data, "deploymentStop")
    after_deployments = list_service_deployments(token, service_id=service_id, limit=3)
    deployment_state_after = deployment_state_before
    if after_deployments:
        deployment_state_after = str(after_deployments[0].get("state") or deployment_state_before)
    return {
        "ok": stop_confirmed,
        "detail": (
            f"Stop submitted for deployment `{deployment_id}`."
            if stop_confirmed
            else "Railway stop mutation did not confirm."
        ),
        "service_id": service_id,
        "service_name": svc.get("service_name"),
        "deployment_id": deployment_id,
        "deployment_state_before": deployment_state_before,
        "deployment_state_after": deployment_state_after,
        "operation": "stop",
        "graphql_operation": "deploymentStop",
        "stop_command_submitted": stop_confirmed,
        "evidence": {
            "provider": "railway",
            "operation": "stop",
            "executed": stop_confirmed,
            "service_name": svc.get("service_name"),
            "deployment_id": deployment_id,
            "graphql_operation": "deploymentStop",
        },
        "rollback_metadata": {
            "deployment_id": deployment_id,
            "recovery_guidance": [
                "Use governed restart or redeploy to bring the service back online",
                "Inspect Railway deployment history if stop state is unexpected",
            ],
        },
    }


def redeploy_service(
    token: str,
    *,
    target_name: str,
    environment_name: str = "production",
    service_id: str | None = None,
) -> dict[str, Any]:
    svc = _resolve_service(token, target_name=target_name)
    if not svc:
        return {"ok": False, "detail": f"Railway service `{target_name}` not found."}
    service_id = str(service_id or svc.get("service_id") or "")
    project_id = str(svc.get("project_id") or "")
    resolved_env = resolve_environment_id(
        token,
        project_id=project_id,
        preferred_name=environment_name or "production",
    )
    environment_id = resolved_env.get("environment_id") if resolved_env else None
    if not environment_id:
        return {"ok": False, "detail": "Could not resolve Railway environment id."}
    submitted = submit_service_instance_redeploy(token, environment_id=environment_id, service_id=service_id)
    if not submitted.get("ok"):
        return {
            "ok": False,
            "detail": submitted.get("detail") or "Redeploy failed.",
            "failure_type": "mutation_failed",
            "restart_command_submitted": False,
        }
    return {
        "ok": True,
        "detail": f"Redeploy triggered for `{svc.get('service_name')}` in environment `{environment_id}`.",
        "service_id": service_id,
        "service_name": svc.get("service_name"),
        "project_id": project_id,
        "environment_id": environment_id,
        "environment_name": resolved_env.get("environment_name") if resolved_env else environment_name,
        "operation": "redeploy",
        "graphql_operation": "serviceInstanceRedeploy",
        "restart_command_submitted": True,
        "provider_request_id": submitted.get("provider_request_id"),
        "railway_response": submitted.get("railway_response"),
    }
