# SPDX-License-Identifier: Apache-2.0
"""Convergence confidence — bounded trust."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_truth_convergence.confidence_recovery import assess_confidence_recovery


def assess_convergence_confidence() -> dict[str, Any]:
    return assess_confidence_recovery()
