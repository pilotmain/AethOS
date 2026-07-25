# SPDX-License-Identifier: Apache-2.0
"""Reconciliation runtime — orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_reconciliation.infrastructure_alignment import assess_infrastructure_alignment
from aethos_core.runtime_reconciliation.operational_rechecks import run_operational_rechecks
from aethos_core.runtime_reconciliation.reconciliation_memory import record_reconciliation
from aethos_core.runtime_reconciliation.replay_alignment import assess_replay_alignment
from aethos_core.runtime_reconciliation.sustained_reconciliation import assess_sustained_reconciliation
from aethos_core.runtime_reconciliation.topology_alignment import assess_topology_alignment


def orchestrate_reconciliation(*, provider: str = "railway") -> dict[str, Any]:
    sustained = assess_sustained_reconciliation()
    topology = assess_topology_alignment()
    replay = assess_replay_alignment()
    infrastructure = assess_infrastructure_alignment(provider=provider)
    rechecks = run_operational_rechecks()
    memory = record_reconciliation(surface="runtime", aligned=topology.get("aligned", False))
    aligned = topology.get("aligned") and replay.get("aligned") and infrastructure.get("aligned")
    return {
        "sustained_reconciliation": sustained,
        "topology_alignment": topology,
        "replay_alignment": replay,
        "infrastructure_alignment": infrastructure,
        "operational_rechecks": rechecks,
        "memory": memory,
        "reconciled": aligned,
        "summary": (
            "Restart transition completed and runtime recovery is currently being reconciled "
            "across infrastructure, dependency health, telemetry freshness, and replay continuity signals."
        ),
        "narrative": (
            "Operational stability is improving, though sustained verification remains active."
        ),
    }
