# SPDX-License-Identifier: Apache-2.0
"""FIX 140 — durable store for operational memory records (organizational layer)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.operational_memory.cross_session.cross_session_contract import (
    CROSS_SESSION_MEMORY_RECORD_SCHEMA_VERSION,
    MAX_PERSISTED_RECORDS_DEFAULT,
)


def memory_records_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "mission_control_operational_memory" / "records"
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_operational_memory_records_for_tests() -> None:
    root = memory_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def _record_path(record_id: str) -> Path:
    safe = "".join(c for c in record_id if c.isalnum() or c in "-_")
    return memory_records_dir() / f"{safe}.json"


def list_operational_memory_records(
    *,
    session_id: str | None = None,
    plan_id: str | None = None,
    limit: int = MAX_PERSISTED_RECORDS_DEFAULT,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(memory_records_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if session_id and str(payload.get("session_id") or "") != session_id:
            continue
        if plan_id and str(payload.get("plan_id") or "") != plan_id:
            continue
        rows.append(payload)
        if len(rows) >= limit:
            break
    return rows


def _find_recent_duplicate(*, session_id: str, plan_id: str, within_seconds: int = 300) -> Path | None:
    now = datetime.now(UTC).timestamp()
    for path in sorted(memory_records_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(payload.get("session_id") or "") != session_id:
            continue
        if plan_id and str(payload.get("plan_id") or "") != plan_id:
            continue
        recorded = str(payload.get("recorded_at") or "")
        try:
            ts = datetime.fromisoformat(recorded.replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        if now - ts <= within_seconds:
            return path
    return None


def persist_operational_memory_record(*, graph: dict[str, Any]) -> dict[str, Any]:
    """Persist a compact organizational memory record derived from a FIX 139 graph."""
    session_id = str(graph.get("session_id") or "default")
    plan_id = str(graph.get("plan_id") or "")
    correlation_id = str(graph.get("correlation_id") or "")

    nodes = list((graph.get("graph") or {}).get("nodes") or [])
    pr_keys = [str(n.get("key")) for n in nodes if n.get("kind") == "pr" and n.get("key")]
    incident_keys = [str(n.get("key")) for n in nodes if n.get("kind") == "incident" and n.get("key")]
    gate_keys = [str(n.get("key")) for n in nodes if n.get("kind") == "gate" and n.get("key")]
    approval_rows = [
        {
            "key": n.get("key"),
            "gate_id": n.get("gate_id"),
            "state": n.get("state"),
            "outcome": n.get("outcome"),
        }
        for n in nodes
        if n.get("kind") == "approval"
    ]

    blocker_sigs = [str(b.get("blocker") or "") for b in graph.get("recurring_blockers") or [] if b.get("blocker")]
    failure_sigs = [str(f.get("signature") or "") for f in graph.get("repeated_failures") or [] if f.get("signature")]

    rollout_nodes = [n for n in nodes if n.get("kind") == "rollout"]
    rollout_stages = [str(n.get("latest_stage") or "") for n in rollout_nodes if n.get("latest_stage")]

    record: dict[str, Any] = {
        "schema_version": CROSS_SESSION_MEMORY_RECORD_SCHEMA_VERSION,
        "record_id": f"omr-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "plan_id": plan_id or None,
        "correlation_id": correlation_id or None,
        "pr_keys": pr_keys,
        "incident_keys": incident_keys,
        "gate_keys": gate_keys,
        "approval_rows": approval_rows,
        "blocker_signatures": blocker_sigs,
        "failure_signatures": failure_sigs,
        "rollout_stages": rollout_stages,
        "mission_lineage": list(graph.get("mission_lineage") or [])[:20],
        "graph_stats": (graph.get("graph") or {}).get("stats") or {},
        "learning_signals": list(graph.get("learning_signals") or [])[:8],
        "sources": dict(graph.get("sources") or {}),
        "read_only": True,
    }

    dup_path = _find_recent_duplicate(session_id=session_id, plan_id=plan_id)
    if dup_path:
        try:
            existing = json.loads(dup_path.read_text(encoding="utf-8"))
            record["record_id"] = str(existing.get("record_id") or record["record_id"])
        except (OSError, json.JSONDecodeError):
            pass
        target = dup_path
    else:
        target = _record_path(record["record_id"])

    target.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def prune_operational_memory_records(*, keep: int = MAX_PERSISTED_RECORDS_DEFAULT) -> int:
    paths = sorted(memory_records_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
