# SPDX-License-Identifier: Apache-2.0
"""End-to-end DevOps loop tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.operations.devops_loop import devops_loop_summary, run_devops_loop


def test_read_logs_and_diagnose_missing_env():
    logs = [{"message": "DATABASE_URL is missing", "timestamp": "2026-01-15T12:00:00+00:00"}]
    with patch("aethos_core.operational_agents.roles.railway_logs", create=True):
        result = run_devops_loop(
            provider="railway",
            service_name="api",
            phase="diagnose",
            logs=logs,
        )
    diagnosis = result.get("diagnosis") or {}
    assert diagnosis.get("ok") is True
    assert diagnosis.get("category") == "missing_env_var"


def test_propose_fix_requires_approval():
    logs = [{"message": "Missing API_KEY env var", "timestamp": "2026-01-15T12:00:00+00:00"}]
    result = run_devops_loop(provider="railway", service_name="api", logs=logs)
    fix = result.get("fix_plan") or {}
    assert fix.get("ok") is True
    assert fix.get("requires_approval") is True
    assert fix.get("preflight_required") is True


def test_devops_loop_summary_includes_diagnosis():
    result = run_devops_loop(
        provider="railway",
        service_name="api",
        logs=[{"message": "ECONNREFUSED connecting to redis", "timestamp": "2026-01-15T12:00:00+00:00"}],
    )
    summary = devops_loop_summary(result)
    assert "Diagnosis" in summary or "diagnosis" in summary.lower() or "connection" in summary.lower()
