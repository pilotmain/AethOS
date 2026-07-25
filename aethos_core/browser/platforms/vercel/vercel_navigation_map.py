# SPDX-License-Identifier: Apache-2.0
"""Vercel dashboard navigation and product chrome — never treat as deployable projects."""

from __future__ import annotations

import re

# Sidebar / top nav / dashboard sections
KNOWN_VERCEL_NAV_LABELS = frozenset(
    {
        "projects",
        "project",
        "deployments",
        "deployment",
        "logs",
        "log",
        "analytics",
        "observability",
        "firewall",
        "storage",
        "usage",
        "upgrade",
        "support",
        "settings",
        "setting",
        "overview",
        "dashboard",
        "team",
        "teams",
        "account",
        "domains",
        "domain",
        "integrations",
        "integration",
        "activity",
        "notifications",
        "notification",
        "billing",
        "members",
        "member",
        "security",
        "feedback",
        "docs",
        "documentation",
        "help",
        "search",
        "filter",
        "sort",
        "new",
        "create",
        "add",
        "import",
        "template",
        "templates",
        "home",
        "menu",
        "more",
        "all",
        "recent",
        "favorites",
        "starred",
        "vercel",
        "github",
        "gitlab",
        "bitbucket",
        "hobby",
        "pro",
        "enterprise",
        "networking",
        "cron",
        "jobs",
        "ai",
        "edge",
        "monitoring",
        "speed",
        "insights",
        "web",
        "flags",
        "experimentation",
        "queues",
        "postgres",
        "kv",
        "redis",
    }
)

# Vercel product areas linked from dashboard — not user apps
PLATFORM_FEATURE_SLUGS = frozenset(
    {
        "workflows",
        "blob-storage",
        "blob",
        "ai-gateway",
        "ai",
        "edge-config",
        "edge",
        "speed-insights",
        "web-analytics",
        "analytics",
        "observability",
        "firewall",
        "storage",
        "postgres",
        "kv",
        "redis",
        "queues",
        "cron-jobs",
        "integrations",
        "domains",
        "activity",
        "usage",
        "support",
        "settings",
        "account",
        "notifications",
        "members",
        "security",
        "billing",
        "templates",
        "import",
        "new",
        "solutions",
        "contact",
        "docs",
        "help",
        "monitoring",
        "flags",
        "experimentation",
        "v0",
        "toolbar",
        "toolbar-v2",
        "agent",
        "alerts",
        "changelog",
        "collections",
        "cdn",
        "sandboxes",
        "stores",
        "environment-variables",
    }
)

# Usage metrics / billing rows on dashboard — never projects
KNOWN_VERCEL_USAGE_METRIC_SLUGS = frozenset(
    {
        "blob-advanced-operations",
        "blob-data-transfer",
        "blob-storage",
        "networking-edge-requests",
        "networking-fast-data-transfer",
        "networking-fast-origin-transfer",
        "vercel-functions-fluid-cpu-duration",
        "vercel-functions-fluid-duration",
        "vercel-functions-invocations",
        "isr-reads",
        "isr-writes",
        "edge-requests",
        "fast-data-transfer",
        "fast-origin-transfer",
        "fluid-cpu-duration",
        "fluid-duration",
        "functions-invocations",
    }
)

_USAGE_METRIC_PREFIXES = (
    "vercel-functions-",
    "blob-",
    "networking-",
    "edge-requests",
    "fast-data-",
    "fluid-",
    "isr-",
)

_SKIP_HREF_SEGMENTS = frozenset(
    {
        "dashboard",
        "settings",
        "account",
        "login",
        "signup",
        "new",
        "teams",
        "docs",
        "help",
        "support",
        "billing",
        "integrations",
        "domains",
        "activity",
        "notifications",
        "import",
        "templates",
        "solutions",
        "contact",
        "legal",
        "privacy",
        "terms",
        "storage",
        "ai",
        "edge",
        "observability",
        "analytics",
        "firewall",
        "usage",
        "workflows",
    }
)

_PROJECT_NAME_RX = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}$")

_PROJECT_SUBPAGES = frozenset(
    {
        "settings",
        "deployments",
        "deployment",
        "analytics",
        "domains",
        "logs",
        "log",
        "usage",
        "storage",
        "environment-variables",
        "integrations",
        "git",
        "overview",
        "functions",
        "cron",
        "observability",
        "firewall",
        "activity",
        "stores",
        "security",
        "members",
    }
)

# Prefer project list regions before generic links
PROJECT_CARD_SELECTORS = (
    '[data-testid*="project"] a[href]',
    '[data-testid="projects-section"] a[href]',
    'main [class*="project"] a[href]',
    'main a[href*="/"][href*="vercel.com"]',
    'a[href*="/"][href*="vercel.com"]',
    'main a[href^="/"]',
)

DEPLOYMENT_ROW_SELECTORS = (
    '[data-testid*="deployment"]',
    '[class*="deployment"]',
)


def is_nav_label(name: str) -> bool:
    return (name or "").strip().lower() in KNOWN_VERCEL_NAV_LABELS


def is_platform_feature_slug(name: str) -> bool:
    raw = (name or "").strip().lower()
    if raw in PLATFORM_FEATURE_SLUGS:
        return True
    if raw.endswith("-storage") or raw.endswith("-gateway") or raw.endswith("-analytics"):
        return True
    return False


def is_usage_metric_slug(name: str) -> bool:
    raw = (name or "").strip().lower()
    if raw in KNOWN_VERCEL_USAGE_METRIC_SLUGS:
        return True
    return any(raw.startswith(p) for p in _USAGE_METRIC_PREFIXES)


def is_plausible_project_name(name: str) -> bool:
    raw = (name or "").strip().lower()
    if not raw or is_nav_label(raw) or is_platform_feature_slug(raw) or is_usage_metric_slug(raw):
        return False
    if raw in _SKIP_HREF_SEGMENTS:
        return False
    if not _PROJECT_NAME_RX.match(raw):
        return False
    if raw.isdigit():
        return False
    return True


def _href_path_segments(href: str) -> list[str]:
    raw = (href or "").strip().split("?")[0].split("#")[0].rstrip("/")
    if raw.startswith("http"):
        try:
            from urllib.parse import urlparse

            raw = urlparse(raw).path or ""
        except Exception:
            pass
    if raw.startswith("/"):
        raw = raw[1:]
    return [p.lower() for p in raw.split("/") if p]


def _is_product_href(href: str) -> bool:
    low = (href or "").lower()
    if "/~/" in low or "/~/usage" in low or "/~/settings" in low:
        return True
    if "/usage" in low and "vercel.com" in low and "/projects" not in low:
        if any(x in low for x in ("/~/", "/usage?", "/usage#")):
            return True
    return False


def project_name_from_href(href: str) -> str | None:
    if not href or _is_product_href(href):
        return None

    parts = _href_path_segments(href)
    if not parts:
        return None

    if parts[0] in ("vercel.com", "www.vercel.com"):
        parts = parts[1:]

    if not parts:
        return None

    if parts[0].startswith("~") or any(p.startswith("~") for p in parts):
        return None

    if len(parts) >= 2:
        team, slug = parts[0], parts[1]
        if team in _SKIP_HREF_SEGMENTS or slug in _SKIP_HREF_SEGMENTS:
            return None
        if slug.startswith("~"):
            return None
        if len(parts) >= 3 and parts[2] in _PROJECT_SUBPAGES:
            if is_plausible_project_name(slug):
                return slug
            return None
        if parts[1] in _PROJECT_SUBPAGES and len(parts) >= 3:
            slug = parts[2]
            if is_plausible_project_name(slug):
                return slug
            return None
        if is_plausible_project_name(slug):
            return slug

    if len(parts) == 1:
        slug = parts[0]
        if slug in _PROJECT_SUBPAGES:
            return None
        if is_plausible_project_name(slug):
            return slug

    return None
