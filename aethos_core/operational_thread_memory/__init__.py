# SPDX-License-Identifier: Apache-2.0
"""Operational thread memory — post-mutation follow-up continuity."""

from aethos_core.operational_thread_memory.followup_resolver import is_vague_operational_followup, resolve_followup_intent
from aethos_core.operational_thread_memory.mutation_thread_memory import (
    find_execution_job_for_service,
    sync_thread_from_execution_job,
    sync_thread_from_preflight,
    sync_thread_on_approval,
)
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, get_active_thread
from aethos_core.operational_thread_memory.thread_reply_composer import compose_operational_thread_followup

__all__ = [
    "clear_threads_for_tests",
    "compose_operational_thread_followup",
    "get_active_thread",
    "is_vague_operational_followup",
    "resolve_followup_intent",
    "sync_thread_from_execution_job",
    "sync_thread_from_preflight",
    "sync_thread_on_approval",
    "find_execution_job_for_service",
]
