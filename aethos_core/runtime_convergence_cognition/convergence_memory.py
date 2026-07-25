# SPDX-License-Identifier: Apache-2.0
"""Convergence memory — historical convergence behavior."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_truth_convergence.runtime_truth_memory import record_truth_convergence


def record_convergence_memory(*, converged: bool) -> dict[str, Any]:
    return record_truth_convergence(converged=converged, tier="convergence_cognition")
