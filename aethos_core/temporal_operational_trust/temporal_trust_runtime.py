# SPDX-License-Identifier: Apache-2.0
"""Temporal trust runtime — trust evolution orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_operational_trust.dependency_trust import assess_dependency_trust
from aethos_core.temporal_operational_trust.replay_trust import assess_replay_trust
from aethos_core.temporal_operational_trust.topology_trust import assess_topology_trust
from aethos_core.temporal_operational_trust.trust_decay_runtime import assess_trust_decay
from aethos_core.temporal_operational_trust.trust_progression import evolve_trust_progression


def orchestrate_temporal_trust() -> dict[str, Any]:
    progression = evolve_trust_progression()
    replay = assess_replay_trust()
    dependency = assess_dependency_trust()
    topology = assess_topology_trust()
    decay = assess_trust_decay()
    temporally_trusted = progression.get("strengthening") and decay.get("trust_erosion_bounded")
    return {
        "trust_progression": progression,
        "replay_trust": replay,
        "dependency_trust": dependency,
        "topology_trust": topology,
        "trust_decay": decay,
        "temporally_trusted": temporally_trusted,
        "summary": progression.get("summary", "Temporal operational trust assessing."),
    }
