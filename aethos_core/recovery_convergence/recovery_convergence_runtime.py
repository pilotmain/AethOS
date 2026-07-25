# SPDX-License-Identifier: Apache-2.0
"""Recovery convergence runtime — recovery orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_truth_convergence.runtime import assess_recovery_truth_convergence


def orchestrate_recovery_convergence(*, provider: str = "railway") -> dict[str, Any]:
    return assess_recovery_truth_convergence(provider=provider)
