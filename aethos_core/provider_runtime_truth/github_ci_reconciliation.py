# SPDX-License-Identifier: Apache-2.0
"""GitHub CI reconciliation — workflow convergence."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_truth_convergence.github_execution_truth import assess_github_execution_truth


def assess_github_ci_reconciliation() -> dict[str, Any]:
    truth = assess_github_execution_truth()
    return {**truth, "converged": truth.get("execution_converged", False)}
