# SPDX-License-Identifier: Apache-2.0
"""Vercel runtime truth — endpoint/runtime verification."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.endpoint_truth import assess_endpoint_truth


def assess_vercel_runtime_truth() -> dict[str, Any]:
    truth = assess_endpoint_truth(provider="vercel")
    return {
        **truth,
        "runtime_verified": truth.get("endpoint_stabilized", False),
        "summary": "Vercel endpoint and runtime truth converging across stabilization window.",
    }
