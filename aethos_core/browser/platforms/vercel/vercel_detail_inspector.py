# SPDX-License-Identifier: Apache-2.0
"""Read-only project detail drilldown — observational navigation only."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.browser.platforms.vercel.vercel_entities import HealthState, VercelProject
from aethos_core.browser.platforms.vercel.vercel_production_urls import (
    best_production_url,
    extract_urls_from_text,
)


def infer_team_from_page(page: Any) -> str | None:
    try:
        locator = page.locator('a[href*="vercel.com/"]')
        count = min(locator.count(), 40)
    except Exception:
        return None
    for i in range(count):
        try:
            href = locator.nth(i).get_attribute("href") or ""
            team = _team_slug_from_page_url(href)
            if team:
                return team
        except Exception:
            continue
    return None


def _team_slug_from_page_url(url: str) -> str | None:
    m = re.search(r"vercel\.com/([^/?#]+)", url or "", re.I)
    if not m:
        return None
    slug = m.group(1).lower()
    if slug in ("dashboard", "login", "signup", "account", "teams", "new"):
        return None
    return slug


def project_detail_url(team: str, project: str) -> str:
    return f"https://vercel.com/{team}/{project}"


def project_deployments_url(team: str, project: str) -> str:
    return f"https://vercel.com/{team}/{project}/deployments"


def _needs_detail_drilldown(project: VercelProject) -> bool:
    if project.production_url:
        return False
    if project.health in (HealthState.HEALTHY, HealthState.FAILED):
        return False
    return project.health in (HealthState.UNKNOWN, HealthState.LIKELY_DEGRADED)


def enrich_projects_from_detail_pages(
    page: Any,
    projects: list[VercelProject],
    *,
    page_url: str = "",
    max_visits: int = 5,
) -> list[VercelProject]:
    """Read-only: open project/deployments pages for unclear projects, then return."""
    team = _team_slug_from_page_url(page_url) or infer_team_from_page(page)

    if not team:
        return projects

    unclear = [p for p in projects if _needs_detail_drilldown(p)][:max_visits]
    if not unclear:
        return projects

    dashboard_url = page_url or page.url if hasattr(page, "url") else "https://vercel.com/dashboard"

    for proj in unclear:
        detail_url = project_detail_url(team, proj.name)
        try:
            page.goto(detail_url, wait_until="domcontentloaded", timeout=12_000)
            try:
                page.wait_for_timeout(800)
            except Exception:
                pass
            text = ""
            try:
                text = page.locator("body").inner_text(timeout=5_000) or ""
            except Exception:
                pass

            url, source, _conf = best_production_url(
                project_name=proj.name,
                card_text=text,
                allow_page_text=False,
            )
            if url:
                proj.production_url = url
                proj.production_url_source = source or "detail_page"
                proj.production_url_confidence = "high"
                proj.production_url_verified = True
                host = url.split("//")[-1].split("/")[0]
                if host:
                    proj.known_domains = list({*(proj.known_domains or []), host})

            low = text.lower()
            if re.search(r"\b(failed|error|errored)\b", low):
                proj.deployment_state = "failed"
            elif re.search(r"\b(no production deployment|not deployed)\b", low):
                proj.deployment_state = "no_production"
            elif re.search(r"\b(production|ready)\b", low) and url:
                proj.deployment_state = "ready"
            elif re.search(r"\b(deployed|deployment)\b", low):
                proj.deployment_state = "deployed"

            for m in extract_urls_from_text(text, proj.name):
                if m.url and not proj.production_url:
                    proj.production_url = m.url
                    proj.production_url_source = m.source

            try:
                page.goto(project_deployments_url(team, proj.name), wait_until="domcontentloaded", timeout=10_000)
                dep_text = page.locator("body").inner_text(timeout=4_000) or ""
                u2, s2, _c2 = best_production_url(
                    project_name=proj.name,
                    card_text=dep_text,
                    allow_page_text=False,
                )
                if u2 and not proj.production_url:
                    proj.production_url = u2
                    proj.production_url_source = s2 or "deployments_tab"
                    proj.production_url_confidence = "high"
                    proj.production_url_verified = True
            except Exception:
                pass
        except Exception:
            continue

    try:
        page.goto(dashboard_url, wait_until="domcontentloaded", timeout=12_000)
    except Exception:
        pass

    return projects
