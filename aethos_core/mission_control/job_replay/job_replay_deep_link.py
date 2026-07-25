# SPDX-License-Identifier: Apache-2.0
"""FIX 137B — stable deep links into job replay steps."""

from __future__ import annotations

import hashlib
from typing import Any

JOB_REPLAY_DEEP_LINK_FIX: str = "FIX 137B"


def replay_link_key(
    *,
    source: str,
    lane: str = "",
    action: str = "",
    timestamp: str = "",
    anchor: str = "",
) -> str:
    raw = "|".join([source, lane, action, str(timestamp or ""), anchor])
    return f"rpl-{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


def timeline_link_ref(*, lane: str, action: str, timestamp: str) -> str:
    return f"timeline:{lane}:{action}:{timestamp}"


def audit_link_ref(*, approval_id: str) -> str:
    return f"audit:{approval_id}"


def evidence_link_ref(*, recorded_at: str, phase: str, source_file: str = "") -> str:
    return f"evidence:{recorded_at}:{phase}:{source_file}"


def link_key_from_candidate(candidate: dict[str, Any]) -> str:
    anchor = str(
        candidate.get("approval_id")
        or candidate.get("event_id")
        or candidate.get("job_id")
        or ""
    )
    return replay_link_key(
        source=str(candidate.get("source") or ""),
        lane=str(candidate.get("lane") or ""),
        action=str(candidate.get("action") or ""),
        timestamp=str(candidate.get("timestamp") or ""),
        anchor=anchor,
    )


def link_refs_from_candidate(candidate: dict[str, Any]) -> dict[str, str]:
    refs: dict[str, str] = {}
    source = str(candidate.get("source") or "")
    lane = str(candidate.get("lane") or "")
    action = str(candidate.get("action") or "")
    timestamp = str(candidate.get("timestamp") or "")

    if source in {"cross_lane_timeline", "software_delivery_timeline"} and action:
        refs["timeline"] = timeline_link_ref(lane=lane, action=action, timestamp=timestamp)
    if candidate.get("approval_id"):
        refs["audit"] = audit_link_ref(approval_id=str(candidate["approval_id"]))
    if candidate.get("job_id"):
        refs["job"] = f"job:{candidate['job_id']}"
    return refs


def build_link_index(steps: list[dict[str, Any]]) -> dict[str, int]:
    index: dict[str, int] = {}
    for step in steps:
        idx = int(step.get("step_index", 0))
        key = str(step.get("link_key") or "")
        if key:
            index[key] = idx
        for alias in (step.get("link_refs") or {}).values():
            if alias:
                index[str(alias)] = idx
        for receipt in step.get("receipts") or []:
            if not isinstance(receipt, dict):
                continue
            ref = evidence_link_ref(
                recorded_at=str(receipt.get("recorded_at") or ""),
                phase=str(receipt.get("phase") or receipt.get("status") or "receipt"),
                source_file=str(receipt.get("source_file") or ""),
            )
            index[ref] = idx
            receipt["evidence_link_ref"] = ref
    return index


def resolve_step_index(*, steps: list[dict[str, Any]], link_index: dict[str, int], link: str) -> int | None:
    if not link:
        return None
    if link in link_index:
        return link_index[link]
    if link.isdigit():
        n = int(link)
        if 0 <= n < len(steps):
            return n
    needle = link.lower()
    for step in steps:
        if str(step.get("link_key") or "").lower() == needle:
            return int(step["step_index"])
        refs = step.get("link_refs") or {}
        if any(str(v).lower() == needle for v in refs.values()):
            return int(step["step_index"])
    return None
