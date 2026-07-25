# SPDX-License-Identifier: Apache-2.0
"""FIX 175 — durable store for governed lane readiness board records."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175,
    GOVERNED_LANE_READINESS_BOARD_EXECUTABLE,
    GOVERNED_LANE_READINESS_BOARD_RECORD_KINDS,
    GOVERNED_LANE_READINESS_BOARD_RECORD_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_175,
    MAX_GOVERNED_LANE_READINESS_BOARD_CONTENT_LEN,
    MAX_PERSISTED_GOVERNED_LANE_READINESS_BOARD_RECORDS,
)


def governed_lane_readiness_board_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_governed_lane_readiness_board"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_governed_lane_readiness_board_records_for_tests() -> None:
    root = governed_lane_readiness_board_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def _record_path(record_id: str) -> Path:
    safe = "".join(c for c in record_id if c.isalnum() or c in "-_")
    return governed_lane_readiness_board_records_dir() / f"{safe}.json"


def list_governed_lane_readiness_board_records(
    *,
    session_id: str | None = None,
    plan_id: str | None = None,
    limit: int = MAX_PERSISTED_GOVERNED_LANE_READINESS_BOARD_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        governed_lane_readiness_board_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
    )
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if session_id and str(payload.get("session_id") or "") != session_id:
            continue
        if plan_id:
            rec_plan = str(payload.get("plan_id") or "")
            if rec_plan and rec_plan != plan_id:
                continue
        rows.append(payload)
    rows.sort(key=lambda r: str(r.get("recorded_at") or ""))
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows


def append_governed_lane_readiness_board_record(
    *,
    session_id: str,
    kind: str,
    content: str,
    plan_id: str | None = None,
    correlation_id: str | None = None,
    author: str = "operator",
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    kind_norm = (kind or "").strip().lower()
    if kind_norm not in GOVERNED_LANE_READINESS_BOARD_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_GOVERNED_LANE_READINESS_BOARD_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": GOVERNED_LANE_READINESS_BOARD_RECORD_SCHEMA_VERSION,
        "record_id": f"glrb-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "plan_id": plan_id or None,
        "correlation_id": correlation_id or None,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": GOVERNED_LANE_READINESS_BOARD_EXECUTABLE,
        "lane_admission_decision_performed": False,
        "lane_admission_performed": False,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_175,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175,
        "governed_lane_readiness_board_memory_only": True,
    }
    _record_path(record["record_id"]).write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(*, keep: int = MAX_PERSISTED_GOVERNED_LANE_READINESS_BOARD_RECORDS) -> int:
    paths = sorted(
        governed_lane_readiness_board_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
