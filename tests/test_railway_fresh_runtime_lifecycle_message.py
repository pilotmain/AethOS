# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 98L — fresh runtime lifecycle messaging when global index is empty."""

from __future__ import annotations

import json

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
    compose_fresh_runtime_lifecycle_reply,
    compose_no_plan_after_lifecycle_ensure,
    compose_session_lifecycle_materialization_failed_reply,
    is_fresh_runtime_lifecycle_state,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    _index_path,
    _store_dir,
    clear_for_tests as clear_lifecycle,
    save_lifecycle_record,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight import build_creation_preflight_from_plan
from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation
from aethos_core.providers.railway.service_creation_simulator.simulator_router import (
    route_railway_service_creation_simulator,
)


def setup_function() -> None:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
        clear_for_tests as clear_readiness,
    )

    clear_lifecycle()
    clear_readiness()


def test_empty_global_index_fresh_runtime_message() -> None:
    _store_dir()
    _index_path().write_text(
        json.dumps({"entries": [], "latest_lifecycle_id": "", "latest_by_repo": {}}),
        encoding="utf-8",
    )
    assert is_fresh_runtime_lifecycle_state() is True
    body = compose_no_plan_after_lifecycle_ensure(ensure_result="miss")
    assert "fresh runtime state" in body.lower()
    assert "lifecycle entries: **0**" in body
    assert "repair railway deployment lifecycle" not in body


def test_missing_global_index_fresh_runtime_message() -> None:
    assert is_fresh_runtime_lifecycle_state() is True
    body = compose_fresh_runtime_lifecycle_reply()
    assert "I don't have a Railway deployment lifecycle in this runtime yet" in body
    assert "global lifecycle index: **missing**" in body
    assert "simulate railway service creation" in body
    assert "repair railway deployment lifecycle" not in body


def test_index_with_entries_session_miss_suggests_repair() -> None:
    plan = apply_plan_review_confirmation(
        {
            "plan_id": "plan-98l",
            "repo": "pilotmain/aethos",
            "branch": "main",
            "project": "pilotos",
            "environment": "production",
            "service_name": "aethos-api",
            "mutation_ready": True,
        }
    )
    preflight = build_creation_preflight_from_plan(plan)
    save_lifecycle_record(
        session_id="98l-orig",
        record={
            "lifecycle_id": "rlc-98l",
            "session_id": "98l-orig",
            "repo": plan["repo"],
            "plan": {"exists": True, "mutation_ready": True, "review_confirmed": True, "snapshot": dict(plan)},
            "preflight": {"exists": True, "preflight_id": preflight["preflight_id"], "snapshot": dict(preflight)},
            "simulation": {"exists": False, "snapshot": {}},
        },
    )
    assert is_fresh_runtime_lifecycle_state() is False
    body = compose_session_lifecycle_materialization_failed_reply(ensure_result="miss")
    assert "repair railway deployment lifecycle" in body
    assert "fresh runtime state" not in body.lower()


def test_simulator_fresh_runtime_via_router() -> None:
    result = route_railway_service_creation_simulator(
        "simulate railway service creation",
        session_id="98l-fresh",
    )
    assert result is not None
    body, intent, meta = result
    assert intent == "railway_service_creation_simulation_not_ready"
    assert "fresh runtime state" in body.lower()
    assert "don't have a saved Railway deployment plan in this session" not in body
    assert meta.get("lifecycle_ensure_result") == "miss"
    assert meta.get("mutation_performed") == "false"
