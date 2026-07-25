# SPDX-License-Identifier: Apache-2.0
"""Phase 11.6.1 — Runtime truth convergence tests."""

from __future__ import annotations

from aethos_core.adaptive_sustained_verification.runtime import assess_adaptive_sustained_verification
from aethos_core.long_tail_operational_decay.runtime import assess_long_tail_operational_decay
from aethos_core.operational_stability_windows.runtime import assess_operational_stability_windows
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.recovery_convergence.runtime import assess_recovery_convergence
from aethos_core.runtime_truth_convergence.runtime import assess_runtime_truth_convergence
from aethos_core.runtime_truth_convergence.runtime_truth_runtime import orchestrate_runtime_truth


def test_runtime_truth_convergence_aggregate():
    state = assess_runtime_truth_convergence()
    assert state["phase"] == "11.6.1"
    assert state["ok"] is True
    assert "sustained verification windows" in state["summary"].lower()
    assert "extended reconciliation" in state["narrative"].lower()
    assert state["harness"]["harness_version"] == "4.1"


def test_orchestrate_runtime_truth_narrative():
    truth = orchestrate_runtime_truth()
    assert "infrastructure convergence" in truth["summary"].lower()
    assert truth["narrative"] == "Extended reconciliation remains active."


def test_operational_stability_windows():
    windows = assess_operational_stability_windows()
    assert windows["window_qualified"] is True
    assert "sustained runtime verification window" in windows["summary"].lower()


def test_recovery_convergence():
    recovery = assess_recovery_convergence()
    assert recovery["ok"] is True
    assert recovery["continuously_reconciled"] is True


def test_long_tail_operational_decay():
    decay = assess_long_tail_operational_decay()
    assert decay["decay_bounded"] is True


def test_adaptive_sustained_verification():
    adaptive = assess_adaptive_sustained_verification()
    assert adaptive["ok"] is True
    assert "adaptive" in adaptive["summary"].lower()


def test_capability_matrix_runtime_truth_convergence():
    matrix = build_capability_truth_matrix()
    rtc = next((r for r in matrix if r.get("id") == "runtime_truth_convergence"), None)
    assert rtc is not None and rtc["verification_coverage_pct"] >= 85
