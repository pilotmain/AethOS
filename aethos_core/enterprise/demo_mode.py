# SPDX-License-Identifier: Apache-2.0
"""Demo mode — safe sample data without real credentials."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.enterprise.paths import demo_mode_root


def _state_path():
    return demo_mode_root() / "state.json"


def is_demo_mode() -> bool:
    path = _state_path()
    if not path.is_file():
        return False
    try:
        return bool(json.loads(path.read_text(encoding="utf-8")).get("enabled"))
    except (OSError, json.JSONDecodeError):
        return False


def demo_status() -> dict[str, Any]:
    enabled = is_demo_mode()
    samples = _load_samples() if enabled else {}
    return {
        "enabled": enabled,
        "label": "DEMO DATA",
        "warning": "All demo artifacts are synthetic — not from live providers.",
        "sample_counts": {k: len(v) if isinstance(v, list) else 1 for k, v in samples.items()},
    }


def enable_demo_mode() -> dict[str, Any]:
    root = demo_mode_root()
    root.mkdir(parents=True, exist_ok=True)
    samples = _seed_demo_samples()
    _state_path().write_text(
        json.dumps({"enabled": True, "enabled_at": time(), "samples_file": "samples.json"}, indent=2),
        encoding="utf-8",
    )
    (root / "samples.json").write_text(json.dumps(samples, indent=2), encoding="utf-8")
    return {"ok": True, "enabled": True, "label": "DEMO DATA", "samples": {k: len(v) for k, v in samples.items()}}


def disable_demo_mode() -> dict[str, Any]:
    path = _state_path()
    if path.is_file():
        path.unlink()
    samples = demo_mode_root() / "samples.json"
    if samples.is_file():
        samples.unlink()
    return {"ok": True, "enabled": False}


def get_demo_overlay() -> dict[str, Any]:
    """Demo data overlay for Mission Control — clearly marked."""
    if not is_demo_mode():
        return {}
    return {"demo": True, "label": "DEMO DATA", **_load_samples()}


def _load_samples() -> dict[str, Any]:
    path = demo_mode_root() / "samples.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _seed_demo_samples() -> dict[str, Any]:
    now = time()
    return {
        "provider_events": [
            {"at": now, "source": "railway", "summary": "[DEMO] Deployment restart observed on staging", "demo": True},
            {"at": now - 3600, "source": "github", "summary": "[DEMO] Workflow rerun completed with warnings", "demo": True},
        ],
        "recommendations": [
            {
                "recommendation_id": f"demo-rec-{uuid4().hex[:8]}",
                "title": "[DEMO] Review workflow convergence",
                "suggested_action": "Generate governed engineering preflight for demo workflow fix?",
                "confidence": 0.72,
                "approval_required": True,
                "demo": True,
            }
        ],
        "research_artifacts": [
            {"artifact_id": f"demo-res-{uuid4().hex[:8]}", "title": "[DEMO] Web research: operational AI platforms", "demo": True},
        ],
        "engineering_preflights": [
            {"preflight_id": f"demo-pf-{uuid4().hex[:8]}", "task": {"title": "[DEMO] Sandbox patch validation"}, "status": "pending", "demo": True},
        ],
        "operational_replay": [
            {"replay_id": f"demo-replay-{uuid4().hex[:8]}", "summary": "[DEMO] Reality loop: 2 anomalies, 1 recommendation", "demo": True},
        ],
        "reliability": {
            "truth_state": "degraded_confidence",
            "bounded_confidence": 0.68,
            "summary": "[DEMO] Sample reliability state for onboarding",
            "demo": True,
        },
    }


def clear_demo_mode_for_tests() -> None:
    disable_demo_mode()
