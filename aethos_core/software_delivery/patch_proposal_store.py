# SPDX-License-Identifier: Apache-2.0
"""FIX 125C — durable patch proposal store (one plan → one proposal)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.patch_proposal_contract import (
    DEPLOY_ENABLED_FIX_125C,
    FILE_WRITE_ENABLED_FIX_125C,
    GIT_COMMIT_ENABLED_FIX_125C,
    MERGE_ENABLED_FIX_125C,
    PATCH_PROPOSAL_SCHEMA_VERSION,
    PR_CREATION_ENABLED_FIX_125C,
)

_PLAN_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_patch_proposals"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(proposal_id: str) -> Path:
    safe = (proposal_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _PLAN_INDEX.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_patch_proposal(*, proposal_id: str) -> dict[str, Any] | None:
    path = _path(proposal_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_patch_proposal_for_plan(*, plan_id: str) -> dict[str, Any] | None:
    pid = _PLAN_INDEX.get(plan_id)
    if pid:
        return load_patch_proposal(proposal_id=pid)
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("plan_id") or "") == plan_id:
            proposal_id = str(payload.get("proposal_id") or "")
            if proposal_id:
                _PLAN_INDEX[plan_id] = proposal_id
            return payload
    return None


def save_patch_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    proposal_id = str(proposal.get("proposal_id") or "").strip()
    if not proposal_id:
        raise ValueError("proposal_id required")
    proposal.setdefault("schema_version", PATCH_PROPOSAL_SCHEMA_VERSION)
    proposal["file_write_enabled"] = FILE_WRITE_ENABLED_FIX_125C
    proposal["git_commit_enabled"] = GIT_COMMIT_ENABLED_FIX_125C
    proposal["pr_creation_enabled"] = PR_CREATION_ENABLED_FIX_125C
    proposal["merge_enabled"] = MERGE_ENABLED_FIX_125C
    proposal["deploy_enabled"] = DEPLOY_ENABLED_FIX_125C
    proposal["updated_at"] = datetime.now(UTC).isoformat()
    _path(proposal_id).write_text(json.dumps(proposal, indent=2), encoding="utf-8")
    plan_id = str(proposal.get("plan_id") or "")
    if plan_id:
        _PLAN_INDEX[plan_id] = proposal_id
    return proposal


def append_proposal_event(
    proposal: dict[str, Any],
    *,
    action: str,
    actor: str = "operator",
    detail: str = "",
) -> dict[str, Any]:
    events = list(proposal.get("events") or [])
    events.append(
        {
            "event_id": f"spe-{uuid.uuid4().hex[:10]}",
            "action": action,
            "actor": actor,
            "detail": detail,
            "recorded_at": datetime.now(UTC).isoformat(),
            "file_write_performed": False,
            "mutation_performed": False,
        }
    )
    proposal["events"] = events
    return save_patch_proposal(proposal)
