# SPDX-License-Identifier: Apache-2.0
"""Railway log timestamp verification tests."""

from __future__ import annotations

from aethos_core.operational_thread_memory.railway_log_evidence import (
    StructuredLogEntry,
    assess_restart_from_logs,
    collect_restart_log_evidence,
    normalize_log_entries,
)


def _job(params: dict):
    class _Job:
        def __init__(self, p):
            self.params = p

    return _Job(params)


def test_log_timestamp_after_approval_verifies_restart_evidence():
    entries = normalize_log_entries(
        [
            {"timestamp": "2026-05-20T10:02:00+00:00", "message": "Application startup complete."},
        ]
    )
    result = assess_restart_from_logs(approval_time="2026-05-20T10:00:00+00:00", entries=entries)
    assert result["verified"] is True
    assert result["latest_timestamp"] == "2026-05-20T10:02:00+00:00"


def test_log_timestamp_before_approval_does_not_verify():
    entries = normalize_log_entries(
        [
            {"timestamp": "2026-05-20T09:59:00+00:00", "message": "Application startup complete."},
        ]
    )
    result = assess_restart_from_logs(approval_time="2026-05-20T10:00:00+00:00", entries=entries)
    assert result["verified"] is False


def test_logs_without_timestamp_return_bounded_uncertainty():
    entries = [StructuredLogEntry(timestamp=None, level="INFO", message="Application startup complete.")]
    result = assess_restart_from_logs(approval_time="2026-05-20T10:00:00+00:00", entries=entries)
    assert result["verified"] is False
    assert result["reason"] == "no_timestamps"
    assert "no timestamp was available" in result["message"]


def test_startup_log_after_approval_contributes_restart_evidence():
    job = _job(
        {
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
            "mutation_execution_approved_at_iso": "2026-05-20T10:00:00+00:00",
            "restart_verification_state": "restart_requested",
            "provider_evidence_bundle": {
                "approved_at": "2026-05-20T10:00:00+00:00",
                "logs_excerpt": [
                    {
                        "timestamp": "2026-05-20T10:01:10+00:00",
                        "level": "INFO",
                        "message": "Application startup complete.",
                    }
                ],
            },
        }
    )
    evidence = collect_restart_log_evidence(job)
    assert evidence.latest_timestamp == "2026-05-20T10:01:10+00:00"
    assert evidence.timestamp_after_approval is True
    assert evidence.startup_after_approval is True


def test_normalize_log_entries_structures_payload():
    entries = normalize_log_entries([{"timestamp": "2026-05-20T10:00:00+00:00", "message": "boot"}])
    assert entries[0].to_dict() == {
        "timestamp": "2026-05-20T10:00:00+00:00",
        "level": "INFO",
        "message": "boot",
    }
