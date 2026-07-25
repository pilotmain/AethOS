# SPDX-License-Identifier: Apache-2.0
"""Backward-compatible re-exports — prefer aethos_core.browser.platforms.vercel."""

from aethos_core.browser.platforms.vercel import (
    HealthState,
    InfrastructureHealthSummary,
    VercelInventoryArtifact,
    VercelProject,
    build_chat_summary_bullets,
    build_full_inventory_report,
    build_inventory_artifact,
    build_operational_summary,
    is_nav_label,
    is_plausible_project_name,
)
from aethos_core.browser.platforms.vercel.vercel_inventory_builder import build_inventory_from_page
from aethos_core.browser.platforms.vercel.vercel_navigation_map import KNOWN_VERCEL_NAV_LABELS


def extract_projects_from_page(page):
    """Legacy API — returns (projects, method)."""
    artifact, method = build_inventory_from_page(page)
    return artifact.projects, method
