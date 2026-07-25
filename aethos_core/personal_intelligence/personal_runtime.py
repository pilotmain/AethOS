# SPDX-License-Identifier: Apache-2.0
"""Personal intelligence — opt-in, explainable, deletable operator understanding."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path


def _personal_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "personal_intelligence"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _opt_in_path(session_id: str) -> Path:
    return _personal_root() / f"opt_in_{session_id}.json"


def _profile_path(session_id: str) -> Path:
    return _personal_root() / f"profile_{session_id}.json"


def get_personal_intelligence_status(*, session_id: str = "default") -> dict[str, Any]:
    opted = _opt_in_path(session_id).is_file()
    profile = {}
    if opted and _profile_path(session_id).is_file():
        try:
            profile = json.loads(_profile_path(session_id).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "ok": True,
        "opted_in": opted,
        "profile": profile,
        "governance": {
            "opt_in": True,
            "explainable": True,
            "deletable": True,
            "locally_controllable": True,
        },
        "features": {
            "preferred_explanation_style": profile.get("explanation_style", "balanced"),
            "stress_frustration_awareness": opted,
            "work_rhythm_understanding": opted,
            "learning_adaptation": opted,
            "operational_preference_memory": opted,
            "relationship_continuity": opted,
        },
        "autonomous_execution_blocked": True,
    }


def opt_in_personal_intelligence(*, session_id: str = "default", explanation_style: str = "balanced") -> dict[str, Any]:
    _opt_in_path(session_id).write_text(json.dumps({"enabled": True, "at": time()}, indent=2), encoding="utf-8")
    profile = {
        "explanation_style": explanation_style,
        "interruption_budget": 3,
        "prefers_brevity_under_stress": True,
        "updated_at": time(),
    }
    _profile_path(session_id).write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return {"ok": True, "opted_in": True, "profile": profile}


def delete_personal_intelligence(*, session_id: str = "default") -> dict[str, Any]:
    for p in (_opt_in_path(session_id), _profile_path(session_id)):
        if p.is_file():
            p.unlink()
    return {"ok": True, "deleted": True, "opted_in": False}


def adapt_to_operator(*, session_id: str = "default", signals: dict[str, Any] | None = None) -> dict[str, Any]:
    """Adapt interaction based on personal profile and human signals."""
    status = get_personal_intelligence_status(session_id=session_id)
    if not status.get("opted_in"):
        return {"adapted": False, "reason": "Personal intelligence not opted in"}
    profile = status.get("profile") or {}
    sig = signals or {}
    adaptations: list[str] = []
    if sig.get("frustrated") and profile.get("prefers_brevity_under_stress"):
        adaptations.append("Reduce verbosity under stress")
    if profile.get("explanation_style") == "beginner":
        adaptations.append("Use explanatory depth")
    elif profile.get("explanation_style") == "expert":
        adaptations.append("Use concise technical depth")
    return {"adapted": True, "adaptations": adaptations, "profile": profile}


def clear_personal_intelligence_for_tests() -> None:
    root = _personal_root()
    for p in root.glob("*.json"):
        p.unlink()
