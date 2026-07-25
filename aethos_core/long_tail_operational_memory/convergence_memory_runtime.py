# SPDX-License-Identifier: Apache-2.0
"""Convergence memory runtime — stabilization history."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_convergence_cognition.convergence_memory import record_convergence_memory


def recall_convergence_history(*, converged: bool = True) -> dict[str, Any]:
    return record_convergence_memory(converged=converged)
