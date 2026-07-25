# SPDX-License-Identifier: Apache-2.0
"""Vercel domains — API-backed read-only inspection."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.vercel.api_client import (
    find_project_by_name,
    list_project_domains,
    parse_domain_record,
    parse_project_record,
)


def fetch_domains(token: str, *, project_name: str) -> dict[str, Any]:
    project = find_project_by_name(token, project_name)
    if not project:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Project `{project_name}` not found via Vercel API.",
            "domains": [],
        }
    project_id = str(project.get("id") or "")
    team_id = str(project.get("teamId") or "") or None
    parsed = parse_project_record(project)
    api_domains = list_project_domains(token, project_id, team_id=team_id)
    records = [parse_domain_record(d) for d in api_domains if isinstance(d, dict)]
    vercel_app = f"{parsed.get('name')}.vercel.app" if parsed.get("name") else None
    if vercel_app and not any(r.get("domain") == vercel_app for r in records):
        records.insert(
            0,
            {
                "domain": vercel_app,
                "type": "vercel.app",
                "verified": True,
                "production": True,
                "redirect": "",
                "last_seen": None,
                "apex": "",
            },
        )
    for alias in parsed.get("domains") or []:
        if alias and not any(r.get("domain") == alias for r in records):
            records.append(
                {
                    "domain": alias,
                    "type": "production_alias",
                    "verified": True,
                    "production": True,
                    "redirect": "",
                    "last_seen": None,
                    "apex": "",
                }
            )
    return {
        "ok": True,
        "source": "provider_api",
        "project_id": project_id,
        "project_name": str(project.get("name") or project_name),
        "domain_count": len(records),
        "domains": records,
    }


def format_domains_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok"):
        return str(payload.get("error") or "Domain fetch failed.")
    lines = [
        f"Project: {payload.get('project_name')}",
        f"Domains ({payload.get('domain_count', 0)}):",
        "",
    ]
    for dom in payload.get("domains") or []:
        verified = "verified" if dom.get("verified") else "unverified"
        prod = "production" if dom.get("production") else "preview/other"
        redirect = dom.get("redirect") or "—"
        lines.append(
            f"- `{dom.get('domain')}` · {dom.get('type', 'custom')} · {verified} · {prod} · redirect: {redirect}"
        )
    if len(lines) <= 3:
        lines.append("(no domains returned)")
    return "\n".join(lines)
