# SPDX-License-Identifier: Apache-2.0
"""Lazy lane hydration — hydrate only contexts required by the current prompt."""

from __future__ import annotations

import re
from time import perf_counter

from aethos_core.chat.route_timing import add_hydration_ms

_RAILWAY_RESTART_RX = re.compile(r"\b(?:restart|re-?deploy|rollback)\b", re.I)


def should_hydrate_browser_context(text: str) -> bool:
    from aethos_core.browser_observation.browser_observation_router import is_browser_observation_lane_intent

    return is_browser_observation_lane_intent(text)


def should_hydrate_railway_deployment_plan_context(text: str) -> bool:
    from aethos_core.providers.railway.deployment_plan.creation_preflight_intent import (
        is_railway_service_creation_preflight_intent,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_intent import (
        is_railway_new_service_plan_intent,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_intent import (
        is_railway_service_creation_simulator_intent,
    )

    return (
        is_railway_new_service_plan_intent(text)
        or is_railway_service_creation_preflight_intent(text)
        or is_railway_service_creation_simulator_intent(text)
    )


def should_hydrate_railway_restart_context(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.providers.github.workflow_lane.workflow_lane_guards import is_railway_mutation_context

    if not is_railway_mutation_context(text):
        return False
    if _RAILWAY_RESTART_RX.search(text or ""):
        return True
    from aethos_core.operational_thread_memory.followup_resolver import is_vague_operational_followup
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread

    if is_vague_operational_followup(text):
        thread = get_active_thread(session_id=session_id)
        if thread and str(thread.provider or "").lower() == "railway":
            return True
    return False


def maybe_hydrate_lane_contexts(*, text: str, session_id: str = "default") -> dict[str, int]:
    """Hydrate lane stores when needed; return per-lane hydration milliseconds."""
    raw = (text or "").strip()
    timings: dict[str, int] = {}

    if should_hydrate_browser_context(raw):
        started = perf_counter()
        from aethos_core.browser_observation.browser_observation_lifecycle import (
            hydrate_browser_observation_context,
        )

        hydrate_browser_observation_context(session_id=session_id)
        timings["browser"] = int((perf_counter() - started) * 1000)

    from aethos_core.providers.github.workflow_lane.workflow_lane_guards import (
        should_hydrate_github_workflow_context,
    )

    if should_hydrate_github_workflow_context(text=raw, session_id=session_id):
        started = perf_counter()
        from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
            hydrate_workflow_discovery_context,
        )
        from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import (
            hydrate_workflow_lane_context,
        )

        hydrate_workflow_discovery_context(session_id=session_id)
        hydrate_workflow_lane_context(session_id=session_id)
        timings["github_workflow"] = int((perf_counter() - started) * 1000)

    if should_hydrate_railway_deployment_plan_context(raw):
        started = perf_counter()
        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
            resolve_railway_deployment_lifecycle,
        )

        resolve_railway_deployment_lifecycle(session_id=session_id, user_text=raw)
        timings["railway_deployment_plan"] = int((perf_counter() - started) * 1000)

    if should_hydrate_railway_restart_context(raw, session_id=session_id):
        started = perf_counter()
        from aethos_core.operational_thread_memory.thread_persistence import get_active_thread

        get_active_thread(session_id=session_id)
        timings["railway_restart"] = int((perf_counter() - started) * 1000)

    total_hydration = sum(timings.values())
    if total_hydration:
        add_hydration_ms(total_hydration)
    return timings
