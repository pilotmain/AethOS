# SPDX-License-Identifier: Apache-2.0
"""Navigation truth alignment — operator-visible workflow labels only."""

from __future__ import annotations

import pytest

from aethos_core.chat.handlers import resolve_handler
from aethos_core.config import get_settings
from aethos_core.jobs.job_approval_guidance import (
    compose_job_approval_guidance_reply,
    mutation_approval_surface,
)
from aethos_core.mission_control.visible_navigation_registry import (
    CAPABILITY_TRUTH,
    HIDDEN_INTERNAL_PANELS,
    REAL_OPERATOR_SURFACES,
    capability_truth,
    contains_hidden_navigation_leakage,
    is_capability_enabled,
    render_capability_truth_lines,
    resolve_visible_navigation_path,
    sanitize_operator_navigation_copy,
    visible_navigation_registry,
    where_is,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import JobStatus, job_store


@pytest.fixture(autouse=True)
def _mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def setup_function() -> None:
    job_store.clear_for_tests()


def test_mutation_approval_maps_to_approvals_inbox():
    path = resolve_visible_navigation_path(internal_surface="Operation Preflights", mode="operator")
    assert path == "Mission Control → Approvals"
    assert "Operation Preflights" not in path


def test_registry_lists_operator_visible_operations():
    reg = visible_navigation_registry(mode="operator")
    assert "Runtime actions" in reg["operator_visible_operations"]
    assert "Operation Preflights" in reg["hidden_internal_panels"]


def test_sanitize_replaces_hidden_labels():
    raw = "Approve in Mission Control → Operations → Operation Preflights"
    cleaned = sanitize_operator_navigation_copy(raw)
    assert "Operation Preflights" not in cleaned
    assert "Approvals" in cleaned


def test_compose_approval_reply_has_no_hidden_leakage():
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={"provider": "railway", "operation_type": "restart", "target_name": "atlas-trader api"},
        source="test",
        session_id="nav-truth",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = JobStatus.COMPLETED
    stored.params["preflight_status"] = "ready_for_mutation_approval"
    stored.params["mutation_preflight"] = {
        "provider": "railway",
        "operation_type": "restart",
        "preflight_status": "ready_for_mutation_approval",
    }
    stored.params["is_current"] = True

    reply = compose_job_approval_guidance_reply(f"where do i approve {job.id}?", session_id="nav-truth")
    assert reply is not None
    assert not contains_hidden_navigation_leakage(reply)
    assert mutation_approval_surface() in reply
    for label in HIDDEN_INTERNAL_PANELS:
        if label in ("tracked-work", "operation-preflights"):
            continue
        assert label.lower() not in reply.lower()


def test_capability_truth_only_references_real_surfaces():
    """§A3: every capability points at a surface that actually exists."""
    for cap_id, row in CAPABILITY_TRUTH.items():
        assert row["surface"] in REAL_OPERATOR_SURFACES, f"{cap_id} → fake surface {row['surface']!r}"
        assert row["env_var"].isupper(), cap_id


def test_where_is_names_the_real_flag_and_surface():
    line = where_is("canvas")
    assert "Canvas tab" in line
    assert "CANVAS_SURFACE_ENABLED" in line
    assert where_is("nonexistent_capability") == ""


def test_is_capability_enabled_reflects_actual_flag_state(monkeypatch):
    monkeypatch.setenv("CANVAS_SURFACE_ENABLED", "true")
    get_settings.cache_clear()
    assert is_capability_enabled("canvas") is True
    monkeypatch.setenv("CANVAS_SURFACE_ENABLED", "false")
    get_settings.cache_clear()
    assert is_capability_enabled("canvas") is False
    assert is_capability_enabled("unknown") is None
    get_settings.cache_clear()


def test_truth_block_marks_disabled_with_real_env_var(monkeypatch):
    monkeypatch.setenv("CANVAS_SURFACE_ENABLED", "false")
    get_settings.cache_clear()
    lines = "\n".join(render_capability_truth_lines())
    assert "Where things are done" in lines
    assert "CANVAS_SURFACE_ENABLED=true in .env" in lines
    # the block explicitly disowns any in-app settings page for flags
    assert "no in-app/mission control settings page for flags" in lines.lower()
    get_settings.cache_clear()


def test_capability_truth_lookup():
    assert capability_truth("agent_runtime")["env_var"] == "AGENT_RUNTIME_ENABLED"
    assert capability_truth("missing") is None


def test_chat_handler_uses_visible_labels():
    get_settings.cache_clear()
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={"provider": "railway", "operation_type": "restart"},
        source="test",
        session_id="nav-truth-chat",
        auto_run=False,
    )
    stored = job_store.get(job.id)
    assert stored is not None
    stored.status = JobStatus.COMPLETED
    stored.params["preflight_status"] = "ready_for_mutation_approval"
    stored.params["is_current"] = True
    stored.params["target_resolved"] = True
    stored.params["target_name"] = "atlas-trader api"

    packed = resolve_handler(f"where do i approve {job.id}?", session_id="nav-truth-chat")
    assert packed is not None
    reply = packed[0]
    assert "Operation Preflights" not in reply
    assert "Approvals" in reply
    assert "Approve Governed Mutation" in reply
