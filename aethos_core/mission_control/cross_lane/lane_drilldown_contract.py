# SPDX-License-Identifier: Apache-2.0
"""FIX 131 — Mission Control lane drilldown contract (read-only introspection)."""

from __future__ import annotations

from typing import Final

LANE_DRILLDOWN_SCHEMA_VERSION: Final[str] = "mission_control_lane_drilldown_v1"
LANE_DRILLDOWN_FIX: Final[str] = "FIX 131"
MUTATION_PERFORMED_FIX_131: Final[bool] = False
LANE_MUTATION_ENABLED_FIX_131: Final[bool] = False

DRILLDOWN_SECTION_KINDS: Final[tuple[str, ...]] = (
    "key_value",
    "gate_list",
    "approval_list",
    "timeline",
    "receipt_list",
    "verification_evidence",
    "rollback_posture",
    "blocker_list",
    "execution_contract",
    "agent_findings",
    "audit_trail",
    "record_list",
)
