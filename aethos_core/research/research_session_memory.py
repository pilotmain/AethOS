# SPDX-License-Identifier: Apache-2.0
"""Per-chat research memory — last comparison replay for HTML follow-ups."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any


def _store_path(session_id: str) -> Path:
    from aethos_core.research.research_artifacts import research_artifacts_root

    safe = (session_id or "default").strip().replace("/", "_")[:128]
    root = research_artifacts_root() / "session_memory"
    root.mkdir(parents=True, exist_ok=True)
    return root / f"{safe}.json"


def remember_research_run(
    *,
    session_id: str,
    replay_id: str,
    query: str,
    comparison: bool = False,
    subjects: tuple[str, str] | None = None,
) -> None:
    from aethos_core.channels.session_alias import resolve_canonical_session_id

    canonical = resolve_canonical_session_id(session_id)
    payload = {
        "replay_id": replay_id,
        "query": query,
        "comparison": comparison,
        "subjects": list(subjects) if subjects else None,
        "updated_at": time(),
    }
    try:
        _store_path(canonical).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def get_last_research_run(session_id: str) -> dict[str, Any] | None:
    from aethos_core.channels.session_alias import session_ids_for_lookup

    best: dict[str, Any] | None = None
    best_ts = -1.0
    for sid in session_ids_for_lookup(session_id):
        path = _store_path(sid)
        if not path.is_file():
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                continue
            ts = float(raw.get("updated_at") or 0)
            if ts >= best_ts:
                best = raw
                best_ts = ts
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return best
