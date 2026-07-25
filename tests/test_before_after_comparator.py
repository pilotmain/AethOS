# SPDX-License-Identifier: Apache-2.0
"""Before/after comparator tests."""

from __future__ import annotations

from aethos_core.post_mutation_verification.before_after_comparator import compare_before_after
from aethos_core.post_mutation_verification.verification_evidence_collector import VerificationEvidence


def _evidence(**kwargs: object) -> VerificationEvidence:
    base = VerificationEvidence()
    for key, value in kwargs.items():
        setattr(base, key, value)
    return base


def test_health_improved() -> None:
    evidence = _evidence(
        deployment_status_before="failed",
        deployment_status_after="success",
        service_health="healthy",
        logs_after_execution=True,
        startup_markers_present=True,
    )
    comparison = compare_before_after(evidence)
    assert comparison.health_improved is True
    assert comparison.health_unchanged_failed is False
    assert "improved" in comparison.change_summary.lower()


def test_health_unchanged_failed() -> None:
    evidence = _evidence(
        deployment_status_before="failed",
        deployment_status_after="failed",
        service_health="failed",
        new_crash_detected=True,
    )
    comparison = compare_before_after(evidence)
    assert comparison.health_unchanged_failed is True
    assert comparison.health_improved is False


def test_logs_after_restart_present() -> None:
    evidence = _evidence(
        logs_after_execution=True,
        startup_markers_present=True,
        log_summary="application startup complete; listening on port 8080",
    )
    comparison = compare_before_after(evidence)
    assert comparison.logs_after_restart_present is True
    assert "startup" in comparison.change_summary.lower()


def test_new_crash_after_restart() -> None:
    evidence = _evidence(
        deployment_status_before="failed",
        deployment_status_after="failed",
        service_health="failed",
        new_crash_detected=True,
    )
    comparison = compare_before_after(evidence)
    assert comparison.new_crash_after_restart is True
    assert "failure" in comparison.change_summary.lower() or "failed" in comparison.change_summary.lower()
