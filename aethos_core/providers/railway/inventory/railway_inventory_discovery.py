# SPDX-License-Identifier: Apache-2.0
"""Canonical Railway project/service inventory discovery — safe, shared across paths."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.api_client import RAILWAY_GRAPHQL_URL, graphql_query
from aethos_core.security.secret_redaction import redact_text

RAILWAY_INVENTORY_PROBE = "ProjectsEnvironmentsServices"

PROJECTS_ENVIRONMENTS_SERVICES_QUERY = """
query ProjectsEnvironmentsServices {
  projects {
    edges {
      node {
        id
        name
        environments {
          edges {
            node {
              id
              name
            }
          }
        }
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


@dataclass
class RailwayInventoryTopology:
    ok: bool
    projects: list[dict[str, Any]] = field(default_factory=list)
    project_count: int = 0
    environment_count: int = 0
    service_count: int = 0
    error: str = ""
    probe: str = RAILWAY_INVENTORY_PROBE
    endpoint: str = RAILWAY_GRAPHQL_URL
    graphql_errors: list[Any] = field(default_factory=list)
    partial: bool = False


def _edge_nodes(edges: Any) -> list[dict[str, Any]]:
    if not isinstance(edges, list):
        return []
    nodes: list[dict[str, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        node = edge.get("node")
        if isinstance(node, dict):
            nodes.append(node)
    return nodes


def parse_projects_environments_services_payload(data: dict[str, Any] | None) -> RailwayInventoryTopology:
    """Normalize Railway GraphQL projects/environments/services response shape."""
    root = data if isinstance(data, dict) else {}
    project_edges = _edge_nodes(((root.get("projects") or {}).get("edges")))
    projects_out: list[dict[str, Any]] = []
    env_total = 0
    svc_total = 0

    for project in project_edges:
        project_id = str(project.get("id") or "")
        project_name = str(project.get("name") or project_id or "unknown")
        env_nodes = _edge_nodes((project.get("environments") or {}).get("edges"))
        service_nodes = _edge_nodes((project.get("services") or {}).get("edges"))

        if not env_nodes:
            env_nodes = [{"id": "production", "name": "production"}]

        environments: list[dict[str, Any]] = []
        for env_node in env_nodes:
            env_id = str(env_node.get("id") or "")
            env_name = str(env_node.get("name") or env_id or "production")
            services = [
                {"id": str(svc.get("id") or ""), "name": str(svc.get("name") or "")}
                for svc in service_nodes
                if str(svc.get("name") or "").strip()
            ]
            env_total += 1
            svc_total += len(services)
            environments.append({"id": env_id, "name": env_name, "services": services})

        projects_out.append(
            {
                "id": project_id,
                "name": project_name,
                "environments": environments,
                "service_count": sum(len(e.get("services") or []) for e in environments),
            }
        )

    return RailwayInventoryTopology(
        ok=True,
        projects=projects_out,
        project_count=len(projects_out),
        environment_count=env_total,
        service_count=svc_total,
    )


def fetch_railway_inventory_topology(token: str) -> RailwayInventoryTopology:
    """Query Railway inventory GraphQL — never raises."""
    if not str(token or "").strip():
        return RailwayInventoryTopology(
            ok=False,
            error="Railway API token missing.",
        )
    try:
        out = graphql_query(token, PROJECTS_ENVIRONMENTS_SERVICES_QUERY)
    except Exception as exc:
        return RailwayInventoryTopology(
            ok=False,
            error=redact_text(f"Railway inventory query failed: {exc}"),
        )

    if not out.get("ok"):
        errors = out.get("errors") if isinstance(out.get("errors"), list) else []
        err = redact_text(
            str(((errors[0] if errors else {}) or {}).get("message") or "GraphQL discovery failed")
        )
        return RailwayInventoryTopology(
            ok=False,
            error=err,
            graphql_errors=errors,
        )

    data = out.get("data")
    if not isinstance(data, dict):
        return RailwayInventoryTopology(
            ok=False,
            error="Railway API returned an unexpected inventory payload.",
            partial=True,
        )

    parsed = parse_projects_environments_services_payload(data)
    parsed.probe = RAILWAY_INVENTORY_PROBE
    parsed.endpoint = RAILWAY_GRAPHQL_URL
    return parsed


def topology_to_inventory_summary(topology: RailwayInventoryTopology) -> dict[str, Any]:
    """Checks/inventory dict shape shared by readiness and chat blockers."""
    return {
        "ok": topology.ok,
        "project_count": topology.project_count,
        "environment_count": topology.environment_count,
        "service_count": topology.service_count,
        "projects": topology.projects,
        "error": topology.error,
        "inventory_probe": topology.probe,
        "inventory_probe_status": "pass" if topology.ok else "fail",
        "inventory_endpoint": topology.endpoint,
        "partial": topology.partial,
    }
