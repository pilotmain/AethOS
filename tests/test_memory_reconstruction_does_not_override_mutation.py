# SPDX-License-Identifier: Apache-2.0
"""Memory reconstruction must not override explicit mutation intent."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.aethos_identity.continuity_decision import compose_continuity_operational_reply
from aethos_core.chat.explicit_mutation_intent import compose_explicit_mutation_preflight_reply
from aethos_core.continuity_intelligence.operational_focus_model import clear_focus_for_tests
from aethos_core.config import get_settings
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests, save_thread_state
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState
from aethos_core.operational_thread_memory.thread_persistence import _expires_at
from aethos_core.runtime.jobs import job_store
from datetime import UTC, datetime


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_focus_for_tests()
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_focus_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _gate(text, params, operation_type):
    enriched = {
        **params,
        "target_name": "pilotos-api",
        "target_resolved": True,
        "target": {
            "project_name": "pilotos",
            "environment": "production",
            "service_name": "pilotos-api",
            "resolved": True,
        },
    }
    return enriched, None


def test_known_service_restart_is_mutation_not_continuity():
    binding = type("Binding", (), {"ok": True, "stored_github_repo": "", "referenced_github_repo": ""})()
    with patch("aethos_core.chat.mutation_target_chat.gate_railway_mutation_preflight", side_effect=_gate), patch(
        "aethos_core.provider_topology.binding_verifier.verify_source_binding",
        return_value=binding,
    ):
        mutation = compose_explicit_mutation_preflight_reply(
            "restart the railway pilotos-api",
            session_id="override-mutation",
        )
        continuity = compose_continuity_operational_reply(
            "restart the railway pilotos-api",
            session_id="override-mutation",
        )
    assert mutation is not None
    assert continuity is None
    assert mutation[1] == "mutation_preflight_job_created"


@patch("aethos_core.aethos_identity.continuity_decision._fetch_readonly_logs")
def test_known_service_logs_stays_readonly(mock_logs):
    mock_logs.return_value = [
        {"timestamp": "2026-05-20T12:00:00+00:00", "level": "INFO", "message": "ready"},
    ]
    mutation = compose_explicit_mutation_preflight_reply(
        "check logs for pilotos-api",
        session_id="override-readonly",
    )
    continuity = compose_continuity_operational_reply(
        "check logs for pilotos-api",
        session_id="override-readonly",
    )
    assert mutation is None
    assert continuity is not None
    assert continuity[1] == "continuity_readonly_logs"


def test_active_inspect_thread_plus_restart_is_mutation():
    save_thread_state(
        OperationalThreadState(
            session_id="inspect-plus-restart",
            provider="railway",
            project="pilotos",
            environment="production",
            service="pilotos-api",
            operation="inspect",
            status="reconstructed_from_topology",
            last_system_result="Reconstructed provider context.",
            updated_at=datetime.now(UTC).isoformat(),
            expires_at=_expires_at(),
        )
    )
    binding = type("Binding", (), {"ok": True, "stored_github_repo": "", "referenced_github_repo": ""})()
    with patch("aethos_core.chat.mutation_target_chat.gate_railway_mutation_preflight", side_effect=_gate), patch(
        "aethos_core.provider_topology.binding_verifier.verify_source_binding",
        return_value=binding,
    ):
        mutation = compose_explicit_mutation_preflight_reply("restart", session_id="inspect-plus-restart")
        continuity = compose_continuity_operational_reply("restart", session_id="inspect-plus-restart")
    assert mutation is not None
    assert mutation[1] == "mutation_preflight_job_created"
    assert continuity is None
