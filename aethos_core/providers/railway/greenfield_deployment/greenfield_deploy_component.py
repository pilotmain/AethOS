# SPDX-License-Identifier: Apache-2.0
"""Detect API vs Mission Control UI greenfield deploy targets from user text."""

from __future__ import annotations

import re
from typing import Any, Literal

DeployComponent = Literal["api", "ui"]

_UI_DEPLOY_RX = re.compile(
    r"\b("
    r"mission\s+control\s+ui"
    r"|mission\s+control"
    r"|aethos\s+ui"
    r"|pilotos\s+ui"
    r"|pilotos\s+mission\s+control"
    r"|deploy\s+(?:the\s+)?ui\b"
    r"|ui\s+deployment"
    r")\b",
    re.I,
)
_API_DEPLOY_RX = re.compile(r"\b(aethos[\s-]?api|backend|api\s+service)\b", re.I)
_ADDITIONAL_SERVICE_RX = re.compile(
    r"\b("
    r"also\s+deploy"
    r"|new\s+deployment"
    r"|new\s+service"
    r"|another\s+service"
    r"|second\s+service"
    r"|separate\s+service"
    r"|deploy\s+(?:the\s+)?ui\b"
    r")\b",
    re.I,
)


def is_additional_railway_service_deploy_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_ADDITIONAL_SERVICE_RX.search(raw) or _UI_DEPLOY_RX.search(raw))


def detect_greenfield_deploy_component(text: str) -> DeployComponent:
    raw = (text or "").strip()
    if _UI_DEPLOY_RX.search(raw):
        return "ui"
    if _API_DEPLOY_RX.search(raw) and not re.search(r"\bui\b", raw, re.I):
        return "api"
    if re.search(r"\bui\b", raw, re.I) and re.search(r"\b(deploy|deployment)\b", raw, re.I):
        return "ui"
    return "api"


def infer_greenfield_service_name(*, text: str, repo: str, component: DeployComponent) -> str:
    if component == "ui":
        return "aethos-ui"
    parsed = (text or "").lower()
    if "aethos-api" in parsed:
        return "aethos-api"
    from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import infer_service_name_from_repo

    return infer_service_name_from_repo(repo)


def greenfield_root_directory(*, component: DeployComponent) -> str:
    return "web" if component == "ui" else ""


def ui_required_env_var_names() -> list[str]:
    return ["NEXT_PUBLIC_API_BASE"]


def resolve_ui_public_api_base(*, plan: dict[str, Any] | None = None) -> str:
    """Resolve Mission Control UI API base for Railway deploy (not localhost)."""
    from pathlib import Path

    plan = plan or {}
    local = ""
    root = Path(str(plan.get("workspace_root") or "")).expanduser()
    if not root.is_dir():
        from aethos_core.providers.railway.greenfield_deployment.local_workspace_source import (
            resolve_configured_workspace_root,
        )

        root = resolve_configured_workspace_root()
    if root and root.is_dir():
        for rel in ("web/.env.local", "web/.env"):
            path = root / rel
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.strip().startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                if key.strip().upper() == "NEXT_PUBLIC_API_BASE":
                    local = value.strip().strip("'\"")
                    break
            if local:
                break

    if local and "localhost" not in local.lower() and "127.0.0.1" not in local:
        return local.rstrip("/")

    environment = str(plan.get("environment") or "staging").strip().lower()
    try:
        from aethos_core.credentials import get_provider_api_token
        from aethos_core.providers.railway.api_client import graphql_query

        token = get_provider_api_token("railway")
        if token:
            query = """
            query {
              projects {
                edges {
                  node {
                    name
                    environments {
                      edges {
                        node {
                          name
                          serviceInstances {
                            edges {
                              node {
                                serviceName
                                domains { serviceDomains { domain } }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
            """
            out = graphql_query(token, query, {})
            project_name = str(plan.get("project") or "pilotos").strip().lower()
            for edge in (((out.get("data") or {}).get("projects") or {}).get("edges") or []):
                node = edge.get("node") or {}
                if str(node.get("name") or "").strip().lower() != project_name:
                    continue
                for eedge in ((node.get("environments") or {}).get("edges") or []):
                    env = eedge.get("node") or {}
                    if str(env.get("name") or "").strip().lower() != environment:
                        continue
                    for sedge in ((env.get("serviceInstances") or {}).get("edges") or []):
                        sn = sedge.get("node") or {}
                        if str(sn.get("serviceName") or "").strip().lower() != "aethos-api":
                            continue
                        domains = ((sn.get("domains") or {}).get("serviceDomains") or [])
                        if domains and isinstance(domains[0], dict):
                            domain = str(domains[0].get("domain") or "").strip()
                            if domain:
                                return f"https://{domain}".rstrip("/")
    except Exception:
        pass

    if environment == "staging":
        return "https://aethos-api-staging.up.railway.app"
    if environment in {"production", "prod"}:
        return "https://aethos-api.up.railway.app"
    return local.rstrip("/") if local else ""


def inspect_component_repo(
    workspace_root: str,
    *,
    component: DeployComponent,
) -> dict[str, Any]:
    from aethos_core.providers.railway.greenfield_deployment.local_repo_inspection import (
        inspect_local_repo_for_deployment,
    )

    inspection = inspect_local_repo_for_deployment(workspace_root)
    if component != "ui":
        return inspection

    from pathlib import Path

    root = Path(workspace_root)
    web_pkg = root / "web" / "package.json"
    if not web_pkg.is_file():
        inspection["ok"] = False
        inspection["error"] = "web/package.json not found for UI deployment"
        return inspection

    inspection["runtime"] = "Node"
    inspection["build_command"] = "cd web && npm ci && npm run build"
    inspection["start_command"] = "cd web && npm start"
    inspection["health_check_path"] = "/"
    inspection["root_directory"] = "web"
    inspection["deploy_component"] = "ui"
    inspection["required_env_var_names"] = ui_required_env_var_names()
    return inspection
