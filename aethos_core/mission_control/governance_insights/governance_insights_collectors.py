# SPDX-License-Identifier: Apache-2.0
"""FIX 143 — collect governance signals for meta-governance analysis."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def _parse_ts(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _read_json_dir(relative: str, *, limit: int = 30) -> list[dict[str, Any]]:
    root = _DATA_ROOT / relative
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        if len(rows) >= limit:
            break
    return rows


def collect_governance_signals(*, session_id: str, limit: int = 200) -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.approval_audit_service import list_ui_approval_audits
    from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload
    from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
        list_operational_memory_records,
    )
    from aethos_core.mission_control.operational_memory.cross_session.cross_session_service import (
        build_cross_session_operational_memory,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    audits = list_ui_approval_audits(session_id=None, limit=limit)
    focal_audits = [a for a in audits if str(a.get("session_id") or "") == sid]
    records = list_operational_memory_records(limit=limit)
    inbox = approval_inbox_payload(session_id=sid)
    rollbacks = _read_json_dir("railway_production_rollback_escalations", limit=20)
    rollouts = _read_json_dir("railway_production_rollout_journal", limit=20)
    incidents = _read_json_dir("railway_production_incidents", limit=20)

    cross_session = build_cross_session_operational_memory(session_id=sid, ingest_current=False)

    gate_counter: Counter[str] = Counter()
    outcome_counter: Counter[str] = Counter()
    session_approval_load: Counter[str] = Counter()
    for audit in audits:
        gate = str(audit.get("gate_id") or "unknown")
        gate_counter[gate] += 1
        outcome = str(audit.get("outcome") or audit.get("status") or "unknown")
        outcome_counter[outcome] += 1
        session_approval_load[str(audit.get("session_id") or "unknown")] += 1

    record_gate_counter: Counter[str] = Counter()
    plan_records: dict[str, list[float]] = defaultdict(list)
    for rec in records:
        for gate in rec.get("gate_keys") or []:
            record_gate_counter[str(gate)] += 1
        pid = str(rec.get("plan_id") or "")
        ts = _parse_ts(rec.get("recorded_at"))
        if pid and ts:
            plan_records[pid].append(ts)

    return {
        "session_id": sid,
        "audits": audits,
        "focal_audits": focal_audits,
        "memory_records": records,
        "approval_inbox": inbox,
        "rollbacks": rollbacks,
        "rollouts": rollouts,
        "incidents": incidents,
        "cross_session_memory": cross_session.memory if cross_session.ok else {},
        "gate_counter": gate_counter,
        "outcome_counter": outcome_counter,
        "session_approval_load": session_approval_load,
        "record_gate_counter": record_gate_counter,
        "plan_record_timestamps": dict(plan_records),
        "collected_at": datetime.now(UTC).isoformat(),
    }
