# SPDX-License-Identifier: Apache-2.0
"""FIX 188 — durable store for PilotOS UI pilot arc orchestrator."""

from __future__ import annotations

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    GOVERNANCE_MUTATION_PERFORMED_FIX_188,
    MAX_PERSISTED_PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORDS,
    MAX_PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_CONTENT_LEN,
    PILOTOS_UI_DEFAULT_REPO_ISSUE,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_EXECUTABLE,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ORIGIN,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORD_KINDS,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION,
    PILOTOS_UI_REPOSITORY,
)

_ISSUE_RX = re.compile(r"pilotmain/[\w.-]+#\d+", re.I)


def pilotos_ui_pilot_arc_orchestrator_records_dir() -> Path:
    root = (
        Path(__file__).resolve().parents[3]
        / "data"
        / "mission_control_pilotos_ui_pilot_arc_orchestrator"
        / "records"
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests() -> None:
    root = pilotos_ui_pilot_arc_orchestrator_records_dir()
    if root.exists():
        for child in root.glob("*.json"):
            child.unlink(missing_ok=True)


def list_pilotos_ui_pilot_arc_orchestrator_records(
    *,
    limit: int = MAX_PERSISTED_PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORDS,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        pilotos_ui_pilot_arc_orchestrator_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
    )
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            rows.append(payload)
    rows.sort(key=lambda r: str(r.get("recorded_at") or ""))
    if len(rows) > limit:
        rows = rows[-limit:]
    return rows


def registered_repo_issue() -> str:
    for record in reversed(list_pilotos_ui_pilot_arc_orchestrator_records()):
        if str(record.get("kind") or "") == "repo_issue_binding":
            issue = str(record.get("repo_issue") or record.get("content") or "").strip()
            if issue:
                return issue
        if str(record.get("kind") or "") == "repository_registration":
            content = str(record.get("content") or "")
            match = _ISSUE_RX.search(content)
            if match:
                return match.group(0)
    return PILOTOS_UI_DEFAULT_REPO_ISSUE


def has_pilot_arc_trust_decision(*, trust_status: str = "CONDITIONALLY_TRUSTED") -> bool:
    for record in reversed(list_pilotos_ui_pilot_arc_orchestrator_records()):
        if str(record.get("kind") or "") != "pilot_arc_trust_decision":
            continue
        if trust_status.lower() in str(record.get("content") or "").lower():
            return True
        meta = record.get("metadata") or {}
        if str(meta.get("trust_status") or "") == trust_status:
            return True
    return False


def append_pilotos_ui_pilot_arc_orchestrator_record(
    *,
    session_id: str,
    kind: str,
    content: str,
    repo_issue: str | None = None,
    author: str = "operator",
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    kind_norm = (kind or "").strip().lower()
    if kind_norm not in PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORD_KINDS:
        blockers.append(f"invalid_kind:{kind_norm}")
        return None, blockers

    text = (content or "").strip()
    if not text and kind_norm != "pilot_arc_transition":
        blockers.append("empty_content")
        return None, blockers
    if len(text) > MAX_PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_CONTENT_LEN:
        blockers.append("content_too_long")
        return None, blockers

    sid = (session_id or "default").strip()[:64] or "default"
    record: dict[str, Any] = {
        "schema_version": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION,
        "record_id": f"puiao-{uuid.uuid4().hex[:12]}",
        "recorded_at": datetime.now(UTC).isoformat(),
        "session_id": sid,
        "repository": PILOTOS_UI_REPOSITORY,
        "repo_issue": repo_issue or None,
        "kind": kind_norm,
        "author": (author or "operator").strip()[:64] or "operator",
        "content": text,
        "metadata": dict(metadata or {}),
        "executable": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_EXECUTABLE,
        "automatic_trust_granting_enabled": False,
        "trust_transfer_enabled": False,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_188,
        "pilotos_ui_pilot_arc_orchestrator_memory_only": True,
        "origin": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ORIGIN,
    }
    path = pilotos_ui_pilot_arc_orchestrator_records_dir() / f"{record['record_id']}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _prune_old_records()
    return record, blockers


def _prune_old_records(
    *, keep: int = MAX_PERSISTED_PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORDS
) -> int:
    paths = sorted(
        pilotos_ui_pilot_arc_orchestrator_records_dir().glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    removed = 0
    for path in paths[keep:]:
        path.unlink(missing_ok=True)
        removed += 1
    return removed
