# SPDX-License-Identifier: Apache-2.0
"""Provider runtime alignment — provider vs runtime truth."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.provider_reconciliation import reconcile_provider_reality


def assess_provider_runtime_alignment(*, provider: str = "railway", operation_type: str = "restart") -> dict[str, Any]:
    recon = reconcile_provider_reality(provider=provider, operation_type=operation_type)
    return {
        **recon,
        "runtime_aligned": recon.get("reality_aligned", False),
        "principle": "Provider APIs describe events. Runtime reconciliation describes reality.",
    }
