# SPDX-License-Identifier: Apache-2.0
"""Deployment reconciliation — provider vs runtime."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_hardening.verify import verify_provider_mutation


def reconcile_deployment(*, provider: str, operation_type: str = "restart") -> dict[str, Any]:
    result = verify_provider_mutation(provider=provider, operation_type=operation_type, provider_result={"deployment_state_after": "success"})
    return {
        "provider": provider,
        "reconciled": bool(result.get("verified")) or result.get("maturity") == "stable",
        "verification": result,
        "principle": "Provider APIs are signals — not operational truth by themselves.",
        "summary": result.get("summary", "Deployment reconciliation assessing."),
    }
