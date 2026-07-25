# SPDX-License-Identifier: Apache-2.0
"""Process observer — runtime process awareness."""

from __future__ import annotations

from typing import Any


def observe_processes(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    processes = runtime_snapshot.get("processes") or runtime_snapshot.get("containers") or []
    if not isinstance(processes, list):
        processes = []
    active = [p for p in processes if str(p.get("status", "")).lower() in ("healthy", "running", "up")]
    return {
        "process_count": len(processes),
        "active_count": len(active),
        "summary": f"{len(active)}/{len(processes)} supervised processes active.",
    }
