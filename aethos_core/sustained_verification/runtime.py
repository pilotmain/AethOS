# SPDX-License-Identifier: Apache-2.0
"""Sustained verification aggregate — Phase 11.6."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.drift_reverification import assess_drift_reverification
from aethos_core.sustained_verification.operational_rechecks import schedule_operational_recheck
from aethos_core.sustained_verification.replay_stability import assess_replay_stability
from aethos_core.sustained_verification.topology_verification import verify_topology_convergence
from aethos_core.sustained_verification.verification_decay import assess_verification_decay
from aethos_core.sustained_verification.verification_runtime import orchestrate_verification


def assess_sustained_verification() -> dict[str, Any]:
    verification = orchestrate_verification(cycles_completed=3, cycles_required=4)
    drift = assess_drift_reverification()
    topology = verify_topology_convergence()
    replay = assess_replay_stability()
    recheck = schedule_operational_recheck(surface="runtime", passed=True)
    decay = assess_verification_decay()
    qualified = (
        drift.get("drift_bounded")
        and topology.get("topology_verified", False)
        and replay.get("replay_stable")
        and decay.get("erosion_bounded")
    )
    return {
        "ok": True,
        "verification": verification,
        "drift_reverification": drift,
        "topology_verification": topology,
        "replay_stability": replay,
        "operational_rechecks": recheck,
        "verification_decay": decay,
        "sustained_qualified": qualified,
        "extended_monitoring_active": not verification.get("sustained"),
        "summary": "Sustained operational verification converging across long-tail windows."
        if not qualified
        else "Sustained operational verification qualified.",
    }
