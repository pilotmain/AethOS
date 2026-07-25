# SPDX-License-Identifier: Apache-2.0
"""Temporal confidence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_confidence.confidence_evolution import evolve_confidence
from aethos_core.temporal_confidence.convergence_confidence import assess_stabilization_confidence
from aethos_core.temporal_confidence.degradation_confidence_decay import assess_degradation_confidence_decay
from aethos_core.temporal_confidence.replay_confidence import assess_replay_confidence
from aethos_core.temporal_confidence.temporal_trust_memory import record_trust_evolution
from aethos_core.temporal_confidence.topology_confidence import assess_topology_confidence


def assess_temporal_confidence() -> dict[str, Any]:
    evolution = evolve_confidence()
    stabilization = assess_stabilization_confidence()
    replay = assess_replay_confidence()
    topology = assess_topology_confidence()
    decay = assess_degradation_confidence_decay()
    memory = record_trust_evolution(score=evolution.get("current_score", 0.84))
    return {
        "ok": True,
        "confidence_evolution": evolution,
        "stabilization_confidence": stabilization,
        "replay_confidence": replay,
        "topology_confidence": topology,
        "degradation_decay": decay,
        "trust_memory": memory,
        "temporally_qualified": evolution.get("improving") and decay.get("confidence_erosion_bounded"),
        "summary": evolution.get("summary", "Temporal confidence assessing."),
    }
