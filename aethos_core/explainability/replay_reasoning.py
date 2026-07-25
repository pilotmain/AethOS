# SPDX-License-Identifier: Apache-2.0
"""Replay reasoning — why replay is incomplete."""

from __future__ import annotations

from typing import Any


def explain_replay_gaps(*, replay_integrity: dict[str, Any], replay_confidence: dict[str, Any] | None = None) -> str:
    parts = ["Replay status explained:"]
    integrity = str(replay_integrity.get("integrity") or "unknown")
    parts.append(f"- Integrity: {integrity}")
    gaps = int(replay_integrity.get("replay_gaps") or 0)
    if gaps:
        parts.append(f"- {gaps} replay gap(s) detected — causal chain may be incomplete.")
    if replay_integrity.get("repair_recommended"):
        parts.append("- Replay repair recommended (readonly reconstruction available).")
    rc = replay_confidence or {}
    if rc.get("replay_confidence") is not None:
        parts.append(f"- Replay confidence: {rc['replay_confidence']:.2f} (bounded).")
    if integrity == "healthy":
        parts.append("- Replay continuity verified.")
    return "\n".join(parts)
