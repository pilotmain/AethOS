# SPDX-License-Identifier: Apache-2.0
"""Convergence confidence — stabilization confidence."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.convergence_confidence import assess_convergence_confidence


def assess_stabilization_confidence() -> dict[str, Any]:
    return assess_convergence_confidence()
