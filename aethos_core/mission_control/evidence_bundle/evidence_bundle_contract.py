# SPDX-License-Identifier: Apache-2.0
"""FIX 136 — evidence bundle export contract (read-only)."""

from __future__ import annotations

from typing import Final

EVIDENCE_BUNDLE_SCHEMA_VERSION: Final[str] = "mission_control_evidence_bundle_v1"
EVIDENCE_BUNDLE_FIX: Final[str] = "FIX 136"
MUTATION_PERFORMED_FIX_136: Final[bool] = False

EVIDENCE_BUNDLE_SECTIONS: Final[tuple[str, ...]] = (
    "mission",
    "timeline",
    "receipts",
    "approvals",
    "blockers",
    "verification",
    "audit",
    "lane_drilldowns",
    "jobs",
    "job_evidence",
    "operation_lifecycle",
    "incident_links",
)
