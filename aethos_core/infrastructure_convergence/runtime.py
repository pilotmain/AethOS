# SPDX-License-Identifier: Apache-2.0
"""Infrastructure convergence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_convergence.convergence_runtime import orchestrate_infrastructure_convergence


def assess_infrastructure_convergence() -> dict[str, Any]:
    convergence = orchestrate_infrastructure_convergence()
    return {"ok": True, **convergence}
