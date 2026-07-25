# SPDX-License-Identifier: Apache-2.0
"""Chat routing for synchronous Railway project/service inventory listing."""

from __future__ import annotations

import re
from typing import Any

_PROJECTS_RX = re.compile(
    r"\b(?:show|list|what are)\b.*\b(?:my\s+)?railway\b.*\b(?:projects?|apps|services?)\b|"
    r"\b(?:show|list)\b.*\brailway\b.*\b(?:projects?|apps|services?)\b|"
    r"\brailway\b.*\b(?:projects?|apps|services?)\b.*\b(?:list|inventory)\b",
    re.I,
)


def is_railway_projects_inventory_intent(text: str) -> bool:
    return bool(_PROJECTS_RX.search((text or "").strip()))


def compose_railway_inventory_blocker(
    *,
    inventory: dict[str, Any],
    checks: dict[str, Any] | None = None,
) -> str:
    checks = checks or {}
    cred_source = (
        checks.get("railway_credential_source_label")
        or checks.get("railway_credential_source")
        or "unknown"
    )
    validation_probe = checks.get("railway_validation_probe") or "ProjectsAndServices"
    validation_ok = bool(checks.get("railway_api_connection_ok"))
    inventory_probe = inventory.get("inventory_probe") or "ProjectsEnvironmentsServices"
    inventory_ok = bool(inventory.get("ok"))
    err = str(inventory.get("error") or "Railway project/service discovery failed.").strip()
    project_count = int(inventory.get("project_count") or 0)
    service_count = int(inventory.get("service_count") or 0)

    lines = [
        "**Railway project/service discovery failed.**",
        "",
        "### Blocker",
        "- Code: `RAILWAY_INVENTORY_UNAVAILABLE`",
        f"- Likely cause: {err[:240]}",
        "",
        "### Credential & probes",
        f"- Credential source: **{cred_source}**",
        f"- Validation probe (`{validation_probe}`): **{'pass' if validation_ok else 'fail'}**",
        f"- Inventory probe (`{inventory_probe}`): **{'pass' if inventory_ok else 'fail'}**",
    ]
    if project_count or service_count:
        lines.append(f"- Partial visibility: **{project_count}** project(s), **{service_count}** service(s)")
    lines.extend(
        [
            "",
            "### Required action",
            "Confirm the Railway token has project read access, then retry discovery.",
            "",
            "### Safe next command",
            "`show railway credential diagnostics`",
            "",
            "No secrets are displayed. No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def format_railway_projects_inventory_reply(inventory: dict[str, Any]) -> str:
    projects = list(inventory.get("projects") or [])
    project_count = int(inventory.get("project_count") or len(projects))
    service_count = int(inventory.get("service_count") or 0)
    env_count = int(inventory.get("environment_count") or 0)
    stale = bool(inventory.get("stale_cache"))

    title = "**Railway projects and services**"
    if stale:
        title = "**Railway projects and services** _(cached)_"

    lines = [
        title,
        "",
    ]
    if stale:
        note = str(inventory.get("cache_note") or "Live Railway API probe failed; showing last cached inventory.")
        refreshed = inventory.get("last_refreshed_at")
        if refreshed:
            note += f" Last refreshed: `{refreshed}`."
        lines.extend([note, ""])
    lines.extend(
        [
            f"- Projects: **{project_count}**",
            f"- Environments: **{env_count}**",
            f"- Services: **{service_count}**",
            f"- Inventory probe: `{inventory.get('inventory_probe') or 'ProjectsEnvironmentsServices'}` · **{'pass (cache)' if stale else 'pass'}**",
            "",
        ]
    )

    if not projects:
        lines.extend(
            [
                "No Railway projects were returned for this token.",
                "",
                "Check workspace/team access on the token account.",
                "",
                "No mutation has been performed.",
            ]
        )
        return "\n".join(lines)

    for project in projects[:12]:
        pname = str(project.get("name") or project.get("id") or "unknown")
        lines.append(f"### `{pname}`")
        for env in list(project.get("environments") or [])[:6]:
            ename = str(env.get("name") or env.get("id") or "production")
            raw_services = list(env.get("services") or [])
            services: list[str] = []
            for svc in raw_services:
                if isinstance(svc, dict):
                    name = str(svc.get("name") or "").strip()
                else:
                    name = str(svc or "").strip()
                if name:
                    services.append(name)
            svc_preview = ", ".join(services[:8]) if services else "(no services listed)"
            suffix = f" (+{len(services) - 8} more)" if len(services) > 8 else ""
            lines.append(f"- **{ename}**: {svc_preview}{suffix}")
        lines.append("")

    if len(projects) > 12:
        lines.append(f"_+ {len(projects) - 12} more project(s) not shown._")
    lines.append("No mutation has been performed.")
    return "\n".join(lines)


def build_railway_inventory_summary_from_cache() -> dict[str, Any] | None:
    """Build list-inventory payload from persisted snapshot — no live Railway API call."""
    from aethos_core.provider_discovery.inventory_memory import load_inventory_snapshot

    cached = load_inventory_snapshot(provider="railway")
    if cached is None or not cached.projects:
        return None

    projects_out: list[dict[str, Any]] = []
    env_count = 0
    svc_count = 0
    for project in cached.projects[:12]:
        envs: list[dict[str, Any]] = []
        for env in project.environments[:6]:
            env_count += 1
            services = [svc.name for svc in env.services[:12]]
            svc_count += len(env.services)
            envs.append({"id": env.id, "name": env.name, "services": services})
        projects_out.append({"id": project.id, "name": project.name, "environments": envs})

    return {
        "ok": True,
        "project_count": len(cached.projects),
        "environment_count": env_count,
        "service_count": svc_count,
        "projects": projects_out,
        "inventory_probe": "ProjectsEnvironmentsServices",
        "inventory_probe_status": "pass (cache)",
        "stale_cache": True,
        "cache_freshness": cached.freshness,
        "last_refreshed_at": cached.last_refreshed_at,
        "cache_note": "Railway API rate limit or live probe failure — using last cached inventory.",
    }


def should_use_cached_railway_inventory(*, error: str) -> bool:
    lower = (error or "").lower()
    return "rate limit" in lower or "try again" in lower or "too many requests" in lower
