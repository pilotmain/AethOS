# SPDX-License-Identifier: Apache-2.0
"""Persistent workspace outputs — completion watch and evolving summaries."""

from __future__ import annotations

from typing import Any

from aethos_core.agent_progression_memory.progression_store import _load, _save


def set_completion_watch(*, session_id: str = "default", enabled: bool = True) -> dict[str, Any]:
    data = _load(session_id)
    data["completion_watch"] = enabled
    _save(session_id, data)
    return {"completion_watch": enabled, "session_id": session_id}


def get_completion_watch(*, session_id: str = "default") -> bool:
    return bool(_load(session_id).get("completion_watch"))


def get_workspace_output_summary(*, session_id: str = "default") -> dict[str, Any]:
    data = _load(session_id)
    artifacts = list(data.get("artifacts") or [])
    return {
        "stage": int(data.get("stage") or 0),
        "completion_watch": bool(data.get("completion_watch")),
        "latest_artifact": artifacts[0] if artifacts else None,
        "artifact_count": len(artifacts),
    }
