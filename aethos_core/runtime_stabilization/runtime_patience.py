# SPDX-License-Identifier: Apache-2.0
"""Runtime patience — avoid premature healthy claims."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_runtime.operational_patience import should_claim_resolved


def assess_runtime_patience(*, stabilization: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    resolved = should_claim_resolved(stabilization=stabilization, verification=verification)
    return {
        "resolved_claim_allowed": resolved,
        "premature_healthy_blocked": not resolved,
        "summary": "Premature healthy claims blocked — stabilization time respected."
        if not resolved
        else "Stabilization patience satisfied.",
    }
