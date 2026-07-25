# SPDX-License-Identifier: Apache-2.0
"""GitHub execution truth — workflow convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.ci_truth_runtime import assess_ci_truth


def assess_github_execution_truth() -> dict[str, Any]:
    truth = assess_ci_truth(provider="github")
    return {
        **truth,
        "execution_converged": truth.get("workflow_converged", False),
        "summary": "GitHub workflow execution truth converging with downstream stability checks.",
    }
