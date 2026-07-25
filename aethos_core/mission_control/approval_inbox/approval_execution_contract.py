# SPDX-License-Identifier: Apache-2.0
"""FIX 133 — Mission Control governed UI approval execution contract."""

from __future__ import annotations

from typing import Final

APPROVAL_EXECUTION_SCHEMA_VERSION: Final[str] = "mission_control_approval_execution_v1"
APPROVAL_EXECUTION_FIX: Final[str] = "FIX 133"

# UI may trigger chat-routed approvals only — never direct provider mutation.
UI_APPROVAL_ORIGIN: Final[str] = "mission_control_approval_inbox"
UI_APPROVAL_CHANNEL: Final[str] = "mission_control_ui"
CHAT_GOVERNANCE_REQUIRED: Final[bool] = True

# Gates that couple approval phrases to GitHub mutation in one command stay view-only in UI.
UI_INELIGIBLE_GATE_IDS: Final[frozenset[str]] = frozenset(
    {
        "branch_push_completed",
        "github_pr_opened",
    }
)

# Job mutation approvals are out of scope for FIX 133 (no Railway / execute controls).
UI_INELIGIBLE_LANES: Final[frozenset[str]] = frozenset({"governed_execution"})

UI_ELIGIBLE_GATE_IDS: Final[frozenset[str]] = frozenset(
    {
        "planning_approved",
        "branch_create",
        "patch_proposal_approved",
        "workspace_apply",
        "github_preflight_approved",
    }
)


def ui_approval_eligible(*, lane: str, gate_id: str) -> bool:
    if lane in UI_INELIGIBLE_LANES:
        return False
    if gate_id in UI_INELIGIBLE_GATE_IDS:
        return False
    return gate_id in UI_ELIGIBLE_GATE_IDS
