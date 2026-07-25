# SPDX-License-Identifier: Apache-2.0
"""Evidence-time honesty for restart verification."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.conversation.provider_memory.provider_followup_runtime import handle_provider_followup
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.railway_log_evidence import collect_restart_log_evidence
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _job(params: dict):
    class _Job:
        def __init__(self, p):
            self.params = p

    return _Job(params)


def _seed_thread(
    session_id: str,
    *,
    approval: str,
    latest_log: str,
    restart_state: str = "stabilizing",
) -> None:
    preflight = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "target": {
                "project_name": "pilotos",
                "environment": "production",
                "service_name": "pilotos-api",
                "resolved": True,
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="Mutation execution — restart",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "mutation_execution_approved_at_iso": approval,
            "execution_state": "execution_stabilizing",
            "restart_verification_state": restart_state,
            "provider_evidence_bundle": {
                "approved_at": approval,
                "logs_excerpt": [
                    {
                        "timestamp": latest_log,
                        "level": "INFO",
                        "message": "Application startup complete.",
                    }
                ],
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    assert stored is not None
    stored.status = stored.status.__class__("completed")
    sync_thread_from_execution_job(job=stored)


def test_latest_logs_older_than_approval_are_unconfirmed():
    evidence = collect_restart_log_evidence(
        _job(
            {
                "mutation_execution_approved_at_iso": "2026-05-25T01:13:20+00:00",
                "restart_verification_state": "stabilizing",
                "provider_evidence_bundle": {
                    "approved_at": "2026-05-25T01:13:20+00:00",
                    "logs_excerpt": [
                        {
                            "timestamp": "2026-05-24T23:09:27+00:00",
                            "level": "INFO",
                            "message": "Application startup complete.",
                        }
                    ],
                },
            }
        )
    )
    assert evidence.conclusion == "restart_unconfirmed"
    assert evidence.timestamp_after_approval is False


def test_latest_logs_after_approval_support_restart_evidence():
    evidence = collect_restart_log_evidence(
        _job(
            {
                "mutation_execution_approved_at_iso": "2026-05-25T01:13:20+00:00",
                "restart_verification_state": "restart_requested",
                "provider_evidence_bundle": {
                    "approved_at": "2026-05-25T01:13:20+00:00",
                    "logs_excerpt": [
                        {
                            "timestamp": "2026-05-25T01:20:00+00:00",
                            "level": "INFO",
                            "message": "Application startup complete.",
                        }
                    ],
                },
            }
        )
    )
    assert evidence.conclusion in {"restart_evidence_detected", "restart_verified"}
    assert evidence.timestamp_after_approval is True


def test_no_approval_time_returns_bounded_uncertainty():
    evidence = collect_restart_log_evidence(
        _job(
            {
                "restart_verification_state": "stabilizing",
                "provider_evidence_bundle": {
                    "logs_excerpt": [
                        {
                            "timestamp": "2026-05-24T23:09:27+00:00",
                            "level": "INFO",
                            "message": "Application startup complete.",
                        }
                    ],
                },
            }
        )
    )
    assert evidence.conclusion != "restart_verified"
    assert evidence.approval_time is None


def test_still_stabilizing_not_used_when_evidence_stale():
    _seed_thread(
        "stale-stabilizing",
        approval="2026-05-25T01:13:20+00:00",
        latest_log="2026-05-24T23:09:27+00:00",
        restart_state="stabilizing",
    )
    with patch(
        "aethos_core.providers.railway.railway_log_evidence.fetch_fresh_logs_for_verification",
        return_value={
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-05-24T23:09:27+00:00",
                    "level": "INFO",
                    "message": "Application startup complete.",
                    "source": "deployment_logs",
                }
            ],
            "sources_checked": ["runtime_logs_after"],
            "errors": [],
        },
    ):
        health = handle_provider_followup(session_id="stale-stabilizing", user_text="check service health")
    assert health is not None
    assert health.conclusion == "restart_unconfirmed"
    assert "Still stabilizing" not in health.body
    assert "do not prove the restart happened" in health.body.lower()

    with patch(
        "aethos_core.providers.railway.railway_log_evidence.fetch_fresh_logs_for_verification",
        return_value={
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-05-24T23:09:27+00:00",
                    "level": "INFO",
                    "message": "Application startup complete.",
                    "source": "deployment_logs",
                }
            ],
            "sources_checked": ["runtime_logs_after"],
            "errors": [],
        },
    ):
        logs = handle_provider_followup(
            session_id="stale-stabilizing",
            user_text="Check top 5 logs for pilotos-api",
        )
        verify = handle_provider_followup(session_id="stale-stabilizing", user_text="did the restart happen?")
    assert logs is not None
    assert "older than the restart approval time" in logs.body
    assert "Still stabilizing" not in logs.body
    assert verify is not None
    assert verify.conclusion == "restart_unconfirmed"
    assert "Still stabilizing" not in verify.body


def test_still_stabilizing_used_when_command_submitted_and_evidence_expected():
    _seed_thread(
        "active-stabilizing",
        approval="2026-05-25T01:13:20+00:00",
        latest_log="2026-05-25T01:14:00+00:00",
        restart_state="stabilizing",
    )
    with patch(
        "aethos_core.providers.railway.railway_log_evidence.fetch_fresh_logs_for_verification",
        return_value={
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-05-25T01:14:00+00:00",
                    "level": "INFO",
                    "message": "Application startup complete.",
                    "source": "runtime_cli_logs",
                }
            ],
            "sources_checked": ["runtime_logs_after"],
            "errors": [],
        },
    ):
        result = handle_provider_followup(session_id="active-stabilizing", user_text="check service health")
    assert result is not None
    assert result.conclusion in {"still_stabilizing", "restart_evidence_detected", "restart_verified"}
