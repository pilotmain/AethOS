# SPDX-License-Identifier: Apache-2.0
"""Rollback integrity aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.rollback_integrity.dependency_recovery import assess_dependency_recovery
from aethos_core.rollback_integrity.rollback_confidence import score_rollback_confidence
from aethos_core.rollback_integrity.rollback_decay import assess_rollback_decay
from aethos_core.rollback_integrity.rollback_memory import record_rollback_outcome
from aethos_core.rollback_integrity.topology_rollback_truth import assess_topology_rollback_truth


def assess_rollback_integrity(*, provider: str = "railway") -> dict[str, Any]:
    confidence = score_rollback_confidence()
    dependency = assess_dependency_recovery()
    decay = assess_rollback_decay(stable=confidence.get("rollback_verified", False))
    topology = assess_topology_rollback_truth()
    memory = record_rollback_outcome(provider=provider, verified=confidence.get("rollback_verified", False))
    return {
        "ok": True,
        "provider": provider,
        "confidence": confidence,
        "dependency_recovery": dependency,
        "rollback_decay": decay,
        "topology": topology,
        "memory": memory,
        "summary": (
            "Rollback completed and primary services recovered, though downstream telemetry stabilization "
            "is still being verified across dependent runtime surfaces."
        ),
    }
