# SPDX-License-Identifier: Apache-2.0
"""Infrastructure alignment — runtime vs provider reconciliation."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.provider_reconciliation import reconcile_provider_reality


def assess_infrastructure_alignment(*, provider: str = "railway") -> dict[str, Any]:
    recon = reconcile_provider_reality(provider=provider)
    return {
        **recon,
        "aligned": recon.get("reality_aligned", False),
        "summary": "Infrastructure aligned with provider runtime signals." if recon.get("reality_aligned") else "Infrastructure alignment converging — provider vs runtime reconciliation active.",
    }
