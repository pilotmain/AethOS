# SPDX-License-Identifier: Apache-2.0
"""Railway sustained truth — deployment convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_runtime_truth.railway_runtime_convergence import assess_railway_runtime_convergence


def assess_railway_sustained_truth() -> dict[str, Any]:
    truth = assess_railway_runtime_convergence()
    return {**truth, "sustained_converged": truth.get("converged", False)}
