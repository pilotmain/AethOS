# SPDX-License-Identifier: Apache-2.0
"""Deep operational reasoning engine — Phase 10.1.4A orchestrator."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.reasoning.confidence_evolution import track_confidence_evolution
from aethos_core.reasoning.dependency_reasoning import analyze_dependency_impact
from aethos_core.reasoning.operational_tradeoffs import compare_operational_tradeoffs
from aethos_core.reasoning.replay_reasoning import reconstruct_replay_evolution
from aethos_core.reasoning.root_cause_depth import analyze_root_cause_depth
from aethos_core.reasoning.uncertainty_reasoning import explain_operational_uncertainty


def assess_deep_operational_reasoning(*, session_id: str = "default") -> dict[str, Any]:
    """Senior engineer-level operational reasoning synthesis."""
    root = analyze_root_cause_depth(session_id=session_id)
    tradeoffs = compare_operational_tradeoffs(session_id=session_id)
    replay = reconstruct_replay_evolution(session_id=session_id)
    uncertainty = explain_operational_uncertainty(session_id=session_id)
    dependency = analyze_dependency_impact(session_id=session_id)
    confidence = track_confidence_evolution(session_id=session_id)

    synthesis = "\n\n".join(
        p
        for p in [
            root.get("narrative"),
            replay.get("narrative"),
            uncertainty.get("narrative"),
            confidence.get("narrative"),
        ]
        if p
    )

    return {
        "ok": True,
        "phase": "10.1.4A",
        "synthesis": synthesis,
        "root_cause": root,
        "tradeoffs": tradeoffs,
        "replay_evolution": replay,
        "uncertainty": uncertainty,
        "dependency_impact": dependency,
        "confidence_evolution": confidence,
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }
