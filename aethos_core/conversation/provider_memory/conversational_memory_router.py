# SPDX-License-Identifier: Apache-2.0
"""Conversational memory router — provider-generic follow-up before passive thread lock."""

from __future__ import annotations

from aethos_core.conversation.provider_memory.followup_intent_classifier import classify_followup_intent, is_operational_followup_request
from aethos_core.conversation.provider_memory.provider_followup_runtime import (
    compose_followup_reply,
    get_active_operational_thread,
    handle_provider_followup,
)


def is_provider_followup_request(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import should_yield_active_thread_for_readonly

    if should_yield_active_thread_for_readonly(text):
        return False

    from aethos_core.failed_service_investigation.global_preemption import should_preempt_to_failed_service
    from aethos_core.operational_planner.planner_router import should_override_active_thread
    from aethos_core.repair_memory.repair_outcome_router import is_repair_outcome_question

    if is_repair_outcome_question(text):
        return False
    if should_preempt_to_failed_service(text, session_id=session_id):
        return False
    if should_override_active_thread(text, session_id=session_id):
        return False
    return is_operational_followup_request(text, session_id=session_id)


def compose_provider_followup_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.post_mutation_verification.global_verification_preemption import (
        verification_preemption_blocks_route,
    )

    if verification_preemption_blocks_route(text, session_id=session_id):
        return None

    from aethos_core.repair_memory.repair_outcome_router import repair_outcome_preemption_blocks_route

    if repair_outcome_preemption_blocks_route(text, session_id=session_id):
        return None

    result = handle_provider_followup(session_id=session_id, user_text=text)
    if result is None or not result.body:
        return None
    return compose_followup_reply(result)


def should_route_provider_followup(text: str, *, session_id: str = "default") -> bool:
    thread = get_active_operational_thread(session_id)
    if thread is None:
        return False
    return classify_followup_intent(text, thread) is not None
