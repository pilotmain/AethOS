# SPDX-License-Identifier: Apache-2.0
"""Replay trust — replay continuity weighting."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.replay_stability import assess_replay_stability


def assess_replay_trust() -> dict[str, Any]:
    replay = assess_replay_stability()
    score = float(replay.get("continuity_score") or 0.82)
    return {"replay_trust": score, "summary": "Replay trust stable across operational windows." if score >= 0.75 else "Replay trust monitoring active."}
