# SPDX-License-Identifier: Apache-2.0
"""Semantic diversification — varied operational storytelling structures."""

from __future__ import annotations

import hashlib
from typing import Any


def _pick_index(*, session_id: str, salt: str, count: int) -> int:
    digest = hashlib.sha256(f"{session_id}:{salt}".encode()).hexdigest()
    return int(digest[:8], 16) % max(count, 1)


def compose_improvement_narrative(
    *,
    concern: str,
    signals: list[str],
    closing: str,
    session_id: str = "default",
) -> str:
    variants = [
        (
            f"Compared to the earlier **{concern}** concern, the trajectory looks better.\n\n"
            f"Strongest signals:\n" + "\n".join(f"- {s}" for s in signals) + f"\n\n{closing}"
        ),
        (
            f"The **{concern}** thread is easing — nothing alarming is accelerating right now.\n\n"
            + "\n".join(f"- {s}" for s in signals)
            + f"\n\n{closing}"
        ),
        (
            f"Recovery momentum on **{concern}** is holding.\n\n"
            f"What stands out:\n" + "\n".join(f"- {s}" for s in signals) + f"\n\n{closing}"
        ),
    ]
    return variants[_pick_index(session_id=session_id, salt="improved", count=len(variants))]


def compose_stability_narrative(
    *,
    subject: str,
    opening: str,
    closing: str,
    session_id: str = "default",
) -> str:
    variants = [
        f"{opening}\n\n**{subject}** looks stable from here — recovery, dependencies, and telemetry are all behaving.\n\n{closing}",
        f"From what I can see, **{subject}** is holding steady.\n\n{opening} {closing}",
        f"**{subject}** reads stable across current checks.\n\nRecovery and dependency signals are clean. {closing}",
    ]
    return variants[_pick_index(session_id=session_id, salt="stable", count=len(variants))]


def compose_monitoring_narrative(
    *,
    sensitive: str,
    session_id: str = "default",
) -> str:
    variants = [
        (
            f"If you want the highest leverage monitoring next, I'd watch:\n"
            f"- **{sensitive}** over long sessions\n"
            "- topology drift after recovery\n"
            "- dependency persistence under load\n"
            "- late regression after stabilization"
        ),
        (
            f"The most sensitive areas right now look like **{sensitive}**, topology drift, "
            "and whether recovery actually persists under sustained load."
        ),
        (
            f"I'd prioritize **{sensitive}** and downstream dependency persistence before adding "
            "generic infrastructure monitors."
        ),
    ]
    return variants[_pick_index(session_id=session_id, salt="monitoring", count=len(variants))]


def assess_semantic_diversification(*, sample_count: int = 3) -> dict[str, Any]:
    return {
        "semantic_variants_enabled": True,
        "structure_rotation": True,
        "variant_pools": sample_count,
        "summary": "Semantic narrative diversification active — structural storytelling variation enabled.",
    }
