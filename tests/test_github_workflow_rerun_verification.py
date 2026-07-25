# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun verification tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.providers.github.mutations.workflow_rerun_verification import (
    summarize_verification_for_operator,
    verify_workflow_rerun,
)


@patch("aethos_core.providers.github.mutations.workflow_rerun_verification.verify_github_workflow_rerun")
def test_verify_workflow_rerun_wrapper(mock_verify) -> None:
    mock_verify.return_value = {"ok": True, "new_run_detected": True, "run_number": 43, "verification_result": "healthy"}
    result = verify_workflow_rerun("token", repository="pilotmain/aethos", source_run_id=42)
    assert result["new_run_detected"] is True
    mock_verify.assert_called_once()


def test_summarize_verification_pass() -> None:
    text = summarize_verification_for_operator({"new_run_detected": True, "run_number": 43, "verification_result": "healthy"})
    assert "passed" in text.lower()


def test_summarize_verification_pending() -> None:
    text = summarize_verification_for_operator(
        {"new_run_detected": True, "run_number": 44, "run_status": "in_progress", "verification_result": "pending"}
    )
    assert "still running" in text.lower()


def test_summarize_verification_failed() -> None:
    text = summarize_verification_for_operator(
        {"new_run_detected": True, "run_number": 45, "run_conclusion": "failure", "verification_result": "inconclusive"}
    )
    assert "failed" in text.lower()
