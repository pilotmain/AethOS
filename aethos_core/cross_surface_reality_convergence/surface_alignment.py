# SPDX-License-Identifier: Apache-2.0
"""Surface alignment — compare operational subjects across surfaces."""

from __future__ import annotations

import re
from typing import Any


def _normalize(subject: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", subject.lower())
    return {t for t in tokens if len(t) > 2}


def _subject_overlap(a: str, b: str) -> float:
    ta, tb = _normalize(a), _normalize(b)
    if not ta or not tb:
        return 0.0
    shared = ta & tb
    return len(shared) / max(len(ta | tb), 1)


def extract_surface_subjects(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    """Collect primary subjects from each operational surface."""
    subjects: dict[str, str | None] = {
        "mission_control": None,
        "operational_context": None,
        "operational_memory": None,
        "telegram": None,
        "relational": None,
        "reconciled": None,
    }

    try:
        from aethos_core.human_centered.continuity_memory import load_continuity_memory

        hc = load_continuity_memory(session_id=session_id)
        subjects["mission_control"] = hc.get("focus") or hc.get("current_system_focus")
    except Exception:
        pass

    try:
        from aethos_core.operational_context_memory.context_store import recall_operational_context

        stored = recall_operational_context(session_id=session_id)
        if stored:
            subjects["operational_context"] = (
                stored.get("deployment_subject")
                or stored.get("latest_focus")
                or stored.get("latest_investigation")
            )
            if session_id.startswith("tg-"):
                subjects["telegram"] = stored.get("latest_investigation") or stored.get("latest_focus")
    except Exception:
        pass

    try:
        from aethos_core.conversation.operational_memory import build_continuity_context

        continuity = build_continuity_context(session_id=session_id)
        if continuity.get("has_memory"):
            subjects["operational_memory"] = continuity.get("last_focus")
    except Exception:
        pass

    if channel == "telegram" or session_id.startswith("tg-"):
        if not subjects["telegram"]:
            subjects["telegram"] = subjects["operational_context"] or subjects["operational_memory"]

    try:
        from aethos_core.operational_context_memory.memory_precedence import reconcile_memory_layers

        reconciliation = reconcile_memory_layers(session_id=session_id, channel=channel)
        subjects["reconciled"] = reconciliation.get("primary_subject")
    except Exception:
        pass

    active = {k: v for k, v in subjects.items() if v}
    return {"subjects": subjects, "active_subjects": active}


def score_surface_alignment(*, surface_subjects: dict[str, Any]) -> dict[str, Any]:
    """Score whether active surfaces agree on operational reality."""
    active: dict[str, str] = surface_subjects.get("active_subjects") or {}
    if not active:
        return {
            "alignment_score": 0.5,
            "surfaces_aligned": True,
            "competing_subjects": [],
            "active_surface_count": 0,
            "summary": "No cross-surface subjects — alignment neutral.",
        }

    values = list(active.values())
    if len(values) == 1:
        return {
            "alignment_score": 0.85,
            "surfaces_aligned": True,
            "competing_subjects": [],
            "active_surface_count": 1,
            "summary": "Single-surface continuity — alignment assumed.",
        }

    anchor = values[0]
    overlaps = [_subject_overlap(anchor, v) for v in values[1:]]
    min_overlap = min(overlaps) if overlaps else 1.0
    competing = [v for v in values if _subject_overlap(anchor, v) < 0.35]

    aligned = min_overlap >= 0.35 and len(competing) <= 1
    score = round(min(0.95, 0.55 + min_overlap * 0.4), 2)

    return {
        "alignment_score": score,
        "surfaces_aligned": aligned,
        "competing_subjects": list(dict.fromkeys(competing)),
        "active_surface_count": len(active),
        "min_overlap": round(min_overlap, 2),
        "summary": (
            "Cross-surface subjects aligned."
            if aligned
            else "Cross-surface subject drift detected — confidence should be reduced."
        ),
    }
