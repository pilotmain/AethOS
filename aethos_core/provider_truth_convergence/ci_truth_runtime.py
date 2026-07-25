# SPDX-License-Identifier: Apache-2.0
"""CI truth runtime — GitHub workflow convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.deployment_reconciliation import reconcile_deployment


def assess_ci_truth(*, provider: str = "github") -> dict[str, Any]:
    recon = reconcile_deployment(provider=provider, operation_type="workflow_rerun")
    return {
        "provider": provider,
        "workflow_converged": recon.get("reconciled", False),
        "reconciliation": recon,
        "summary": "CI workflow truth converging with downstream stability checks."
        if not recon.get("reconciled")
        else "CI workflow truth verified.",
    }
