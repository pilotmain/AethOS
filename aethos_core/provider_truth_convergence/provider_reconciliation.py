# SPDX-License-Identifier: Apache-2.0
"""Provider reconciliation — provider vs infrastructure reality."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.deployment_reconciliation import reconcile_deployment


def reconcile_provider_reality(*, provider: str, operation_type: str = "restart") -> dict[str, Any]:
    recon = reconcile_deployment(provider=provider, operation_type=operation_type)
    aligned = recon.get("reconciled", False)
    return {
        "provider": provider,
        "reality_aligned": aligned,
        "reconciliation": recon,
        "principle": "Provider APIs are signals — not operational truth by themselves.",
        "summary": "Provider signal reconciled with infrastructure reality."
        if aligned
        else "Provider signal diverges from infrastructure reality — extended verification active.",
    }
