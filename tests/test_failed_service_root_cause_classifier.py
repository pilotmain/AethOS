# SPDX-License-Identifier: Apache-2.0
"""Root-cause classifier tests."""

from __future__ import annotations

from aethos_core.failed_service_investigation.root_cause_classifier import classify_root_cause


def _logs(*messages: str) -> list[dict]:
    return [{"message": msg} for msg in messages]


def test_wiredtiger_only_is_bounded_startup_storage_activity():
    result = classify_root_cause(
        logs=_logs("WiredTiger message", "WiredTiger recovery log replay has progressed"),
        service_name="MongoDB",
        deployment_state="failed",
    )
    assert result.category == "database_startup_or_storage_activity"
    assert result.confidence in {"low", "medium"}
    assert result.bounded_diagnosis is True
    assert result.suggests_mutation is False
    assert any("WiredTiger" in line for line in result.interpretation)


def test_missing_env_var():
    result = classify_root_cause(
        logs=_logs("Error: missing required environment variable DATABASE_URL"),
        service_name="api",
    )
    assert result.category == "missing_env_variable"
    assert result.confidence == "high"


def test_out_of_memory():
    result = classify_root_cause(
        logs=_logs("FATAL ERROR: out of memory"),
        service_name="worker",
    )
    assert result.category == "resource_pressure"
    assert result.confidence == "high"


def test_permission_denied_storage():
    result = classify_root_cause(
        logs=_logs("permission denied opening /data/db/WiredTiger.lock"),
        service_name="MongoDB",
    )
    assert result.category == "storage_permission_issue"
    assert result.confidence == "high"


def test_module_not_found_start_command():
    result = classify_root_cause(
        logs=_logs("Error: Cannot find module 'express'"),
        service_name="api",
    )
    assert result.category == "start_command_error"
    assert result.confidence == "high"


def test_exit_code_crash_loop():
    result = classify_root_cause(
        logs=_logs("process exited with code 1", "container restart"),
        service_name="worker",
        deployment_state="crashed",
    )
    assert result.category == "crash_loop"
    assert "exit" in " ".join(result.next_checks).lower() or result.suggests_mutation is False
