# SPDX-License-Identifier: Apache-2.0
"""Pod health — pod lifecycle verification."""

from __future__ import annotations

from typing import Any


def assess_pod_health(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    pods = runtime_snapshot.get("pods") or []
    if not isinstance(pods, list):
        pods = []
    ready = [p for p in pods if str(p.get("phase", "")).lower() in ("running", "ready") and p.get("ready")]
    pending = [p for p in pods if str(p.get("phase", "")).lower() in ("pending", "crashloopbackoff", "failed")]
    return {
        "pod_count": len(pods),
        "ready_count": len(ready),
        "pending_count": len(pending),
        "all_ready": len(pending) == 0 and len(ready) > 0,
        "summary": f"{len(ready)}/{len(pods)} pods ready." if pods else "No pods in snapshot.",
    }
