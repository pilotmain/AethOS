# SPDX-License-Identifier: Apache-2.0
"""Continuity memory — grounded operator journey tracking."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path


def _root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "human_centered" / "continuity_memory"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(session_id: str) -> Path:
    return _root() / f"continuity_{session_id}.json"


def _empty_record() -> dict[str, Any]:
    return {
        "phase": None,
        "focus": None,
        "resolved": [],
        "unresolved": [],
        "pending_validation": [],
        "last_manual_validation_request": None,
        "current_system_focus": None,
        "next_best_step": None,
        "confidence": 0.5,
        "evidence_refs": [],
        "replay_refs": [],
        "governance": "No autonomous action",
        "collaboration_context": [],
    }


def load_continuity_memory(*, session_id: str = "default") -> dict[str, Any]:
    path = _path(session_id)
    if not path.is_file():
        return _empty_record()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        base = _empty_record()
        base.update(data)
        return base
    except (OSError, json.JSONDecodeError):
        return _empty_record()


def save_continuity_memory(*, session_id: str = "default", record: dict[str, Any]) -> dict[str, Any]:
    record["updated_at"] = time()
    _path(session_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def set_active_phase(*, session_id: str = "default", phase: str, focus: str) -> dict[str, Any]:
    record = load_continuity_memory(session_id=session_id)
    record["phase"] = phase
    record["focus"] = focus
    record["current_system_focus"] = focus
    return save_continuity_memory(session_id=session_id, record=record)


def record_resolved_issue(*, session_id: str = "default", issue: str, evidence_ref: str | None = None) -> None:
    record = load_continuity_memory(session_id=session_id)
    resolved: list[str] = record.get("resolved") or []
    if issue not in resolved:
        resolved.insert(0, issue)
    record["resolved"] = resolved[:12]
    if evidence_ref:
        refs: list[str] = record.get("evidence_refs") or []
        if evidence_ref not in refs:
            refs.insert(0, evidence_ref)
        record["evidence_refs"] = refs[:10]
    save_continuity_memory(session_id=session_id, record=record)


def record_unresolved_issue(*, session_id: str = "default", issue: str) -> None:
    record = load_continuity_memory(session_id=session_id)
    issues: list[str] = record.get("unresolved") or []
    if issue not in issues:
        issues.insert(0, issue)
    record["unresolved"] = issues[:12]
    save_continuity_memory(session_id=session_id, record=record)


def record_pending_validation(*, session_id: str = "default", item: str) -> None:
    record = load_continuity_memory(session_id=session_id)
    pending: list[str] = record.get("pending_validation") or []
    if item not in pending:
        pending.insert(0, item)
    record["pending_validation"] = pending[:10]
    save_continuity_memory(session_id=session_id, record=record)


def record_manual_validation_request(*, session_id: str = "default", request: str) -> None:
    record = load_continuity_memory(session_id=session_id)
    record["last_manual_validation_request"] = {"request": request[:300], "at": time()}
    save_continuity_memory(session_id=session_id, record=record)


def set_next_best_step(*, session_id: str = "default", step: str, confidence: float | None = None) -> None:
    record = load_continuity_memory(session_id=session_id)
    record["next_best_step"] = step
    if confidence is not None:
        record["confidence"] = round(max(0.0, min(1.0, confidence)), 2)
    save_continuity_memory(session_id=session_id, record=record)


def add_collaboration_context(*, session_id: str = "default", context: str) -> None:
    record = load_continuity_memory(session_id=session_id)
    ctx: list[str] = record.get("collaboration_context") or []
    if context not in ctx:
        ctx.insert(0, context)
    record["collaboration_context"] = ctx[:8]
    save_continuity_memory(session_id=session_id, record=record)


def add_replay_ref(*, session_id: str = "default", ref: str) -> None:
    record = load_continuity_memory(session_id=session_id)
    refs: list[str] = record.get("replay_refs") or []
    if ref not in refs:
        refs.insert(0, ref)
    record["replay_refs"] = refs[:8]
    save_continuity_memory(session_id=session_id, record=record)


def seed_default_continuity(*, session_id: str = "default") -> dict[str, Any]:
    """Seed grounded continuity for operators entering Living Intelligence fresh."""
    record = load_continuity_memory(session_id=session_id)
    if record.get("phase") and record.get("resolved"):
        return record

    record.update({
        "phase": "10.1.1",
        "focus": "Human API convergence",
        "current_system_focus": "Living Intelligence depth and runtime integrity",
        "resolved": [
            "Fixed /human/living 404 caused by humanApi.ts using Next relative fetch instead of mcFetch",
            "Human API routes discovery and Runtime Integrity panel mounted",
        ],
        "unresolved": [
            "Living Intelligence replay integrity during long-running sessions",
        ],
        "pending_validation": [
            "Refresh Mission Control → Living Intelligence → Living Companion",
            "Confirm Runtime Integrity → Route Health shows all human routes mounted",
            "Validate replay integrity during long-running operational sessions",
        ],
        "next_best_step": "Investigate replay stitching or validate Living Companion panel after restart",
        "confidence": 0.82,
        "evidence_refs": ["human_route_registry", "runtime_integrity_report"],
        "replay_refs": ["human_runtime_replay"],
        "governance": "No autonomous action",
        "collaboration_context": [
            "Stabilizing Human-Centered Runtime before adding more intelligence layers",
        ],
    })
    return save_continuity_memory(session_id=session_id, record=record)


def delete_continuity_memory(*, session_id: str = "default") -> dict[str, Any]:
    path = _path(session_id)
    if path.is_file():
        path.unlink()
    return {"ok": True, "deleted": True, "session_id": session_id}


def get_continuity_transparency(*, session_id: str = "default") -> dict[str, Any]:
    record = load_continuity_memory(session_id=session_id)
    return {
        "ok": True,
        "stored_fields": list(record.keys()),
        "record": record,
        "deletable": True,
        "locally_controllable": True,
        "explainable": True,
        "autonomous_execution_blocked": True,
    }


def clear_continuity_memory_for_tests() -> None:
    root = _root()
    for p in root.glob("*.json"):
        p.unlink()
