# SPDX-License-Identifier: Apache-2.0
"""Extract production URLs — project-card scope only; no page-level smearing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from aethos_core.browser.platforms.vercel.vercel_url_classifier import (
    classify_url_type,
    url_type_rank,
)

_VERCEL_APP_RX = re.compile(
    r"https?://([a-z0-9][a-z0-9_-]*)\.vercel\.app",
    re.I,
)
_VERCEL_APP_BARE_RX = re.compile(
    r"\b([a-z0-9][a-z0-9_-]*)\.vercel\.app\b",
    re.I,
)
_HTTPS_URL_RX = re.compile(
    r"https?://[a-z0-9][\w.-]*\.[a-z]{2,}(?:/[^\s]*)?",
    re.I,
)
_CUSTOM_DOMAIN_RX = re.compile(
    r"\b([a-z0-9][\w.-]*\.(?:com|io|app|dev|net|org|co|ai|so|me|xyz|site|cloud|tools))\b",
    re.I,
)
_SKIP_DOMAINS = frozenset(
    {
        "vercel.com",
        "vercel.app",
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        "npmjs.com",
        "google.com",
        "gstatic.com",
    }
)

_CARD_SOURCES = frozenset(
    {
        "project_card",
        "project_card_domain",
        "custom_domain",
        "vercel_app_text",
        "vercel_app_link",
        "anchor_url",
        "production_badge",
        "project_href",
        "memory",
    }
)
_HIGH_CONFIDENCE_SOURCES = frozenset(
    {
        "project_card",
        "project_card_domain",
        "custom_domain",
        "project_href",
        "detail_page",
        "deployments_tab",
        "memory",
    }
)


@dataclass
class ProductionUrlMatch:
    url: str
    source: str
    confidence: str = "high"


def _normalize_url(raw: str) -> str:
    u = (raw or "").strip().rstrip(").,;]")
    if not u.startswith("http"):
        u = f"https://{u}"
    return u


def _domain_from_url(url: str) -> str:
    try:
        from urllib.parse import urlparse

        host = urlparse(url).netloc.lower()
        return host.removeprefix("www.")
    except Exception:
        return ""


def _is_usable_domain(host: str) -> bool:
    if not host or host in _SKIP_DOMAINS:
        return False
    if host.endswith(".vercel.app"):
        return True
    return "." in host


def _slug_matches_project(slug: str, name: str) -> bool:
    s = (slug or "").lower().replace("_", "-")
    n = (name or "").lower().replace("_", "-")
    if not s or not n:
        return False
    if s == n:
        return True
    if s.endswith(f"-{n}") or s.startswith(f"{n}-"):
        return True
    if n.endswith(f"-{s}") or n.startswith(f"{s}-"):
        return True
    return False


def _domain_matches_project(domain: str, name: str) -> bool:
    host = domain.lower()
    stem = host.split(".")[0]
    n = name.lower().replace("_", "-")
    if stem == n:
        return True
    if _slug_matches_project(stem, n):
        return True
    if len(n) >= 5 and n in stem:
        return True
    if host.endswith(".vercel.app"):
        return _slug_matches_project(stem, n)
    return False


def extract_urls_from_text(
    text: str,
    project_name: str,
    *,
    scope: str = "project_card",
) -> list[ProductionUrlMatch]:
    """URLs from project card text only — not whole-page body."""
    name = (project_name or "").lower()
    blob = text or ""
    matches: list[ProductionUrlMatch] = []
    seen: set[str] = set()

    def _add(url: str, source: str, confidence: str = "high") -> None:
        host = _domain_from_url(url)
        if not host or host in seen or not _is_usable_domain(host):
            return
        if not _domain_matches_project(host, name):
            return
        seen.add(host)
        matches.append(
            ProductionUrlMatch(url=_normalize_url(url), source=source, confidence=confidence)
        )

    for m in _VERCEL_APP_RX.finditer(blob):
        if _slug_matches_project(m.group(1).lower(), name):
            _add(m.group(0), "vercel_app_link")

    for m in _VERCEL_APP_BARE_RX.finditer(blob):
        if _slug_matches_project(m.group(1).lower(), name):
            _add(f"https://{m.group(0)}", "vercel_app_text")

    for m in _HTTPS_URL_RX.finditer(blob):
        host = _domain_from_url(m.group(0))
        if host and _domain_matches_project(host, name):
            _add(m.group(0), "anchor_url")

    for m in _CUSTOM_DOMAIN_RX.finditer(blob):
        domain = m.group(1).lower()
        if domain in _SKIP_DOMAINS:
            continue
        if _domain_matches_project(domain, name):
            conf = "high" if scope == "project_card" else "medium"
            _add(f"https://{domain}", "custom_domain", confidence=conf)

    return matches


def best_production_url(
    *,
    project_name: str,
    card_text: str = "",
    href: str | None = None,
    memory_url: str | None = None,
    allow_page_text: bool = False,
    page_text: str = "",
) -> tuple[str | None, str | None, str]:
    """Returns (url, source, confidence). Never uses page_text unless allow_page_text."""
    if memory_url:
        return _normalize_url(memory_url), "memory", "high"

    if href and ".vercel.app" in href:
        slug = href.split(".vercel.app")[0].split("/")[-1].lower()
        if _slug_matches_project(slug, project_name):
            return _normalize_url(href), "project_href", "high"

    matches = extract_urls_from_text(card_text, project_name, scope="project_card")
    if not matches and allow_page_text and page_text:
        matches = extract_urls_from_text(page_text, project_name, scope="page_fallback")

    if matches:
        matches.sort(
            key=lambda m: (
                url_type_rank(classify_url_type(m.url)),
                0 if m.confidence == "high" else 1,
            )
        )
        m = matches[0]
        return m.url, m.source, m.confidence
    return None, None, "none"


def confidence_for_source(source: str | None, *, verified: bool = False) -> str:
    if verified:
        return "high"
    if not source or source == "none":
        return "none"
    if source in _HIGH_CONFIDENCE_SOURCES:
        return "high"
    if source in _CARD_SOURCES:
        return "medium"
    return "low"


def dedupe_shared_production_urls(projects: list[Any]) -> None:
    """Clear URLs reused across unrelated projects (page-level smearing)."""
    by_url: dict[str, list[Any]] = {}
    for p in projects:
        url = getattr(p, "production_url", None)
        if url:
            by_url.setdefault(url, []).append(p)

    global_sources = frozenset({"page_text", "page_link", "domain_row", "page_fallback"})

    for url, group in by_url.items():
        if len(group) < 2:
            continue
        weak = [p for p in group if getattr(p, "production_url_source", "") in global_sources]
        if weak:
            for p in weak:
                p.production_url = None
                p.production_url_source = None
                p.production_url_confidence = "none"
            continue
        if len(group) >= 2:
            best = max(
                group,
                key=lambda p: (
                    1 if getattr(p, "production_url_verified", False) else 0,
                    1 if getattr(p, "production_url_confidence", "") == "high" else 0,
                ),
            )
            for p in group:
                if p is not best:
                    p.production_url = None
                    p.production_url_source = None
                    p.production_url_confidence = "none"
