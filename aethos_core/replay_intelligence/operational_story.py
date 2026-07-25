# SPDX-License-Identifier: Apache-2.0
"""Operational story — operator-readable incident narrative."""

from __future__ import annotations

from typing import Any


def build_operational_story(*, chains: list[dict[str, Any]], events: list[dict[str, Any]], window_hours: int = 48) -> str:
    """Produce operator-readable causal narrative."""
    if chains:
        primary = chains[0]
        steps = primary.get("steps") or []
        narrative = " → ".join(steps)
        conf = primary.get("confidence", 0.5)
        return (
            f"Over the last {window_hours}h, AethOS reconstructed this operational sequence:\n"
            f"{narrative}.\n"
            f"Replay confidence: {conf:.2f} (bounded, readonly)."
        )

    summaries = [str(e.get("summary") or e.get("detail") or "") for e in events[:5] if e.get("summary") or e.get("detail")]
    if summaries:
        return f"Operational timeline ({window_hours}h): {'; '.join(summaries[:3])}."
    return f"No reconstructable operational sequence in the last {window_hours}h."
