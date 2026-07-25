# SPDX-License-Identifier: Apache-2.0
"""FIX 134 — Mission Control UI action safety contract."""

from __future__ import annotations

from typing import Final

ACTION_SAFETY_SCHEMA_VERSION: Final[str] = "mission_control_action_safety_v1"
ACTION_SAFETY_FIX: Final[str] = "FIX 134"

# Mission Control UI approval path must only invoke chat governance — never provider SDKs.
FORBIDDEN_DIRECT_PROVIDER_CALLS: Final[tuple[str, ...]] = (
    "open_governed_pull_request",
    "push_governed_branch_to_github",
    "github_git_mutation",
    "railway_execution",
    "approve_mutation_execution",
    "execute_governed_mutation",
    "dispatch_provider_mutation",
)

REQUIRED_UI_APPROVAL_ENTRYPOINT: Final[str] = "resolve_chat_turn"

FORBIDDEN_MC_UI_CONTROLS_FIX_134: Final[tuple[str, ...]] = (
    "deploy",
    "restart",
    "execute_mutation",
    "merge",
    "railway_mutation",
    "provider_mutation_bypass",
)
