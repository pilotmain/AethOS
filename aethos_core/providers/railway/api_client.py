# SPDX-License-Identifier: Apache-2.0
"""Railway GraphQL API client."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from aethos_core.security.secret_redaction import redact_text

_log = logging.getLogger(__name__)

RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"

PROJECTS_SERVICES_QUERY = """
query ProjectsAndServices {
  projects {
    edges {
      node {
        id
        name
        services {
          edges {
            node {
              id
              name
            }
          }
        }
      }
    }
  }
}
"""

SERVICE_DEPLOYMENTS_QUERY = """
query ServiceDeployments($serviceId: String!, $first: Int!) {
  service(id: $serviceId) {
    id
    name
    projectId
    deployments(first: $first) {
      edges {
        node {
          id
          status
          createdAt
          url
          meta
        }
      }
    }
  }
}
"""

SERVICE_LOGS_QUERY = """
query DeploymentLogs($deploymentId: String!) {
  deploymentLogs(deploymentId: $deploymentId, limit: 200) {
    message
    timestamp
  }
}
"""


def graphql_query(token: str, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    if not token.strip():
        return {"ok": False, "errors": [{"message": "missing token"}]}
    headers = {"Authorization": f"Bearer {token.strip()}"}
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables
    try:
        with httpx.Client(timeout=25.0) as client:
            r = client.post(RAILWAY_GRAPHQL_URL, json=payload, headers=headers)
        if r.status_code >= 400:
            return {
                "ok": False,
                "status_code": r.status_code,
                "errors": [{"message": redact_text(r.text[:200])}],
            }
        if not r.content:
            return {
                "ok": False,
                "status_code": r.status_code,
                "errors": [{"message": "Railway API returned an empty response."}],
            }
        try:
            data = r.json()
        except ValueError:
            snippet = redact_text(r.text[:200]) if r.text else "(empty body)"
            return {
                "ok": False,
                "status_code": r.status_code,
                "errors": [{"message": f"Railway API returned non-JSON response: {snippet}"}],
            }
        if data.get("errors"):
            return {"ok": False, "status_code": r.status_code, "errors": data.get("errors"), "data": data.get("data")}
        return {"ok": True, "status_code": r.status_code, "data": data.get("data") or {}}
    except httpx.HTTPError as exc:
        return {"ok": False, "status_code": None, "errors": [{"message": redact_text(str(exc))}]}


def test_connection(token: str) -> dict[str, object]:
    out = graphql_query(token, "query { me { id email } }")
    if not out.get("ok"):
        err = ((out.get("errors") or [{}])[0] or {}).get("message", "Railway auth failed")
        return {"ok": False, "detail": redact_text(str(err))}
    me = (out.get("data") or {}).get("me") or {}
    email = str(me.get("email") or "")
    return {
        "ok": True,
        "detail": f"Railway account verified{f' ({email})' if email else ''}.",
        "account_email": email or None,
    }


def _normalize(name: str) -> str:
    return (name or "").strip().lower().replace("_", "-")


def list_services(token: str) -> list[dict[str, Any]]:
    result = list_services_with_status(token)
    if not result.get("ok"):
        return []
    services = result.get("services")
    return services if isinstance(services, list) else []


def list_services_with_status(token: str) -> dict[str, Any]:
    out = graphql_query(token, PROJECTS_SERVICES_QUERY)
    if not out.get("ok"):
        err = ((out.get("errors") or [{}])[0] or {}).get("message", "GraphQL query failed")
        return {
            "ok": False,
            "services": [],
            "error": redact_text(str(err)),
            "status_code": out.get("status_code"),
        }
    services: list[dict[str, Any]] = []
    projects = (((out.get("data") or {}).get("projects") or {}).get("edges")) or []
    for edge in projects:
        if not isinstance(edge, dict):
            continue
        project = edge.get("node") if isinstance(edge.get("node"), dict) else {}
        project_id = str(project.get("id") or "")
        project_name = str(project.get("name") or "")
        for svc_edge in (project.get("services") or {}).get("edges") or []:
            if not isinstance(svc_edge, dict):
                continue
            node = svc_edge.get("node") if isinstance(svc_edge.get("node"), dict) else {}
            services.append(
                {
                    "service_id": str(node.get("id") or ""),
                    "service_name": str(node.get("name") or ""),
                    "project_id": project_id,
                    "project_name": project_name,
                }
            )
    return {"ok": True, "services": services, "error": None}


def find_service_by_name(token: str, service_name: str) -> dict[str, Any] | None:
    target = _normalize(service_name)
    if not target:
        return None
    best: dict[str, Any] | None = None
    best_score = 0
    for svc in list_services(token):
        name = _normalize(str(svc.get("service_name") or ""))
        score = 0
        if name == target:
            score = 100
        elif target in name or name in target:
            score = 80
        if score > best_score:
            best_score = score
            best = svc
    return best if best_score >= 80 else None


def parse_deployment_record(node: dict[str, Any]) -> dict[str, Any]:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    return {
        "id": str(node.get("id") or ""),
        "state": str(node.get("status") or "unknown").lower(),
        "target": "production",
        "branch": str(meta.get("branch") or meta.get("commitBranch") or ""),
        "commit": str(meta.get("commitHash") or meta.get("commitSha") or "")[:12],
        "commit_message": str(meta.get("commitMessage") or "")[:200],
        "created_at": node.get("createdAt"),
        "url": str(node.get("url") or ""),
        "error_message": str(meta.get("error") or meta.get("reason") or ""),
    }


def list_service_deployments(token: str, *, service_id: str, limit: int = 20) -> list[dict[str, Any]]:
    out = graphql_query(
        token,
        SERVICE_DEPLOYMENTS_QUERY,
        {"serviceId": service_id, "first": limit},
    )
    if not out.get("ok"):
        return []
    service = (out.get("data") or {}).get("service") or {}
    edges = ((service.get("deployments") or {}).get("edges")) or []
    rows: list[dict[str, Any]] = []
    for edge in edges:
        if isinstance(edge, dict) and isinstance(edge.get("node"), dict):
            rows.append(parse_deployment_record(edge["node"]))
    return rows


def fetch_deployment_logs(token: str, *, deployment_id: str) -> list[dict[str, Any]]:
    out = graphql_query(token, SERVICE_LOGS_QUERY, {"deploymentId": deployment_id})
    if not out.get("ok"):
        return []
    logs = (out.get("data") or {}).get("deploymentLogs") or []
    structured: list[dict[str, Any]] = []
    for row in logs:
        if not isinstance(row, dict):
            continue
        ts = row.get("timestamp")
        from aethos_core.providers.railway.railway_log_evidence import normalize_railway_timestamp_to_utc

        normalized_ts = normalize_railway_timestamp_to_utc(ts) if ts is not None else None
        structured.append(
            {
                "timestamp": normalized_ts or ts,
                "level": str(row.get("level") or "INFO"),
                "message": str(row.get("message") or ""),
                "source": "deployment_logs",
            }
        )
    return structured


def fetch_runtime_logs_after(
    token: str,
    *,
    service_id: str,
    service_name: str = "",
    environment_id: str | None = None,
    since_iso: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    from aethos_core.providers.railway.railway_log_evidence import fetch_runtime_logs_after as _fetch

    return _fetch(
        token,
        service_id=service_id,
        service_name=service_name,
        environment_id=environment_id,
        since_iso=since_iso,
        limit=limit,
    )


def latest_log_timestamp(logs: list[dict[str, Any]]) -> str | None:
    latest: str | None = None
    for row in logs:
        ts = row.get("timestamp")
        if ts is None:
            continue
        text = str(ts)
        if latest is None or text > latest:
            latest = text
    return latest


def logs_after_timestamp(logs: list[dict[str, Any]], *, since_iso: str) -> list[dict[str, Any]]:
    return [row for row in logs if str(row.get("timestamp") or "") > since_iso]
