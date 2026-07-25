# SPDX-License-Identifier: Apache-2.0
"""Vercel platform semantic layer — entities, DOM parsing, health, summaries."""

from aethos_core.browser.platforms.vercel.vercel_entities import (
    HealthState,
    InfrastructureHealthSummary,
    VercelInventoryArtifact,
    VercelProject,
)
from aethos_core.browser.platforms.vercel.vercel_inventory_builder import (
    build_chat_summary_bullets,
    build_full_inventory_report,
    build_inventory_artifact,
    build_inventory_from_page,
    build_operational_summary,
)
from aethos_core.browser.platforms.vercel.vercel_navigation_map import (
    is_nav_label,
    is_plausible_project_name,
    is_platform_feature_slug,
)

__all__ = [
    "HealthState",
    "InfrastructureHealthSummary",
    "VercelInventoryArtifact",
    "VercelProject",
    "build_chat_summary_bullets",
    "build_full_inventory_report",
    "build_inventory_artifact",
    "build_inventory_from_page",
    "build_operational_summary",
    "is_nav_label",
    "is_plausible_project_name",
    "is_platform_feature_slug",
]
