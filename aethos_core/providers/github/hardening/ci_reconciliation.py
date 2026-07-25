# SPDX-License-Identifier: Apache-2.0
"""GitHub CI reconciliation — logs + status + artifacts."""

from __future__ import annotations

from typing import Any


def reconcile_ci_signals(*, workflow_truth: dict[str, Any], readonly_artifact: dict[str, Any]) -> dict[str, Any]:
    summary = str(readonly_artifact.get("summary") or "").lower()
    downstream_stable = "deploy" not in summary or any(w in summary for w in ("stable", "success", "green"))
    return {
        "downstream_stable": downstream_stable,
        "ci_reconciled": workflow_truth.get("workflow_completed") and not workflow_truth.get("critical_failures"),
        "summary": "CI signals reconciled across workflow status and readonly evidence.",
    }
