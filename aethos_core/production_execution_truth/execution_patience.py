# SPDX-License-Identifier: Apache-2.0
"""Execution patience — prevent premature healthy claims."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_runtime.operational_patience import should_claim_resolved


def assess_execution_patience(*, stabilization: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    resolved = should_claim_resolved(stabilization=stabilization, verification=verification)
    return {
        "healthy_claim_allowed": resolved,
        "premature_claim_blocked": not resolved,
        "summary": "Premature healthy claims blocked — execution patience active."
        if not resolved
        else "Execution patience satisfied — stabilization complete.",
    }
