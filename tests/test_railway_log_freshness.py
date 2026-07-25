# SPDX-License-Identifier: Apache-2.0
"""Railway log freshness and verification window alignment tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.conversation.provider_memory.provider_followup_runtime import handle_provider_followup
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.railway_log_evidence import (
    collect_restart_log_evidence,
    refresh_restart_log_evidence,
)
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.providers.railway.railway_log_evidence import (
    fetch_fresh_logs_for_verification,
    normalize_railway_timestamp_to_utc,
    pick_newer_log_entries,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean():
    clear_threads_for_tests()
    job_store.clear_for_tests()
    yield
    clear_threads_for_tests()
    job_store.clear_for_tests()


def _job(params: dict):
    class _Job:
        def __init__(self, p):
            self.params = p

    return _Job(params)


def _seed_execution(session_id: str, *, approval: str, bundle_logs: list[dict], restart_state: str = "stabilizing"):
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
                "service_id": "svc-pilotos-api",
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
            "target": {
                "project_name": "pilotos",
                "environment": "production",
                "service_name": "pilotos-api",
                "service_id": "svc-pilotos-api",
            },
            "mutation_execution_approved_at_iso": approval,
            "execution_state": "execution_stabilizing",
            "restart_verification_state": restart_state,
            "provider_evidence_bundle": {
                "approved_at": approval,
                "logs_excerpt": bundle_logs,
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
    return stored


def test_timestamp_normalized_from_railway_ui_format_to_utc():
    assert normalize_railway_timestamp_to_utc("2026-05-25 01:51:03") == "2026-05-25T01:51:03Z"
    assert normalize_railway_timestamp_to_utc("2026-05-25T01:50:41Z") == "2026-05-25T01:50:41Z"


def test_runtime_logs_after_approval_verify_restart_evidence():
    approval = "2026-05-25T01:50:41Z"
    fresh_logs = [
        {
            "timestamp": "2026-05-25T01:51:03Z",
            "level": "INFO",
            "message": "Application startup complete.",
            "source": "runtime_cli_logs",
        }
    ]
    job = _seed_execution(
        "fresh-runtime",
        approval=approval,
        bundle_logs=[
            {
                "timestamp": "2026-05-25T01:13:58Z",
                "level": "INFO",
                "message": "Old cached startup complete.",
            }
        ],
    )
    with patch(
        "aethos_core.providers.railway.railway_log_evidence.fetch_fresh_logs_for_verification",
        return_value={"ok": True, "logs": fresh_logs, "sources_checked": ["runtime_logs_after"], "errors": []},
    ):
        evidence = refresh_restart_log_evidence(job, bypass_cache=True)
    assert evidence.latest_timestamp == "2026-05-25T01:51:03Z"
    assert evidence.timestamp_after_approval is True
    assert evidence.conclusion in {"restart_evidence_detected", "restart_verified"}
    assert evidence.startup_after_approval is True


def test_stale_cached_logs_ignored_when_bypass_cache_true():
    approval = "2026-05-25T01:50:41Z"
    job = _seed_execution(
        "stale-cache",
        approval=approval,
        bundle_logs=[
            {
                "timestamp": "2026-05-25T01:13:58Z",
                "level": "INFO",
                "message": "Application startup complete.",
            }
        ],
    )
    with patch(
        "aethos_core.providers.railway.railway_log_evidence.fetch_fresh_logs_for_verification",
        return_value={
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-05-25T01:13:58Z",
                    "level": "INFO",
                    "message": "Application startup complete.",
                    "source": "deployment_logs",
                }
            ],
            "sources_checked": ["runtime_logs_after"],
            "errors": [],
        },
    ):
        evidence = refresh_restart_log_evidence(job, bypass_cache=True)
    assert evidence.conclusion == "restart_unconfirmed"
    assert evidence.latest_timestamp == "2026-05-25T01:13:58Z"


def test_deployment_logs_older_but_runtime_logs_newer_verified():
    cached = [
        {"timestamp": "2026-05-25T01:13:58Z", "message": "old deployment boot", "level": "INFO"},
    ]
    fresh = [
        {
            "timestamp": "2026-05-25T01:51:03Z",
            "message": "Application startup complete.",
            "level": "INFO",
            "source": "runtime_cli_logs",
        },
        {
            "timestamp": "2026-05-25T01:13:58Z",
            "message": "old deployment boot",
            "level": "INFO",
            "source": "deployment_logs",
        },
    ]
    selected = pick_newer_log_entries(cached, fresh, prefer_fresh=True)
    assert selected[0]["timestamp"] == "2026-05-25T01:51:03Z"

    evidence = collect_restart_log_evidence(
        _job(
            {
                "mutation_execution_approved_at_iso": "2026-05-25T01:50:41Z",
                "restart_verification_state": "stabilizing",
                "provider_evidence_bundle": {"approved_at": "2026-05-25T01:50:41Z", "logs_excerpt": fresh},
            }
        )
    )
    assert evidence.timestamp_after_approval is True
    assert evidence.conclusion in {"restart_evidence_detected", "restart_verified"}


def test_wrong_deployment_logs_do_not_override_runtime_logs():
    approval = "2026-05-25T01:50:41Z"
    with patch(
        "aethos_core.providers.railway.cli_executor.railway_logs",
        return_value={
            "logs": [
                {
                    "timestamp": "2026-05-25 01:51:03",
                    "message": "Application startup complete.",
                }
            ]
        },
    ), patch(
        "aethos_core.providers.railway.mutations.resolve_railway_mutation_credentials",
        return_value=("token", "env", None),
    ), patch(
        "aethos_core.providers.railway.api_client.find_service_by_name",
        return_value={"service_id": "svc-1", "service_name": "pilotos-api", "project_id": "proj-1"},
    ), patch(
        "aethos_core.providers.railway.api_client.list_service_deployments",
        return_value=[{"id": "dep-old", "state": "SUCCESS", "created_at": "2026-05-24T20:00:00Z"}],
    ), patch(
        "aethos_core.providers.railway.api_client.fetch_deployment_logs",
        return_value=[
            {
                "timestamp": "2026-05-25T01:13:58Z",
                "level": "INFO",
                "message": "Old deployment startup complete.",
            }
        ],
    ):
        payload = fetch_fresh_logs_for_verification(
            target={"service_name": "pilotos-api", "service_id": "svc-1", "project_id": "proj-1"},
            approval_time=approval,
            bypass_cache=True,
            limit=5,
        )
    assert payload["ok"] is True
    assert payload["logs"][0]["timestamp"] == "2026-05-25T01:51:03Z"
    assert "Application startup complete." in payload["logs"][0]["message"]


def test_followup_top_logs_use_fresh_runtime_logs():
    approval = "2026-05-25T01:50:41Z"
    _seed_execution(
        "followup-fresh",
        approval=approval,
        bundle_logs=[
            {"timestamp": "2026-05-25T01:13:58Z", "level": "INFO", "message": "stale cached line"},
        ],
    )
    with patch(
        "aethos_core.providers.railway.railway_log_evidence.fetch_fresh_logs_for_verification",
        return_value={
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-05-25T01:51:03Z",
                    "level": "INFO",
                    "message": "Application startup complete.",
                    "source": "runtime_cli_logs",
                }
            ],
            "sources_checked": ["runtime_logs_after"],
            "errors": [],
        },
    ):
        result = handle_provider_followup(
            session_id="followup-fresh",
            user_text="give me top 5 logs for pilotos-api",
        )
    assert result is not None
    assert "2026-05-25T01:51:03Z" in result.body
    assert result.conclusion in {"restart_evidence_detected", "restart_verified"}


def test_followup_did_restart_happen_marks_verified_with_fresh_runtime_logs():
    approval = "2026-05-25T01:50:41Z"
    _seed_execution(
        "followup-verify",
        approval=approval,
        bundle_logs=[
            {"timestamp": "2026-05-25T01:13:58Z", "level": "INFO", "message": "stale cached line"},
        ],
    )
    with patch(
        "aethos_core.providers.railway.railway_log_evidence.fetch_fresh_logs_for_verification",
        return_value={
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-05-25T01:51:03Z",
                    "level": "INFO",
                    "message": "Application startup complete.",
                    "source": "runtime_cli_logs",
                }
            ],
            "sources_checked": ["runtime_logs_after"],
            "errors": [],
        },
    ):
        result = handle_provider_followup(session_id="followup-verify", user_text="did the restart happen?")
    assert result is not None
    assert result.conclusion in {"restart_evidence_detected", "restart_verified"}
    assert "runtime logs after the restart approval time" in result.body.lower()
