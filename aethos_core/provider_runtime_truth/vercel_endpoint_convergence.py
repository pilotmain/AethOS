# SPDX-License-Identifier: Apache-2.0
"""Vercel endpoint convergence — endpoint truth."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.vercel_runtime_truth import assess_vercel_runtime_truth


def assess_vercel_endpoint_convergence() -> dict[str, Any]:
    truth = assess_vercel_runtime_truth()
    return {**truth, "converged": truth.get("runtime_verified", False)}
