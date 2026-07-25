# SPDX-License-Identifier: Apache-2.0
"""Endpoint truth — Vercel endpoint stabilization."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.deployment_reconciliation import reconcile_deployment


def assess_endpoint_truth(*, provider: str = "vercel") -> dict[str, Any]:
    recon = reconcile_deployment(provider=provider, operation_type="redeploy")
    return {
        "provider": provider,
        "endpoint_stabilized": recon.get("reconciled", False),
        "reconciliation": recon,
        "summary": "Endpoint stabilization converging across runtime surfaces."
        if not recon.get("reconciled")
        else "Endpoint stabilization verified.",
    }
