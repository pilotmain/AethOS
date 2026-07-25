# SPDX-License-Identifier: Apache-2.0
"""Universal evidence bundle and Railway startup detection regression tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.conversation.provider_memory.adapters.railway_adapter import RailwayEvidenceAdapter
from aethos_core.conversation.provider_memory.provider_followup_runtime import handle_provider_followup
from aethos_core.operational_skill_runtime.evidence_collector import (
    build_universal_evidence_from_job,
    detect_startup_after_approval,
    resolve_command_state,
)
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job, sync_thread_from_preflight
from aethos_core.operational_thread_memory.railway_log_evidence import collect_restart_log_evidence, refresh_restart_log_evidence
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
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


def test_full_log_scan_detects_startup_after_approval():
    entries = [
        {"timestamp": "2026-05-25T01:13:58Z", "message": "old line"},
        {"timestamp": "2026-05-25T01:51:03Z", "message": "Application startup complete."},
    ]
    detected, row = detect_startup_after_approval(entries, approval_time="2026-05-25T01:50:41Z")
    assert detected is True
    assert row is not None
    assert "startup complete" in row["message"].lower()


def test_command_state_from_evidence_bundle():
    job = _job(
        {
            "provider_evidence_bundle": {
                "command_submitted": True,
                "command": "serviceInstanceRedeploy",
            }
        }
    )
    submitted, command = resolve_command_state(job)
    assert submitted is True
    assert command == "serviceInstanceRedeploy"


def test_universal_evidence_bundle_fields():
    job = _job(
        {
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "target": {"service_name": "pilotos-api", "project_name": "pilotos", "environment": "production"},
            "mutation_execution_approved_at_iso": "2026-05-25T01:50:41Z",
            "provider_evidence_bundle": {
                "approved_at": "2026-05-25T01:50:41Z",
                "command_submitted": True,
                "command": "serviceInstanceRedeploy",
                "logs_excerpt": [
                    {"timestamp": "2026-05-25T01:51:03Z", "message": "Application startup complete."},
                ],
            },
        }
    )
    bundle = build_universal_evidence_from_job(job)
    assert bundle.command_submitted is True
    assert bundle.command_name == "serviceInstanceRedeploy"
    assert bundle.startup_log_observed_after_approval is True
    assert bundle.latest_log_timestamp == "2026-05-25T01:51:03Z"


def test_collect_restart_evidence_marks_startup_from_non_latest_line():
    evidence = collect_restart_log_evidence(
        _job(
            {
                "mutation_execution_approved_at_iso": "2026-05-25T01:50:41Z",
                "restart_verification_state": "stabilizing",
                "provider_evidence_bundle": {
                    "approved_at": "2026-05-25T01:50:41Z",
                    "command_submitted": True,
                    "command": "serviceInstanceRedeploy",
                    "logs_excerpt": [
                        {"timestamp": "2026-05-25T01:51:03Z", "message": "Application startup complete."},
                        {"timestamp": "2026-05-25T01:51:10Z", "message": "Health check passed"},
                    ],
                },
            }
        )
    )
    assert evidence.startup_after_approval is True
    assert evidence.timestamp_after_approval is True
    assert evidence.conclusion in {"restart_evidence_detected", "restart_verified"}


def test_railway_adapter_reports_submitted_command():
    session_id = "evidence-adapter"
    preflight = authority.create_job(
        title="preflight",
        job_type="mutation_preflight",
        params={"provider": "railway", "operation_type": "restart", "target_name": "pilotos-api"},
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight)
    execution = authority.create_job(
        title="execution",
        job_type="mutation_execution",
        params={
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "pilotos-api",
            "mutation_execution_approved_at_iso": "2026-05-25T01:50:41Z",
            "provider_evidence_bundle": {
                "approved_at": "2026-05-25T01:50:41Z",
                "command_submitted": True,
                "command": "serviceInstanceRedeploy",
                "logs_excerpt": [
                    {"timestamp": "2026-05-25T01:51:03Z", "message": "Application startup complete."},
                ],
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    stored = job_store.get(execution.id)
    sync_thread_from_execution_job(job=stored)

    adapter = RailwayEvidenceAdapter()
    with patch(
        "aethos_core.providers.railway.railway_log_evidence.fetch_fresh_logs_for_verification",
        return_value={
            "ok": True,
            "logs": [
                {
                    "timestamp": "2026-05-25T01:51:03Z",
                    "message": "Application startup complete.",
                    "source": "runtime_cli_logs",
                }
            ],
            "sources_checked": ["runtime_logs_after"],
            "errors": [],
        },
    ):
        verification = adapter.verify_operation(None, stored)
    assert verification.provider_command == "submitted"
    assert verification.startup_after_approval is True
