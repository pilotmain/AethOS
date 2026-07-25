# SPDX-License-Identifier: Apache-2.0
"""Replay window validation — replay continuity."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_reconciliation.topology_alignment import assess_topology_alignment


def validate_replay_window() -> dict[str, Any]:
    from aethos_core.sustained_verification.replay_stability import assess_replay_stability

    replay = assess_replay_stability()
    return {
        **replay,
        "aligned": replay.get("replay_stable", False),
        "summary": "Replay continuity aligned across operational windows." if replay.get("replay_stable") else "Replay continuity alignment monitoring active.",
    }
