# SPDX-License-Identifier: Apache-2.0
"""Presence memory compaction — reduce long-term noise."""

from __future__ import annotations

from typing import Any

from aethos_core.presence.presence_memory import _load, _save


def compact_presence_memory(*, max_incidents: int = 80) -> dict[str, Any]:
    """Summarize recurring patterns and collapse low-value events."""
    data = _load()
    for key in ("incidents", "deployments", "validations", "recommendations", "replay_refs"):
        rows = list(data.get(key) or [])
        compacted = _compact_bucket(rows)
        data[key] = compacted[:max_incidents]

    data["compacted_patterns"] = _summarize_patterns(data)
    _save(data)
    return {
        "ok": True,
        "compacted_patterns": data.get("compacted_patterns"),
        "incidents_remaining": len(data.get("incidents") or []),
    }


def _compact_bucket(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for row in rows:
        detail = str(row.get("detail") or row.get("kind") or "")
        if _low_value(detail):
            continue
        key = detail[:80].lower()
        if key not in groups:
            groups[key] = {**row, "count": 1}
        else:
            groups[key]["count"] = int(groups[key].get("count") or 1) + 1
    out = list(groups.values())
    out.sort(key=lambda r: float(r.get("at") or 0), reverse=True)
    for row in out:
        if int(row.get("count") or 1) > 1:
            row["detail"] = f"{row.get('detail')} (×{row['count']} occurrences summarized)"
    return out


def _low_value(detail: str) -> bool:
    lower = detail.lower()
    return any(tok in lower for tok in ("repo_drift_scan", "recommendation_generated", "presence_cycle", "scheduled repo drift"))


def _summarize_patterns(data: dict[str, Any]) -> list[str]:
    patterns: list[str] = []
    for row in (data.get("incidents") or [])[:10]:
        if int(row.get("count") or 1) >= 2:
            patterns.append(f"Recurring: {row.get('detail')}")
    for row in (data.get("deployments") or [])[:5]:
        patterns.append(f"Deployment history: {row.get('detail')}")
    return patterns[:12]
