# SPDX-License-Identifier: Apache-2.0
"""Solo greenfield deploy thread memory and status follow-up routing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.operational_thread_memory.solo_greenfield_thread_memory import (
    compose_greenfield_deployment_status_reply,
    sync_thread_from_solo_greenfield,
)
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, get_active_thread
from aethos_core.providers.railway.execution_contract.execution_journal import clear_for_tests as clear_journals_for_tests
from aethos_core.providers.railway.greenfield_deployment.deployment_status_followup_router import (
    is_railway_deployment_status_followup,
    route_railway_deployment_status_followup,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    clear_journals_for_tests()
    yield
    clear_threads_for_tests()
    clear_journals_for_tests()


def _sample_plan() -> dict:
    return {
        "project": "pilotos",
        "environment": "staging",
        "service_name": "aethos-api",
        "repo": "pilotmain/aethos",
        "branch": "main",
    }


def _sample_journal() -> dict:
    return {
        "execution_id": "rexec-test123",
        "session_id": "solo-status-test",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "aethos-api",
        "railway_service_id": "52736b80-baea-4b2a-be31-84d267b3a8cb",
        "railway_deployment_id": "37f7c3bc-871b-4c0c-8d18-92dc7421f37c",
        "runtime_verification_performed": True,
        "runtime_verification": {"verified": True, "ok": True},
    }


def test_solo_greenfield_sync_persists_active_thread():
    sync_thread_from_solo_greenfield(
        session_id="solo-status-test",
        user_text="Deploy AethOS to Railway with env vars and verify it.",
        plan=_sample_plan(),
        journal=_sample_journal(),
        execution_status="completed",
    )
    thread = get_active_thread(session_id="solo-status-test")
    assert thread is not None
    assert thread.active_thread == "railway_greenfield_deployment"
    assert thread.service == "aethos-api"
    assert thread.status == "deploy_live"


def test_status_update_routes_to_railway_deployment_not_e2e():
    sync_thread_from_solo_greenfield(
        session_id="solo-status-test",
        user_text="Deploy AethOS to Railway with env vars and verify it.",
        plan=_sample_plan(),
        journal=_sample_journal(),
        execution_status="completed",
    )
    assert is_railway_deployment_status_followup("status update please")

    with patch(
        "aethos_core.operational_thread_memory.solo_greenfield_thread_memory.poll_greenfield_deployment_status",
        return_value={
            "ok": True,
            "deployment_id": "37f7c3bc-871b-4c0c-8d18-92dc7421f37c",
            "state": "SUCCESS",
            "health_ok": True,
            "url": "https://aethos-api-staging.up.railway.app",
            "branch": "main",
            "commit": "ff320be",
            "error_message": "",
        },
    ):
        routed = route_railway_deployment_status_followup("status update please", session_id="solo-status-test")

    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_greenfield_deployment_status_followup"
    assert "pilotos" in body
    assert "aethos-api" in body
    assert "SUCCESS" in body
    assert meta["provider"] == "railway"


def test_railway_clarification_status_update_uses_thread():
    sync_thread_from_solo_greenfield(
        session_id="solo-status-test",
        user_text="Deploy AethOS to Railway with env vars and verify it.",
        plan=_sample_plan(),
        journal=_sample_journal(),
        execution_status="completed",
    )
    with patch(
        "aethos_core.operational_thread_memory.solo_greenfield_thread_memory.poll_greenfield_deployment_status",
        return_value={
            "ok": True,
            "deployment_id": "37f7c3bc-871b-4c0c-8d18-92dc7421f37c",
            "state": "SUCCESS",
            "health_ok": True,
            "url": "",
            "branch": "main",
            "commit": "",
            "error_message": "",
        },
    ):
        routed = route_railway_deployment_status_followup(
            "no im asking about aethos deployment in railway status update?",
            session_id="solo-status-test",
        )
    assert routed is not None
    body, intent, _meta = routed
    assert intent == "railway_greenfield_deployment_status_followup"
    assert "Railway deployment status" in body


def test_compose_status_reply_without_live_poll():
    thread = sync_thread_from_solo_greenfield(
        session_id="solo-status-test",
        user_text="Deploy AethOS to Railway with env vars and verify it.",
        plan=_sample_plan(),
        journal=_sample_journal(),
        execution_status="completed",
    )
    with patch(
        "aethos_core.operational_thread_memory.solo_greenfield_thread_memory.poll_greenfield_deployment_status",
        return_value={"ok": False, "detail": "offline"},
    ):
        body, intent, _meta = compose_greenfield_deployment_status_reply(thread=thread)
    assert intent == "railway_greenfield_deployment_status_followup"
    assert "offline" in body
