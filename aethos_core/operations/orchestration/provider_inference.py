# SPDX-License-Identifier: Apache-2.0
"""Inventory-first provider inference — avoid silent Vercel guessing."""

from __future__ import annotations

from typing import Any


def _norm(name: str) -> str:
    return (name or "").strip().lower().replace("_", "").replace("-", "")


def _matches(hint: str, candidate: str) -> bool:
    h = _norm(hint)
    c = _norm(candidate)
    if not h or not c:
        return False
    return h == c or h in c or c in h


def find_target_in_operational_memory(hint: str) -> dict[str, Any] | None:
    """Phase 9.3L — provider-neutral shaping from persisted inventory memory."""
    from aethos_core.runtime.operational_memory import operational_memory

    h = _norm(hint)
    if not h:
        return None

    for name in operational_memory.known_railway_services():
        if _matches(hint, name):
            row = operational_memory.get_railway_service_memory().get(name, {})
            return {
                "provider": "railway",
                "name": name,
                "service_name": name,
                "service_id": row.get("service_id"),
                "project_name": row.get("project_name"),
                "source": "operational_memory_railway",
            }

    for name in operational_memory.known_vercel_projects():
        if _matches(hint, name):
            row = operational_memory.get_vercel_project_memory().get(name, {})
            return {
                "provider": "vercel",
                "name": name,
                "url": row.get("production_url") or row.get("known_production_url"),
                "source": "operational_memory_vercel",
            }

    for name in operational_memory.known_github_repos():
        if _matches(hint, name) or _matches(hint, name.split("/")[-1]):
            row = operational_memory.get_github_repo_memory().get(name, {})
            return {
                "provider": "github",
                "name": name,
                "url": row.get("html_url"),
                "source": "operational_memory_github",
            }

    return None


def find_target_in_railway_inventory(hint: str) -> dict[str, Any] | None:
    from aethos_core.runtime.latest_inventory_store import get_latest_railway_inventory_job

    latest = get_latest_railway_inventory_job()
    if not latest:
        return None
    for row in latest.get("services_by_name", {}).values():
        name = str(row.get("name") or row.get("service_name") or "")
        if _matches(hint, name):
            return {
                "provider": "railway",
                "name": name,
                "service_name": name,
                "service_id": row.get("service_id"),
                "project_name": row.get("project_name"),
                "url": row.get("url"),
                "domains": row.get("domains") or [],
                "source": "railway_inventory",
            }
    return None


def find_target_in_vercel_inventory(hint: str) -> dict[str, Any] | None:
    from aethos_core.runtime.latest_inventory_store import get_latest_project_state

    state = get_latest_project_state(hint)
    if not state or not state.get("name"):
        return None
    return {
        "provider": "vercel",
        "name": state.get("name"),
        "url": state.get("production_url"),
        "source": state.get("source") or "vercel_inventory",
    }


def find_target_in_github_inventory(hint: str) -> dict[str, Any] | None:
    from aethos_core.runtime.latest_inventory_store import get_latest_github_inventory_job

    latest = get_latest_github_inventory_job()
    if not latest:
        return None
    for row in latest.get("repos_by_name", {}).values():
        name = str(row.get("name") or row.get("full_name") or "")
        if _matches(hint, name):
            return {"provider": "github", "name": name, "url": row.get("html_url"), "source": "github_inventory"}
    return None


def infer_provider_for_hints(hints: list[str]) -> dict[str, Any]:
    if not hints:
        return {"status": "unknown", "matches": []}
    matches: list[dict[str, Any]] = []
    for hint in hints:
        memory_hit = find_target_in_operational_memory(hint)
        if memory_hit:
            matches.append({**memory_hit, "hint": hint})
            continue
        for finder in (find_target_in_railway_inventory, find_target_in_vercel_inventory, find_target_in_github_inventory):
            hit = finder(hint)
            if hit:
                matches.append({**hit, "hint": hint})
    providers = sorted({m["provider"] for m in matches})
    if len(providers) == 1:
        primary = matches[0]
        return {
            "status": "resolved",
            "provider": providers[0],
            "target_name": primary.get("name"),
            "url": primary.get("url"),
            "matches": matches,
            "match_source": primary.get("source"),
        }
    if len(providers) > 1:
        return {"status": "ambiguous", "providers": providers, "matches": matches}
    return {"status": "unknown", "matches": matches}


def resolve_url_for_target(hint: str) -> str:
    inferred = infer_provider_for_hints([hint])
    url = str(inferred.get("url") or "").strip()
    if url.startswith(("http://", "https://")):
        return url
    for match in inferred.get("matches") or []:
        candidate = str(match.get("url") or "").strip()
        if candidate.startswith(("http://", "https://")):
            return candidate
    return ""
