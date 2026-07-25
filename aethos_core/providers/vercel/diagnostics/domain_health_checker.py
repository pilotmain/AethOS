# SPDX-License-Identifier: Apache-2.0
"""Vercel domain health checks — reachability for production domains."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.vercel.operations.domains_api import fetch_domains


def _normalize_url(domain: str) -> str:
    raw = (domain or "").strip()
    if not raw:
        return ""
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return f"https://{raw}"


def check_domain_health(
    token: str,
    *,
    project_name: str,
    production_url: str | None = None,
) -> dict[str, Any]:
    domains_payload = fetch_domains(token, project_name=project_name)
    if not domains_payload.get("ok"):
        return {
            "ok": False,
            "error": str(domains_payload.get("error") or "Domain fetch failed."),
            "checks": [],
        }

    from aethos_core.operations.execution.execution_runner import _url_reachability

    candidates: list[str] = []
    if production_url:
        candidates.append(production_url)
    for dom in domains_payload.get("domains") or []:
        if not isinstance(dom, dict):
            continue
        if dom.get("production") or dom.get("verified"):
            candidates.append(str(dom.get("domain") or ""))
    seen: set[str] = set()
    checks: list[dict[str, Any]] = []
    for domain in candidates:
        url = _normalize_url(domain)
        if not url or url in seen:
            continue
        seen.add(url)
        reach = _url_reachability(url)
        checks.append(
            {
                "domain": domain,
                "url": url,
                "reachable": bool(reach.get("reachable")),
                "status_code": reach.get("status_code"),
                "summary": str(reach.get("summary") or ""),
            }
        )
        if len(checks) >= 3:
            break

    healthy = sum(1 for row in checks if row.get("reachable"))
    return {
        "ok": True,
        "project_name": project_name,
        "domain_count": domains_payload.get("domain_count", 0),
        "domains": domains_payload.get("domains") or [],
        "checks": checks,
        "healthy_count": healthy,
        "summary": f"{healthy}/{len(checks)} checked domain(s) reachable." if checks else "No production domains to check.",
    }
