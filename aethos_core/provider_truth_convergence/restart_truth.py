# SPDX-License-Identifier: Apache-2.0
"""Restart truth — restart stabilization integrity."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.deployment_reconciliation import reconcile_deployment


def assess_restart_truth(*, provider: str = "railway") -> dict[str, Any]:
    recon = reconcile_deployment(provider=provider, operation_type="restart")
    return {
        "provider": provider,
        "restart_stabilized": recon.get("reconciled", False),
        "reconciliation": recon,
        "summary": "Restart stabilization verified with extended monitoring active."
        if recon.get("reconciled")
        else "Restart stabilization converging.",
    }
