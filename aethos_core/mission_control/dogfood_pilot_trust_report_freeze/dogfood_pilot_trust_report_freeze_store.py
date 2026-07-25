# SPDX-License-Identifier: Apache-2.0
"""FIX 186 — durable store for dogfood pilot trust report freeze."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_contract import (
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_EXECUTABLE,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ORIGIN,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORD_KINDS,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_186,
    MAX_DOGFOOD_PILOT_TRUST_REPORT_FREEZE_CONTENT_LEN,
    MAX_PERSISTED_DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORDS,
)


def dogfood_pilot_trust_report_freeze_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_dogfood_pilot_trust_report_freeze"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_dogfood_pilot_trust_report_freeze_records_for_tests() -> None:
    root = dogfood_pilot_trust_report_freeze_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_dogfood_pilot_trust_report_freeze_records(
    *,
    session_id: str | None = None,
    limit: int = MAX_PERSISTED_DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        dogfood_pilot_trust_report_freeze_records_dir().glob("*.json"),
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
        rows.append(payload)
    rows.sort(key=lambda r: str(r.get("recorded_at") or ""))
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows


def has_expansion_approval_record(*, session_id: str | None = None) -> bool:
    for record in list_dogfood_pilot_trust_report_freeze_records(session_id=session_id):
        if str(record.get("kind") or "") == "expansion_approval_note":
            return True
    return False


def has_trust_report_freeze_record(*, session_id: str | None = None) -> bool:
    for record in list_dogfood_pilot_trust_report_freeze_records(session_id=session_id):
        if str(record.get("kind") or "") == "trust_report_freeze_artifact":
            return True
    return False


def has_operator_review_record(*, session_id: str | None = None) -> bool:
    for record in list_dogfood_pilot_trust_report_freeze_records(session_id=session_id):
        if str(record.get("kind") or "") == "operator_review_note":
            return True
    return False


def append_dogfood_pilot_trust_report_freeze_record(
    *,
    session_id: str,
    kind: str,
    content: str,
    author: str = "operator",
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    kind_norm = (kind or "").strip().lower()
    if kind_norm not in DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text:
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_DOGFOOD_PILOT_TRUST_REPORT_FREEZE_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
        "record_id": f"dptrf-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_EXECUTABLE,
        "direct_provider_mutation_performed": False,
        "pilot_reexecution_performed": False,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_186,
        "dogfood_pilot_trust_report_freeze_memory_only": True,
        "trust_report_origin": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ORIGIN,
    }
    path = dogfood_pilot_trust_report_freeze_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(
    *, keep: int = MAX_PERSISTED_DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORDS
) -> int:
    paths = sorted(
        dogfood_pilot_trust_report_freeze_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
