# SPDX-License-Identifier: Apache-2.0
"""Human runtime replay — observable living intelligence artifacts."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path


def _artifacts_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "human_runtime_artifacts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _write_artifact(name: str, payload: dict[str, Any]) -> Path:
    path = _artifacts_root() / f"{name}.json"
    record = {"artifact": name, "at": time(), **payload}
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return path


def snapshot_human_runtime_state(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.living_companion_runtime import get_living_companion_overview

    overview = get_living_companion_overview(session_id=session_id)
    _write_artifact("human_runtime_state", {"session_id": session_id, "state": overview})
    return {"ok": True, "artifact": "human_runtime_state", "session_id": session_id}


def record_living_presence_cycle(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.presence.live.live_presence_runtime import get_live_operational_stream

    cycle = get_live_operational_stream(session_id=session_id, limit=12)
    _write_artifact("living_presence_cycle", {"session_id": session_id, "cycle": cycle})
    return {"ok": True, "artifact": "living_presence_cycle"}


def record_conversational_memory_trace(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.conversation.continuity_renderer import render_continuity_resume

    trace = render_continuity_resume(session_id=session_id)
    _write_artifact("conversational_memory_trace", {"session_id": session_id, "trace": trace})
    return {"ok": True, "artifact": "conversational_memory_trace"}


def record_continuity_memory_snapshot(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.human_centered.continuity_memory import get_continuity_transparency

    snap = get_continuity_transparency(session_id=session_id)
    _write_artifact("continuity_memory_snapshot", {"session_id": session_id, "snapshot": snap})
    return {"ok": True, "artifact": "continuity_memory_snapshot"}


def record_copilot_reasoning_trace(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.copilot.copilot_runtime import generate_operational_hypotheses

    trace = generate_operational_hypotheses(session_id=session_id)
    _write_artifact("copilot_reasoning_trace", {"session_id": session_id, "trace": trace})
    return {"ok": True, "artifact": "copilot_reasoning_trace"}


def record_explainability_snapshot(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.trust.world_class_explainability import build_world_class_explanation

    snap = build_world_class_explanation(session_id=session_id)
    _write_artifact("explainability_snapshot", {"session_id": session_id, "snapshot": snap})
    return {"ok": True, "artifact": "explainability_snapshot"}


def get_human_runtime_replay(*, session_id: str = "default") -> dict[str, Any]:
    """Collect all human runtime replay artifacts."""
    snapshot_human_runtime_state(session_id=session_id)
    record_living_presence_cycle(session_id=session_id)
    record_conversational_memory_trace(session_id=session_id)
    record_continuity_memory_snapshot(session_id=session_id)
    record_copilot_reasoning_trace(session_id=session_id)
    record_explainability_snapshot(session_id=session_id)

    artifacts: dict[str, Any] = {}
    root = _artifacts_root()
    for name in (
        "human_runtime_state",
        "living_presence_cycle",
        "conversational_memory_trace",
        "continuity_memory_snapshot",
        "copilot_reasoning_trace",
        "explainability_snapshot",
    ):
        path = root / f"{name}.json"
        if path.is_file():
            try:
                artifacts[name] = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                artifacts[name] = {"error": "unreadable"}

    return {
        "ok": True,
        "session_id": session_id,
        "artifacts": artifacts,
        "artifact_dir": str(root),
        "readonly": True,
        "autonomous_execution_blocked": True,
        "replayed_at": time(),
    }


def clear_human_runtime_artifacts_for_tests() -> None:
    root = _artifacts_root()
    for p in root.glob("*.json"):
        p.unlink()
