# SPDX-License-Identifier: Apache-2.0
"""Recovery runtime orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_runtime.operational_patience import should_claim_resolved
from aethos_core.recovery_runtime.recovery_confidence import score_recovery_confidence
from aethos_core.recovery_runtime.recovery_storytelling import build_recovery_story
from aethos_core.recovery_runtime.recovery_tracking import track_recovery


def assess_recovery_state(*, mutation_job_id: str) -> dict[str, Any]:
    from aethos_core.reconciliation.mutation_reconciliation import reconcile_mutation

    reconciliation = reconcile_mutation(mutation_job_id=mutation_job_id)
    if not reconciliation.get("ok"):
        return reconciliation

    verification = reconciliation.get("verification") or {}
    stabilization = reconciliation.get("stabilization") or {}
    tracking = track_recovery(verification=verification, stabilization=stabilization)
    confidence = score_recovery_confidence(verification=verification, reconciliation=reconciliation)
    resolved = should_claim_resolved(stabilization=stabilization, verification=verification)
    narrative = build_recovery_story(
        resolved=resolved,
        extended_monitoring=tracking.get("extended_monitoring_active", True),
        recovery_confidence=float(confidence.get("recovery_confidence") or 0.5),
    )

    return {
        "ok": True,
        "mutation_job_id": mutation_job_id,
        "reconciliation": reconciliation,
        "tracking": tracking,
        "confidence": confidence,
        "resolved_claim_allowed": resolved,
        "narrative": narrative,
        "summary": narrative,
    }


def build_recovery_narrative(*, mutation_job_id: str) -> str:
    state = assess_recovery_state(mutation_job_id=mutation_job_id)
    return str(state.get("narrative") or state.get("summary") or "Recovery state assessing.")
