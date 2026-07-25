# SPDX-License-Identifier: Apache-2.0
"""Railway runtime convergence — deployment stabilization."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.railway_runtime_truth import assess_railway_runtime_truth


def assess_railway_runtime_convergence() -> dict[str, Any]:
    truth = assess_railway_runtime_truth()
    return {**truth, "converged": truth.get("runtime_stabilized", False)}
