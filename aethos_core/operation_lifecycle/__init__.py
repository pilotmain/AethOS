# SPDX-License-Identifier: Apache-2.0
"""Operation lifecycle — canonical mutation execution continuity."""

from aethos_core.operation_lifecycle.lifecycle_followup_router import (
    compose_lifecycle_followup_reply,
    is_lifecycle_followup_intent,
)
from aethos_core.operation_lifecycle.lifecycle_resolver import (
    get_latest_operation_state,
    has_completed_operation,
    has_recent_mutation_execution,
    is_blocked_by_credentials,
    is_duplicate_mutation_request,
    is_operation_verified,
    is_waiting_for_approval,
)
from aethos_core.operation_lifecycle.operation_state_store import (
    OperationLifecycleState,
    refresh_operation_state_for_session,
    upsert_operation_state_from_job,
)

__all__ = [
    "OperationLifecycleState",
    "compose_lifecycle_followup_reply",
    "get_latest_operation_state",
    "has_completed_operation",
    "has_recent_mutation_execution",
    "is_blocked_by_credentials",
    "is_duplicate_mutation_request",
    "is_lifecycle_followup_intent",
    "is_operation_verified",
    "is_waiting_for_approval",
    "refresh_operation_state_for_session",
    "upsert_operation_state_from_job",
]
