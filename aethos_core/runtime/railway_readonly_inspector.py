# SPDX-License-Identifier: Apache-2.0
"""Run Railway on-demand inventory jobs — API only; operational memory via 9.3L dispatch."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.operations.execution.execution_evidence import CONFIDENCE_CONFIRMED, evidence_item
from aethos_core.providers.railway.inventory.inventory_adapter import RailwayInventoryAdapter


class RailwayInventoryError(Exception):
    """Safe, operator-facing inventory failure (no token values)."""


@dataclass
class RailwayInventoryOutcome:
    summary: str
    preview: str
    full_result: str
    items: list[dict[str, Any]]
    evidence: list[dict[str, Any]]


def distinct_project_names(items: list[dict[str, Any]]) -> set[str]:
    """Distinct Railway project names across the full inventory (not preview slice)."""
    names: set[str] = set()
    for row in items:
        project = str(row.get("project_name") or "").strip()
        if project and project != "—":
            names.add(project)
    return names


def build_chat_summary(items: list[dict[str, Any]]) -> str:
    if not items:
        return build_empty_inventory_summary()
    lines = ["Railway services found:", ""]
    for row in items[:8]:
        name = str(row.get("name") or row.get("service_name") or "—")
        project = str(row.get("project_name") or "—")
        lines.append(f"- **{name}** — project: `{project}`")
    if len(items) > 8:
        lines.append("")
        lines.append(f"+ {len(items) - 8} more services — see Mission Control → Jobs for the full report.")
    lines.append("")
    project_count = len(distinct_project_names(items)) or 1
    lines.append(
        f"Found **{len(items)}** service{'s' if len(items) != 1 else ''} "
        f"across **{project_count}** project{'s' if project_count != 1 else ''}."
    )
    return "\n".join(lines)


def build_empty_inventory_summary() -> str:
    return (
        "Railway inventory completed, but no services were returned for this token.\n\n"
        "Check:\n"
        "- token account scope\n"
        "- Railway workspace/team access\n"
        "- GraphQL response shape"
    )


def build_inventory_error_summary(error: str) -> str:
    safe = (error or "GraphQL query failed").strip()[:240]
    return (
        "Railway inventory could not retrieve services.\n\n"
        f"Reason:\n{safe}\n\n"
        "Check:\n"
        "- token validity\n"
        "- account/team access\n"
        "- Railway GraphQL response"
    )


def build_full_report(
    items: list[dict[str, Any]],
    *,
    user_request: str = "",
    inventory_error: str = "",
) -> str:
    project_count = len(distinct_project_names(items))
    lines = [
        "# Railway services inventory",
        "",
        f"**Services found:** {len(items)}",
        f"**Projects found:** {project_count}",
        "",
        "| Service | Project | Service ID |",
        "| --- | --- | --- |",
    ]
    for row in items:
        name = str(row.get("name") or row.get("service_name") or "—")
        project = str(row.get("project_name") or "—")
        sid = str(row.get("service_id") or "—")
        lines.append(f"| {name} | {project} | `{sid[:16]}…` |" if len(sid) > 16 else f"| {name} | {project} | `{sid}` |")
    if not items:
        lines.append("| (none) | — | — |")
    lines.extend(["", "## Evidence", "", "- source:railway_api · confidence: confirmed"])
    if inventory_error:
        lines.extend(["", "## Diagnostic", "", f"- {inventory_error.strip()[:500]}"])
    if user_request:
        lines.extend(["", f"_Request:_ {user_request[:500]}"])
    return "\n".join(lines)


def run_railway_services_inventory(
    *,
    credential_id: str,
    user_request: str = "",
) -> RailwayInventoryOutcome:
    from aethos_core.providers.railway.auth import RailwayAuthAdapter

    token = RailwayAuthAdapter().get_api_token(credential_id)
    if not token:
        raise RailwayInventoryError("Railway API token unavailable for inventory.")

    fetched = RailwayInventoryAdapter().fetch_projects_inventory(auth_context={"token": token})
    if not fetched.get("ok"):
        error = str(fetched.get("error") or "GraphQL query failed")
        summary = build_inventory_error_summary(error)
        full = build_full_report([], user_request=user_request, inventory_error=error)
        raise RailwayInventoryError(summary)

    items = fetched.get("items") if isinstance(fetched.get("items"), list) else []
    summary = build_chat_summary(items)
    full = build_full_report(items, user_request=user_request)
    evidence = [
        evidence_item(
            source="railway_api",
            type="inventory",
            confidence=CONFIDENCE_CONFIRMED,
            message=f"Listed {len(items)} Railway service(s) via GraphQL API.",
            service_count=len(items),
        )
    ]
    if items:
        for row in items[:8]:
            name = str(row.get("name") or row.get("service_name") or "")
            if name:
                evidence.append(
                    evidence_item(
                        source="railway_api",
                        type="service",
                        confidence=CONFIDENCE_CONFIRMED,
                        message=f"Service `{name}` in project `{row.get('project_name') or '—'}`.",
                        service_id=row.get("service_id"),
                        project_id=row.get("project_id"),
                    )
                )
    return RailwayInventoryOutcome(
        summary=summary,
        preview=summary.split("\n")[0][:240],
        full_result=full,
        items=items,
        evidence=evidence,
    )
