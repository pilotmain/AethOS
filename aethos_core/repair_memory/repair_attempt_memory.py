# SPDX-License-Identifier: Apache-2.0
"""Repair attempt memory — durable outcomes from post-mutation verification."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from time import time
from typing import Any

_MEMORY: dict[str, Any] | None = None


@dataclass
class RepairAttemptOutcome:
    target: str
    operation: str
    attempted_at: str
    result: str
    health_after: str
    helped: bool
    evidence: list[str] = field(default_factory=list)
    lesson: str = ""
    provider: str = "railway"
    project: str = ""
    environment: str = ""
    service: str = ""
    execution_job_id: str = ""
    session_id: str = "default"
    verification_status: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "RepairAttemptOutcome":
        return cls(
            target=str(payload.get("target") or ""),
            operation=str(payload.get("operation") or "restart"),
            attempted_at=str(payload.get("attempted_at") or ""),
            result=str(payload.get("result") or ""),
            health_after=str(payload.get("health_after") or ""),
            helped=bool(payload.get("helped")),
            evidence=list(payload.get("evidence") or []),
            lesson=str(payload.get("lesson") or ""),
            provider=str(payload.get("provider") or "railway"),
            project=str(payload.get("project") or ""),
            environment=str(payload.get("environment") or ""),
            service=str(payload.get("service") or ""),
            execution_job_id=str(payload.get("execution_job_id") or ""),
            session_id=str(payload.get("session_id") or "default"),
            verification_status=str(payload.get("verification_status") or ""),
        )


def _store_path() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "repair_memory"
    root.mkdir(parents=True, exist_ok=True)
    return root / "outcomes.json"


def _load_raw() -> dict[str, Any]:
    global _MEMORY
    if _MEMORY is not None:
        return _MEMORY
    path = _store_path()
    if not path.is_file():
        _MEMORY = {"outcomes": []}
        return _MEMORY
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raw = {"outcomes": []}
    except (OSError, json.JSONDecodeError):
        raw = {"outcomes": []}
    _MEMORY = raw
    return _MEMORY


def _save_raw(data: dict[str, Any]) -> None:
    global _MEMORY
    data["updated_at"] = time()
    _MEMORY = data
    _store_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def _target_key(outcome: RepairAttemptOutcome) -> str:
    return ":".join(
        [
            outcome.provider.lower(),
            outcome.project.lower(),
            outcome.environment.lower(),
            outcome.service.lower(),
            outcome.operation.lower(),
        ]
    )


def save_repair_attempt(outcome: RepairAttemptOutcome) -> RepairAttemptOutcome:
    data = _load_raw()
    rows = list(data.get("outcomes") or [])
    key = _target_key(outcome)
    rows = [row for row in rows if _target_key(RepairAttemptOutcome.from_dict(row)) != key or row.get("execution_job_id") != outcome.execution_job_id]
    rows.append(outcome.to_dict())
    rows.sort(key=lambda row: row.get("attempted_at") or "", reverse=True)
    data["outcomes"] = rows[:200]
    _save_raw(data)
    return outcome


def list_repair_attempts(*, limit: int = 20) -> list[RepairAttemptOutcome]:
    rows = list(_load_raw().get("outcomes") or [])
    return [RepairAttemptOutcome.from_dict(row) for row in rows[:limit]]


def lookup_latest_for_target(
    target_path: str,
    *,
    operation: str | None = None,
) -> RepairAttemptOutcome | None:
    needle = (target_path or "").strip().lower()
    for row in list_repair_attempts(limit=50):
        if row.target.lower() != needle:
            continue
        if operation and row.operation.lower() != operation.lower():
            continue
        return row
    return None


def lookup_latest_for_service(
    service: str,
    *,
    operation: str = "restart",
) -> RepairAttemptOutcome | None:
    service_key = (service or "").strip().lower()
    for row in list_repair_attempts(limit=50):
        if row.service.lower() != service_key:
            continue
        if row.operation.lower() != operation.lower():
            continue
        return row
    return None


def reset_repair_memory_for_tests() -> None:
    global _MEMORY
    _MEMORY = {"outcomes": []}
    path = _store_path()
    if path.is_file():
        path.unlink()
