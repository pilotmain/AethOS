# SPDX-License-Identifier: Apache-2.0
"""LifeOS — personal operational layer (opt-in, auditable)."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path


def _life_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "life"
    root.mkdir(parents=True, exist_ok=True)
    return root


DOMAINS = frozenset({
    "calendar", "reminders", "goals", "focus", "travel",
    "learning", "health_routines", "finances", "relationships",
})


def get_lifeos_status(*, session_id: str = "default") -> dict[str, Any]:
    path = _life_root() / f"opt_in_{session_id}.json"
    opted_in = path.is_file() and json.loads(path.read_text()).get("enabled") is True
    return {
        "ok": True,
        "opted_in": opted_in,
        "domains": sorted(DOMAINS),
        "governance": {
            "opt_in": True,
            "explainable": True,
            "revocable": True,
            "auditable": True,
        },
        "autonomous_execution_blocked": True,
    }


def opt_in_lifeos(*, session_id: str = "default", domains: list[str] | None = None) -> dict[str, Any]:
    selected = [d for d in (domains or list(DOMAINS)) if d in DOMAINS]
    record = {"enabled": True, "domains": selected, "opted_in_at": time()}
    (_life_root() / f"opt_in_{session_id}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return {"ok": True, "opted_in": True, "domains": selected}


def revoke_lifeos(*, session_id: str = "default") -> dict[str, Any]:
    path = _life_root() / f"opt_in_{session_id}.json"
    if path.is_file():
        path.unlink()
    return {"ok": True, "opted_in": False, "revoked_at": time()}


def summarize_life_domain(*, domain: str, session_id: str = "default") -> dict[str, Any]:
    status = get_lifeos_status(session_id=session_id)
    if not status.get("opted_in"):
        return {
            "ok": False,
            "reason": "LifeOS is opt-in only. Enable from Mission Control or ask to opt in.",
            "autonomous_execution_blocked": True,
        }
    if domain not in DOMAINS:
        return {"ok": False, "reason": f"Unknown domain: {domain}"}
    return {
        "ok": True,
        "domain": domain,
        "summary": f"LifeOS {domain} — governed personal operations (no silent actions).",
        "actions_require_approval": True,
        "autonomous_execution_blocked": True,
    }
