# SPDX-License-Identifier: Apache-2.0
"""Infrastructure convergence memory — convergence history."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_convergence_cognition.convergence_memory import record_convergence_memory


def record_infrastructure_convergence(*, converged: bool = True) -> dict[str, Any]:
    return record_convergence_memory(converged=converged)
