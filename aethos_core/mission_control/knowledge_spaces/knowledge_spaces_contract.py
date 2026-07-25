# SPDX-License-Identifier: Apache-2.0
"""FIX 141 — mission knowledge spaces contract (read-only semantic retrieval)."""

from __future__ import annotations

from typing import Final

KNOWLEDGE_SPACES_SCHEMA_VERSION: Final[str] = "mission_control_knowledge_spaces_v1"
KNOWLEDGE_SPACES_FIX: Final[str] = "FIX 141"
MUTATION_PERFORMED_FIX_141: Final[bool] = False
AUTONOMOUS_ACTION_ENABLED_FIX_141: Final[bool] = False
AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_141: Final[bool] = False

KNOWLEDGE_SPACES_ROUTE_ID: Final[str] = "mission_control_knowledge_spaces"

KNOWLEDGE_SPACES_INVARIANT: Final[str] = (
    "knowledge_spaces_are_read_only_semantic_retrieval_recommendation_only_no_autonomous_action"
)

KNOWLEDGE_DOCUMENT_CATEGORIES: Final[tuple[str, ...]] = (
    "mission",
    "incident",
    "blocker",
    "approval",
    "pr",
    "verification",
    "rerun_plan",
    "agent_finding",
    "rollout",
    "failure",
    "lifecycle",
)

DEFAULT_SEARCH_LIMIT: Final[int] = 20
SEEN_BEFORE_SCORE_THRESHOLD: Final[float] = 0.68
RELATED_MISSION_SCORE_THRESHOLD: Final[float] = 0.45
