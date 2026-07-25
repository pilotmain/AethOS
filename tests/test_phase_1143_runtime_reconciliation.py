# SPDX-License-Identifier: Apache-2.0
"""Phase 11.4.3 — Runtime reconciliation tests."""

from __future__ import annotations

from aethos_core.operational_patience.runtime import assess_operational_patience
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix
from aethos_core.reality_harness_v41.scenarios import list_reality_scenarios_v41
from aethos_core.recovery_truth_convergence.runtime import assess_recovery_truth_convergence
from aethos_core.runtime_decay.runtime import assess_runtime_decay
from aethos_core.runtime_reconciliation.reconciliation_runtime import orchestrate_reconciliation
from aethos_core.runtime_reconciliation.runtime import assess_runtime_reconciliation
from aethos_core.sustained_verification_windows.runtime import assess_sustained_verification_windows


def test_runtime_reconciliation_aggregate():
    state = assess_runtime_reconciliation()
    assert state["phase"] == "11.4.3"
    assert state["ok"] is True
    assert "reconciled" in state["reconciliation"]["summary"].lower()
    assert state["harness"]["harness_version"] == "4.1"


def test_reconciliation_narrative():
    recon = orchestrate_reconciliation()
    assert "replay continuity" in recon["summary"].lower()
    assert "sustained verification" in recon["narrative"].lower()


def test_operational_patience():
    patience = assess_operational_patience()
    assert patience["patience_maintained"] is True
    assert "sustained runtime stabilization" in patience["summary"].lower()


def test_runtime_decay():
    decay = assess_runtime_decay()
    assert decay["ok"] is True
    assert decay["decay_bounded"] is True


def test_sustained_verification_windows():
    windows = assess_sustained_verification_windows()
    assert windows["window_qualified"] is True
    assert "sustained verification window" in windows["summary"].lower()


def test_recovery_truth_convergence():
    recovery = assess_recovery_truth_convergence()
    assert recovery["ok"] is True
    assert recovery["converged"] is True


def test_reality_harness_v41():
    scenarios = list_reality_scenarios_v41()
    assert len(scenarios) == 8
    assert all(s["harness_version"] == "4.1" for s in scenarios)
    ids = {s["id"] for s in scenarios}
    assert "railway_delayed_degradation" in ids
    assert "prolonged_recovery" in ids


def test_capability_matrix_runtime_reconciliation():
    matrix = build_capability_truth_matrix()
    rr = next((r for r in matrix if r.get("id") == "runtime_reconciliation"), None)
    assert rr is not None and rr["verification_coverage_pct"] >= 84
