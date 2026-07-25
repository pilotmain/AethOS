# SPDX-License-Identifier: Apache-2.0
"""FIX 139 — operational memory substrate contract (read-only)."""

from __future__ import annotations

from typing import Final

OPERATIONAL_MEMORY_SCHEMA_VERSION: Final[str] = "mission_control_operational_memory_v1"
OPERATIONAL_MEMORY_FIX: Final[str] = "FIX 139"
MUTATION_PERFORMED_FIX_139: Final[bool] = False
AUTONOMOUS_ADAPTATION_ENABLED_FIX_139: Final[bool] = False

OPERATIONAL_MEMORY_ROUTE_ID: Final[str] = "mission_control_operational_memory"

OPERATIONAL_MEMORY_INVARIANT: Final[str] = (
    "operational_memory_is_read_only_no_autonomous_adaptation_until_explicit_future_fix"
)

OPERATIONAL_MEMORY_NODE_KINDS: Final[tuple[str, ...]] = (
    "mission",
    "job",
    "approval",
    "gate",
    "incident",
    "rollout",
    "pr",
    "replay_step",
    "verification",
    "rerun_plan",
    "agent_finding",
    "blocker",
    "lifecycle",
    "receipt",
)

OPERATIONAL_MEMORY_EDGE_KINDS: Final[tuple[str, ...]] = (
    "session_contains",
    "plan_governs",
    "job_in_session",
    "approval_for_gate",
    "audit_of_approval",
    "replay_of_timeline",
    "rerun_plan_targets",
    "incident_blocks",
    "rollout_observed",
    "dependency",
    "lineage",
    "correlates_with",
    "evidence_of",
)
