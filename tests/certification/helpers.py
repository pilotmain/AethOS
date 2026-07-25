# SPDX-License-Identifier: Apache-2.0
"""Certification helpers — provider isolation assertions and shared fixtures."""

from __future__ import annotations

import json
import re
from typing import Any

from aethos_core.chat.route_trace import clear_route_traces_for_tests
from aethos_core.chat.service import ChatTurnResult
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.operational_state.narrative import clear_operational_narrative_for_tests
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.workflow_creation.workflow_creation_context import (
    clear_for_tests as clear_creation_ctx,
)
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
)
from aethos_core.browser_observation.browser_observation_lifecycle import clear_lifecycle_for_tests as clear_browser_obs_lifecycle
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    clear_for_tests as clear_railway_creation_preflight,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    clear_for_tests as clear_railway_deployment_lifecycle,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
    clear_for_tests as clear_railway_service_creation_simulation,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import clear_for_tests as clear_railway_deployment_plan
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import clear_for_tests as clear_railway_deployment_readiness
from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import clear_lifecycle_for_tests
from aethos_core.providers.github.workflow_lane.workflow_lane_router import clear_for_tests as clear_lane
from aethos_core.response_composition.operational_result_store import clear_operational_results_for_tests
from aethos_core.runtime.jobs import job_store
from aethos_core.task_frame.pending_action import clear_pending_actions_for_tests
from aethos_core.task_frame.task_memory import clear_task_frames_for_tests

_FORBIDDEN_REPLY_MARKERS: dict[str, tuple[str, ...]] = {
    "github": (
        "no pending github workflow creation plan",
        "cannot access local variable 'discovery'",
        "governed workflow-file creation plan",
        "workflow discovery hydration",
        "start with `draft workflow proposal`",
    ),
    "railway": (
        "governed railway restart preflight",
        "creating a new governed railway",
        "pilotos / production / pilotos-api",
        "mutation preflight (governed execution)",
    ),
    "vercel": (
        "vercel why down",
        "vercel deployment is failing",
        "check vercel logs",
    ),
    "generic_capability": (
        "how i can help",
        "operational pathways",
        "tell me what you're working through",
    ),
    "browser_observation": (
        "i cannot take screenshots",
        "cannot take screenshots",
        "screenshots are not supported",
    ),
    "active_thread": (
        "active operational thread",
        "active thread was `",
        "continuing the active thread",
    ),
}

_FORBIDDEN_META_MARKERS: dict[str, tuple[str, ...]] = {
    "github": (
        "github_workflow_lane",
        "workflow_discovery",
        "github_workflow",
    ),
    "railway": (
        "retry_active_operation",
        "mutation_preflight",
        "explicit_mutation",
    ),
    "vercel": (
        "vercel_why_down",
        "vercel_readonly",
    ),
}


def reset_certification_runtime() -> None:
    """Clear volatile runtime state between certification scenarios."""
    import os

    os.environ["AETHOS_CERTIFICATION_MODE"] = "true"
    from aethos_core.operation_lifecycle.global_lifecycle_index import reset_global_lifecycle_index_for_tests
    from aethos_core.operation_lifecycle.operation_state_store import reset_operation_state_store_for_tests
    from aethos_core.post_mutation_verification.verification_intent_router import (
        reset_pending_verification_for_tests,
    )

    reset_global_lifecycle_index_for_tests()
    reset_operation_state_store_for_tests()
    reset_pending_verification_for_tests()
    clear_github_context_for_tests()
    clear_runtime_context_for_tests()
    clear_creation_ctx()
    clear_lane()
    clear_lifecycle_for_tests()
    clear_browser_obs_lifecycle()
    clear_railway_deployment_readiness()
    clear_railway_deployment_plan()
    clear_railway_creation_preflight()
    clear_railway_service_creation_simulation()
    clear_railway_deployment_lifecycle()
    from aethos_core.providers.railway.env_value_readiness.env_value_context import (
        clear_for_tests as clear_railway_env_value_readiness,
    )
    from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
        clear_deployment_env_presence_for_tests,
    )
    from aethos_core.providers.railway.env_value_readiness.env_rotation_metadata import (
        clear_rotation_metadata_for_tests,
    )

    clear_railway_env_value_readiness()
    clear_deployment_env_presence_for_tests()
    clear_rotation_metadata_for_tests()
    from aethos_core.operational_planner.adapters.railway_wide_health_cache import clear_cache_for_tests

    clear_cache_for_tests()
    clear_route_traces_for_tests()
    clear_provider_wide_health_for_tests()
    clear_operational_results_for_tests()
    clear_operational_narrative_for_tests()
    clear_threads_for_tests()
    clear_pending_actions_for_tests()
    clear_task_frames_for_tests()
    job_store.clear_for_tests()


def assert_route_did_not_call_provider(
    result: ChatTurnResult,
    forbidden_provider: str,
    *,
    allow_markers: tuple[str, ...] = (),
) -> None:
    """Assert a chat turn did not route into a forbidden provider family."""
    key = forbidden_provider.strip().lower()
    reply = (result.reply or "").lower()
    meta = dict(result.meta or {})
    meta.pop("blocked_routes", None)
    meta_blob = " ".join(str(v).lower() for v in {"intent": result.intent, **meta}.values())

    for marker in _FORBIDDEN_REPLY_MARKERS.get(key, ()):
        if marker in allow_markers:
            continue
        assert marker not in reply, (
            f"Forbidden reply marker {marker!r} for provider {forbidden_provider!r} "
            f"(intent={result.intent!r})"
        )

    for marker in _FORBIDDEN_META_MARKERS.get(key, ()):
        if marker in allow_markers:
            continue
        assert marker not in meta_blob, (
            f"Forbidden meta marker {marker!r} for provider {forbidden_provider!r} "
            f"(meta={result.meta!r})"
        )


def assert_route_owns(
    result: ChatTurnResult,
    *,
    route_id: str | None = None,
    intent: str | None = None,
    matched_module: str | None = None,
) -> None:
    if route_id is not None:
        assert str(result.meta.get("route_id") or "") == route_id, result.meta
    if intent is not None:
        assert result.intent == intent, result.intent
    if matched_module is not None:
        assert matched_module in str(result.meta.get("matched_module") or ""), result.meta


def assert_no_generic_capability_prose(result: ChatTurnResult) -> None:
    assert_route_did_not_call_provider(result, "generic_capability")


def assert_json_payload_valid(text: str) -> dict[str, Any]:
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    raw = fence.group(1).strip() if fence else text.strip()
    payload = json.loads(raw)
    assert isinstance(payload, dict)
    return payload
