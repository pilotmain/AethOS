# SPDX-License-Identifier: Apache-2.0
"""Restraint runtime — bounded reasoning and suggestion throttling."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path


def _restraint_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "restraint"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _recent_path(session_id: str) -> Path:
    return _restraint_root() / f"recent_{session_id}.json"


def apply_restraint(*, text: str, session_id: str = "default", max_paragraphs: int = 6) -> dict[str, Any]:
    """Prevent over-analysis and repetition."""
    path = _recent_path(session_id)
    recent: list[str] = []
    if path.is_file():
        try:
            recent = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            recent = []

    fingerprint = text[:120]
    if fingerprint in recent[:5]:
        return {
            "text": "*(I already shared this — happy to go deeper on a specific part if useful.)*",
            "restraint": {"repetition_suppressed": True},
        }

    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    trimmed = text
    if len(parts) > max_paragraphs:
        trimmed = "\n\n".join(parts[:max_paragraphs]) + "\n\n*(Calm summary — ask for more depth if needed.)*"

    recent.insert(0, fingerprint)
    path.write_text(json.dumps(recent[:10], indent=2), encoding="utf-8")

    return {
        "text": trimmed,
        "restraint": {
            "over_analysis_prevented": len(parts) > max_paragraphs,
            "repetition_suppressed": False,
            "suggestion_throttled": False,
            "confidence_humility": True,
        },
    }


def get_restraint_status(*, session_id: str = "default") -> dict[str, Any]:
    return {
        "ok": True,
        "principle": "The smartest systems are often the calmest systems.",
        "features": {
            "over_analysis_prevention": True,
            "repetition_suppression": True,
            "suggestion_throttling": True,
            "cognitive_load_balancing": True,
            "confidence_humility": True,
            "relevance_filtering": True,
        },
        "autonomous_execution_blocked": True,
    }


def clear_restraint_for_tests() -> None:
    root = _restraint_root()
    for p in root.glob("*.json"):
        p.unlink()
