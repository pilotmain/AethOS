# SPDX-License-Identifier: Apache-2.0
"""Replay integrity — validate replay continuity."""

from __future__ import annotations

from typing import Any


def assess_replay_integrity(
    *,
    replays: list[dict[str, Any]] | None = None,
    expected_coverage_hours: float = 48.0,
) -> dict[str, Any]:
    """Evaluate replay continuity and gap detection."""
    rows = list(replays or [])
    if not rows:
        return {
            "integrity": "missing",
            "replay_gaps": 1,
            "coverage_ratio": 0.0,
            "summary": "No operational replays available.",
            "repair_recommended": True,
        }

    gap_count = 0
    for row in rows:
        cycle = row.get("cycle") or row
        if not cycle.get("anomalies") and not cycle.get("observations"):
            gap_count += 1
        if not row.get("replay_id") and not row.get("created_at"):
            gap_count += 1

    coverage = min(1.0, len(rows) / max(expected_coverage_hours / 12, 1))
    integrity = "healthy"
    if gap_count >= 2:
        integrity = "degraded"
    elif gap_count == 1:
        integrity = "partial"
    if len(rows) < 2:
        integrity = "incomplete"

    return {
        "integrity": integrity,
        "replay_gaps": gap_count,
        "coverage_ratio": round(coverage, 2),
        "replay_count": len(rows),
        "summary": f"Replay integrity {integrity} ({len(rows)} records, {gap_count} gap(s)).",
        "repair_recommended": gap_count >= 1 or integrity != "healthy",
    }
