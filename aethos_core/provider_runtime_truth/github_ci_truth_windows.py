# SPDX-License-Identifier: Apache-2.0
"""GitHub CI truth windows — CI runtime truth."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_runtime_truth.github_ci_reconciliation import assess_github_ci_reconciliation


def assess_github_ci_truth_windows() -> dict[str, Any]:
    truth = assess_github_ci_reconciliation()
    return {**truth, "ci_truth_continuous": truth.get("converged", False)}
