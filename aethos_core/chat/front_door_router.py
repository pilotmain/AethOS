# SPDX-License-Identifier: Apache-2.0
"""Front-door routing handler."""

from __future__ import annotations

from aethos_core.chat.front_door_intent import (
    classify_front_door_intent,
    compose_front_door_reply,
    should_skip_operational_cognition,
)


def compose_front_door_route_reply(
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

    from aethos_core.world_model.investigation_strategy_router import investigation_strategy_preemption_blocks_route

    if investigation_strategy_preemption_blocks_route(text, session_id=session_id):
        return None

    intent = classify_front_door_intent(text, session_id=session_id)
    if not should_skip_operational_cognition(text, intent=intent):
        return None
    return compose_front_door_reply(intent, text=text, session_id=session_id)
