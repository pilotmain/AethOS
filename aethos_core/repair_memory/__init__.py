# SPDX-License-Identifier: Apache-2.0
"""Repair memory — learn from post-mutation verification outcomes."""

from aethos_core.repair_memory.historical_repair_lookup import (
    lookup_latest_failed_restart,
    should_avoid_repeat_restart,
)
from aethos_core.repair_memory.outcome_recorder import record_verification_outcome
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome, reset_repair_memory_for_tests
from aethos_core.repair_memory.recommendation_guard import (
    compose_did_restart_help_reply,
    compose_next_step_with_repair_guard,
    compose_restart_again_reply,
    should_block_restart_recommendation,
)
from aethos_core.repair_memory.repair_outcome_router import (
    compose_repair_outcome_route_reply,
    find_latest_repair_outcome_for_context,
    is_repair_outcome_question,
    repair_outcome_preemption_blocks_route,
    route_repair_outcome_question,
)

__all__ = [
    "RepairAttemptOutcome",
    "compose_did_restart_help_reply",
    "compose_next_step_with_repair_guard",
    "compose_repair_outcome_route_reply",
    "compose_restart_again_reply",
    "find_latest_repair_outcome_for_context",
    "is_repair_outcome_question",
    "lookup_latest_failed_restart",
    "record_verification_outcome",
    "repair_outcome_preemption_blocks_route",
    "reset_repair_memory_for_tests",
    "route_repair_outcome_question",
    "should_avoid_repeat_restart",
    "should_block_restart_recommendation",
]
