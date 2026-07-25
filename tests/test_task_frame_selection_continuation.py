# SPDX-License-Identifier: Apache-2.0
"""Task frame selection continuation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.runtime.jobs import job_store
from aethos_core.task_frame.clarification_state import store_target_selection_task
from aethos_core.task_frame.selection_resolver import resolve_selection
from aethos_core.task_frame.task_expiration import task_expires_at
from aethos_core.task_frame.task_frame import TaskCandidate, TaskFrame
from aethos_core.task_frame.task_memory import clear_task_frames_for_tests, get_active_task_frame


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_task_frames_for_tests()
    job_store.clear_for_tests()
    yield
    clear_task_frames_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _candidates():
    return [
        {"project_name": "atlas-trader", "environment": "production", "service_name": "api", "service_id": "svc-1"},
        {"project_name": "lifeos", "environment": "production", "service_name": "api", "service_id": "svc-2"},
        {
            "project_name": "influencer-crm",
            "environment": "production",
            "service_name": "influencer-crm",
            "service_id": "svc-3",
        },
    ]


def test_user_selects_number_three():
    frame = store_target_selection_task(
        session_id="tf-select",
        provider="railway",
        operation="restart",
        original_request="restart the railway influencer-crm api service",
        candidates=_candidates(),
    )
    selected = resolve_selection("3", frame)
    assert selected is not None
    assert selected.project == "influencer-crm"
    assert selected.service == "influencer-crm"


def test_user_selects_copied_option_text():
    frame = store_target_selection_task(
        session_id="tf-copy",
        provider="railway",
        operation="restart",
        original_request="restart railway",
        candidates=_candidates(),
    )
    selected = resolve_selection("3. influencer-crm / production / influencer-crm", frame)
    assert selected is not None
    assert selected.index == 3


def test_stale_task_frame_expires():
    frame = TaskFrame(
        session_id="tf-stale",
        task_id="tf-expired",
        intent="provider_restart",
        provider="railway",
        operation="restart",
        status="awaiting_target_selection",
        candidates=[TaskCandidate(index=1, project="p", environment="production", service="api")],
        expires_at="2020-01-01T00:00:00+00:00",
    )
    from aethos_core.task_frame.task_memory import save_task_frame

    save_task_frame(frame)
    assert get_active_task_frame(session_id="tf-stale") is None


def test_wrong_selection_asks_again():
    from aethos_core.task_frame.task_continuation import compose_task_continuation_reply

    store_target_selection_task(
        session_id="tf-wrong",
        provider="railway",
        operation="restart",
        original_request="restart railway",
        candidates=_candidates(),
    )
    reply = compose_task_continuation_reply("99", session_id="tf-wrong")
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "task_frame_selection_invalid"
    assert "couldn't match" in body.lower()


def test_selection_creates_preflight_no_generic_fallback(monkeypatch):
    from aethos_core.api.main import app

    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    store_target_selection_task(
        session_id="tf-flow",
        provider="railway",
        operation="restart",
        original_request="restart the railway influencer-crm api service",
        candidates=_candidates(),
        params={"provider": "railway", "operation_type": "restart"},
    )
    client = TestClient(app)
    response = client.post(
        "/api/v1/chat",
        json={"message": "3. influencer-crm / production / influencer-crm", "session_id": "tf-flow"},
    )
    body = response.json()
    assert body.get("intent") == "task_frame_preflight_created"
    assert "influencer-crm / production / influencer-crm" in body["reply"]
    assert "preflight" in body["reply"].lower()
    assert get_active_task_frame(session_id="tf-flow") is None
