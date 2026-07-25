# SPDX-License-Identifier: Apache-2.0
"""DOM-aware Vercel dashboard parsing with confidence scoring and pipeline visibility."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.browser.platforms.vercel.vercel_entities import VercelProject
from aethos_core.browser.platforms.vercel.vercel_navigation_map import (
    PROJECT_CARD_SELECTORS,
    is_plausible_project_name,
    project_name_from_href,
)
from aethos_core.browser.platforms.vercel.vercel_production_urls import (
    best_production_url,
    confidence_for_source,
    dedupe_shared_production_urls,
)
from aethos_core.browser.platforms.vercel.vercel_project_scoring import (
    ProjectCandidate,
    bucket_candidates,
    score_candidate,
)


@dataclass
class ExtractionPipelineStats:
    raw_links_seen: int = 0
    project_like_links_seen: int = 0
    candidate_names_seen: int = 0
    candidates_after_nav_filter: int = 0
    candidates_after_confidence: int = 0
    confirmed_projects: int = 0
    likely_projects: int = 0
    low_confidence_ignored: int = 0
    known_memory_matches: int = 0
    dashboard_ready: bool = False
    dashboard_ready_signal: str | None = None
    rejection_reasons: list[dict[str, str]] = field(default_factory=list)
    filtered_candidates: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ParseProjectsResult:
    projects: list[VercelProject] = field(default_factory=list)
    likely_projects: list[VercelProject] = field(default_factory=list)
    ignored_labels: list[str] = field(default_factory=list)
    extraction_method: str = "dom_semantic"
    low_confidence_count: int = 0
    pipeline: ExtractionPipelineStats = field(default_factory=ExtractionPipelineStats)
    memory_fallback: bool = False
    memory_fallback_names: list[str] = field(default_factory=list)


def wait_for_dashboard_ready(page: Any, *, timeout_ms: int = 8_000) -> tuple[bool, str | None]:
    """Wait for project grid markers before extracting."""
    per = max(1500, timeout_ms // 4)
    markers = (
        "All Projects",
        "Add New",
        "Projects",
        "New Project",
    )
    for marker in markers:
        try:
            page.get_by_text(marker, exact=False).first.wait_for(state="visible", timeout=per)
            return True, marker
        except Exception:
            continue
    selectors = (
        'a[href*="/"][href*="vercel.com"]',
        '[data-testid*="project"]',
        "main a[href^='/']",
    )
    for sel in selectors:
        try:
            page.wait_for_selector(sel, timeout=per)
            return True, sel
        except Exception:
            continue
    return False, None


def _deployment_hint_from_text(text: str) -> str:
    low = (text or "").lower()
    if re.search(r"\b(failed|error|errored|build failed)\b", low):
        return "failed"
    if re.search(r"\b(no production deployment|not deployed to production)\b", low):
        return "no_production"
    if re.search(r"\b(building|deploying|queued)\b", low):
        return "building"
    if re.search(r"\b(ready|production)\b", low) and not re.search(
        r"\bno production\b", low
    ):
        return "ready"
    if re.search(r"\b(preview)\b", low):
        return "preview"
    if re.search(r"\b(deployed|deployment)\b", low):
        return "deployed"
    return ""


def _candidate_to_project(
    c: ProjectCandidate,
    *,
    bucket: str,
    source: str = "dom",
    page_text: str = "",
    memory_entry: dict[str, Any] | None = None,
) -> VercelProject:
    deploy = _deployment_hint_from_text(c.card_text)
    mem = memory_entry or {}
    mem_url = mem.get("known_production_url") or mem.get("production_url")
    prod_url, prod_source, prod_conf = best_production_url(
        project_name=c.name,
        card_text=c.card_text,
        href=c.href,
        memory_url=mem_url,
        allow_page_text=False,
    )
    if prod_url and prod_source == "memory":
        prod_conf = "high"
    repo = mem.get("known_repo")
    if not repo:
        m = re.search(r"github\.com/[\w.-]+/[\w.-]+", c.card_text, re.I)
        if m:
            repo = m.group(0)
    domains: list[str] = list(mem.get("known_domains") or [])
    if prod_url:
        host = prod_url.split("//")[-1].split("/")[0].lower()
        if host and host not in domains:
            domains.append(host)
    return VercelProject(
        name=c.name,
        status="active",
        production_url=prod_url,
        production_url_source=prod_source,
        production_url_confidence=prod_conf if prod_url else "none",
        known_domains=domains,
        git_repo=repo,
        deployment_state=deploy or None,
        last_deploy_state=deploy or None,
        deployment_status=source if source != "dom" else (deploy or None),
        attention_reason=(
            "stale — needs refresh" if source == "memory" else None
        ),
        environment=bucket,
    )


def _count_raw_links(page: Any) -> tuple[int, int, list[str]]:
    raw = 0
    project_like = 0
    hrefs: list[str] = []
    try:
        locator = page.locator("a[href]")
        count = min(locator.count(), 200)
        raw = count
        for i in range(count):
            try:
                href = locator.nth(i).get_attribute("href") or ""
            except Exception:
                continue
            if not href:
                continue
            hrefs.append(href)
            name = project_name_from_href(href)
            if name:
                project_like += 1
    except Exception:
        pass
    return raw, project_like, hrefs


def _collect_candidates_from_page(
    page: Any,
    *,
    known_projects: set[str] | None = None,
) -> tuple[dict[str, ProjectCandidate], ExtractionPipelineStats]:
    known = {k.lower() for k in (known_projects or set())}
    pipeline = ExtractionPipelineStats()
    ready, signal = wait_for_dashboard_ready(page)
    pipeline.dashboard_ready = ready
    pipeline.dashboard_ready_signal = signal

    raw, project_like, all_hrefs = _count_raw_links(page)
    pipeline.raw_links_seen = raw
    pipeline.project_like_links_seen = project_like

    candidates: dict[str, ProjectCandidate] = {}
    seen_hrefs: set[str] = set()

    def _ingest_link(href: str, card_text: str = "", *, from_dom: bool = True) -> None:
        if not href:
            return
        name = project_name_from_href(href)
        if not name:
            return
        seen_hrefs.add(href)
        prev = candidates.get(name)
        merged_text = card_text or (prev.card_text if prev else "")
        c = score_candidate(
            name,
            href=href,
            card_text=merged_text,
            from_dom=from_dom or (prev.from_dom if prev else False),
            memory_confirmed=name in known,
        )
        if not c:
            pipeline.rejection_reasons.append(
                {"name": name, "reason": "nav_or_product_filter", "href": href[:120]}
            )
            return
        if prev is None:
            candidates[c.name] = c
        else:
            if merged_text and len(merged_text) > len(prev.card_text or ""):
                prev.card_text = merged_text
            if c.score > prev.score:
                prev.score = c.score
                prev.signals = list({*prev.signals, *c.signals})
            if c.href:
                prev.href = c.href

    for href in all_hrefs:
        _ingest_link(href)

    for selector in PROJECT_CARD_SELECTORS:
        try:
            locator = page.locator(selector)
            count = min(locator.count(), 120)
        except Exception:
            continue
        for i in range(count):
            try:
                el = locator.nth(i)
                href = el.get_attribute("href") or ""
                try:
                    card_text = el.inner_text(timeout=600) or ""
                except Exception:
                    card_text = ""
                _ingest_link(href, card_text, from_dom=True)
            except Exception:
                continue

    if len(candidates) < 2:
        text = _body_text(page)
        for token in re.split(r"[\s\n]+", text):
            t = token.strip().lower().rstrip(",.")
            if not t or not is_plausible_project_name(t):
                continue
            c = score_candidate(
                t,
                card_text=text,
                from_text_fallback=True,
                memory_confirmed=t in known,
            )
            if c and c.name not in candidates:
                candidates[c.name] = c

    pipeline.candidate_names_seen = len(candidates)
    pipeline.candidates_after_nav_filter = len(candidates)
    return candidates, pipeline


def parse_projects_from_page(
    page: Any,
    *,
    known_projects: list[str] | None = None,
    memory_context: dict[str, dict[str, Any]] | None = None,
    page_url: str = "",
    page_title: str = "",
) -> ParseProjectsResult:
    known_set = {k.lower() for k in (known_projects or [])}
    mem_ctx = memory_context or {}
    body_text = _body_text(page)
    candidates, pipeline = _collect_candidates_from_page(page, known_projects=known_set)

    for name in known_set:
        if name in candidates:
            pipeline.known_memory_matches += 1

    buckets = bucket_candidates(candidates)
    pipeline.confirmed_projects = len(buckets.confirmed)
    pipeline.likely_projects = len(buckets.likely)
    pipeline.low_confidence_ignored = len(buckets.low_confidence) + len(buckets.ignored)
    pipeline.candidates_after_confidence = len(buckets.confirmed) + len(buckets.likely)

    for c in buckets.confirmed + buckets.likely + buckets.low_confidence:
        pipeline.filtered_candidates.append(
            {
                "name": c.name,
                "score": c.score,
                "signals": c.signals,
                "href": (c.href or "")[:160],
            }
        )
    for c in buckets.low_confidence:
        pipeline.rejection_reasons.append(
            {"name": c.name, "reason": f"low_confidence score={c.score}"}
        )

    confirmed_projects = [
        _candidate_to_project(
            c,
            bucket="confirmed",
            memory_entry=mem_ctx.get(c.name),
        )
        for c in buckets.confirmed
    ]
    likely_projects = [
        _candidate_to_project(
            c,
            bucket="likely",
            memory_entry=mem_ctx.get(c.name),
        )
        for c in buckets.likely
    ]
    projects = confirmed_projects + likely_projects
    dedupe_shared_production_urls(projects)

    ignored = [c.name for c in buckets.low_confidence] + buckets.ignored
    method = "dom_semantic" if any(c.from_dom for c in buckets.confirmed + buckets.likely) else (
        "text_filtered" if projects else "none"
    )

    memory_fallback = False
    memory_fallback_names: list[str] = []

    if not projects and known_set:
        memory_fallback = True
        memory_fallback_names = sorted(known_set)
        projects = [
            VercelProject(
                name=n,
                status="active",
                deployment_status="memory_fallback",
                attention_reason="stale — needs refresh",
                environment="memory",
            )
            for n in memory_fallback_names
        ]
        method = "operational_memory_fallback"
        pipeline.known_memory_matches = len(memory_fallback_names)

    return ParseProjectsResult(
        projects=projects,
        likely_projects=likely_projects,
        ignored_labels=sorted(set(ignored))[:40],
        extraction_method=method,
        low_confidence_count=len(ignored),
        pipeline=pipeline,
        memory_fallback=memory_fallback,
        memory_fallback_names=memory_fallback_names,
    )


def build_extraction_debug(
    *,
    page_url: str,
    page_title: str,
    parsed: ParseProjectsResult,
    visible_text_excerpt: str,
    known_memory_projects: list[str],
) -> dict[str, Any]:
    p = parsed.pipeline
    return {
        "current_url": page_url,
        "page_title": page_title,
        "candidate_count": p.candidate_names_seen,
        "raw_link_count": p.raw_links_seen,
        "project_like_link_count": p.project_like_links_seen,
        "filtered_candidates": p.filtered_candidates[:30],
        "rejection_reasons": p.rejection_reasons[:30],
        "known_memory_projects": known_memory_projects,
        "visible_text_excerpt": (visible_text_excerpt or "")[:2000],
        "pipeline": {
            "raw_links_seen": p.raw_links_seen,
            "project_like_links_seen": p.project_like_links_seen,
            "candidate_names_seen": p.candidate_names_seen,
            "candidates_after_nav_filter": p.candidates_after_nav_filter,
            "candidates_after_confidence": p.candidates_after_confidence,
            "confirmed_projects": p.confirmed_projects,
            "likely_projects": p.likely_projects,
            "low_confidence_ignored": p.low_confidence_ignored,
            "known_memory_matches": p.known_memory_matches,
            "dashboard_ready": p.dashboard_ready,
            "dashboard_ready_signal": p.dashboard_ready_signal,
        },
        "memory_fallback": parsed.memory_fallback,
        "extraction_method": parsed.extraction_method,
    }


def _body_text(page: Any) -> str:
    try:
        return page.locator("body").inner_text(timeout=8_000) or ""
    except Exception:
        try:
            return page.inner_text("body") or ""
        except Exception:
            return ""
