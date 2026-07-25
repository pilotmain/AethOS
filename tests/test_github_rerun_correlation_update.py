# SPDX-License-Identifier: Apache-2.0
"""GitHub rerun correlation update tests."""

from __future__ import annotations

from aethos_core.cross_provider_correlation.correlation_store import clear_store_for_tests, get_session_snapshot
from aethos_core.providers.github.mutations.workflow_rerun_verification import update_correlation_after_rerun_verification


def setup_function() -> None:
    clear_store_for_tests()


def test_update_correlation_after_successful_rerun() -> None:
    result = update_correlation_after_rerun_verification(
        session_id="rerun-corr",
        repository="pilotmain/aethos",
        verification={
            "new_run_detected": True,
            "run_number": 50,
            "run_conclusion": "success",
            "run_status": "completed",
            "head_branch": "main",
            "head_sha": "abc123def456",
        },
    )
    assert result["github_status"] == "passed"
    snapshot = get_session_snapshot("rerun-corr")
    assert snapshot.get("github")
    assert snapshot["github"]["status"] == "passed"


def test_update_correlation_after_failed_rerun() -> None:
    result = update_correlation_after_rerun_verification(
        session_id="rerun-corr-fail",
        repository="pilotmain/aethos",
        verification={
            "new_run_detected": True,
            "run_number": 51,
            "run_conclusion": "failure",
            "run_status": "completed",
            "head_branch": "main",
        },
    )
    assert result["github_status"] == "failed"
    snapshot = get_session_snapshot("rerun-corr-fail")
    assert snapshot["github"]["status"] == "failed"
