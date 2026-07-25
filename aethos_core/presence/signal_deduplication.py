# SPDX-License-Identifier: Apache-2.0
"""Signal deduplication — collapse redundant feed items."""

from __future__ import annotations

import re
from typing import Any


def deduplicate_signals(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse duplicate/redundant operational feed items."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        key = _fingerprint(event)
        groups.setdefault(key, []).append(event)

    merged: list[dict[str, Any]] = []
    for key, rows in groups.items():
        if len(rows) == 1:
            merged.append(rows[0])
            continue
        merged.append(_merge_group(key, rows))
    merged.sort(key=lambda e: float(e.get("at") or e.get("created_at") or 0), reverse=True)
    return merged


def _fingerprint(event: dict[str, Any]) -> str:
    source = str(event.get("source") or "unknown")
    summary = _normalize_summary(str(event.get("summary") or ""))
    provider = str(event.get("provider") or "")
    kind = str(event.get("kind") or source)
    if "repo_drift" in summary or "repo_drift" in kind:
        return "internal:repo_drift_scan"
    if "recommendation_generated" in summary:
        return f"internal:recommendation:{summary[:40]}"
    if source == "recommendation":
        rid = event.get("recommendation_id")
        if rid:
            return f"rec:{rid}"
    return f"{source}:{kind}:{summary[:60]}:{provider}"


def _normalize_summary(text: str) -> str:
    t = re.sub(r"\s+", " ", text.lower().strip())
    t = re.sub(r"#\d+", "#N", t)
    return t[:120]


def _merge_group(key: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows.sort(key=lambda r: float(r.get("at") or r.get("created_at") or 0), reverse=True)
    base = dict(rows[0])
    count = len(rows)
    base["dedupe_count"] = count
    base["recurrence"] = max(int(base.get("recurrence") or 0), count)
    if key == "internal:repo_drift_scan":
        base["summary"] = f"Repeated repository drift observed across {count} scans"
        base["signal_class"] = "internal_substrate"
        base["severity"] = "low"
    elif count > 1:
        base["summary"] = f"{base.get('summary')} (×{count} similar signals)"
    base["deduplicated"] = True
    return base
