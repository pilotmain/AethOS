# SPDX-License-Identifier: Apache-2.0
"""FIX 125A — durable software delivery issue plans."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.issue_plan_contract import (
    AUTONOMOUS_MERGE_PERMITTED,
    CODE_GENERATION_ENABLED_FIX_125A,
    INFRA_MUTATION_PERMITTED,
    ISSUE_PLAN_SCHEMA_VERSION,
)

_SESSION_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_issue_plans"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(plan_id: str) -> Path:
    safe = (plan_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.session_plan_index import clear_session_plan_index_for_tests
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _SESSION_INDEX.clear()
    clear_session_plan_index_for_tests()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_issue_plan(*, plan_id: str) -> dict[str, Any] | None:
    path = _path(plan_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def list_issue_plans_for_session(*, session_id: str) -> list[dict[str, Any]]:
    sid = (session_id or "default").strip()[:64] or "default"
    rows: list[dict[str, Any]] = []
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("session_id") or "") == sid:
            rows.append(payload)
    return rows


def _delivery_progress_score(*, plan_id: str) -> int:
    from aethos_core.software_delivery.branch_push_store import branch_push_completed_for_plan
    from aethos_core.software_delivery.github_pr_open_store import _pr_open_completed_local
    from aethos_core.software_delivery.github_pr_preflight_store import github_pr_creation_approved_for_plan
    from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan
    from aethos_core.software_delivery.workspace_verification_store import workspace_verification_passed

    score = 0
    if _pr_open_completed_local(plan_id=plan_id):
        score += 1000
    elif branch_push_completed_for_plan(plan_id=plan_id):
        score += 900
    elif github_pr_creation_approved_for_plan(plan_id=plan_id):
        score += 800
    elif load_pr_draft_for_plan(plan_id=plan_id):
        score += 700
    elif workspace_verification_passed(plan_id=plan_id):
        score += 600
    return score


def _plan_sort_key(plan: dict[str, Any]) -> tuple[int, str]:
    plan_id = str(plan.get("plan_id") or "")
    return (_delivery_progress_score(plan_id=plan_id), str(plan.get("updated_at") or ""))


def load_issue_plan_for_session(*, session_id: str) -> dict[str, Any] | None:
    sid = (session_id or "default").strip()[:64] or "default"
    from aethos_core.software_delivery.session_plan_index import load_session_plan_id

    indexed_id = load_session_plan_id(session_id=sid)
    if indexed_id:
        cached = load_issue_plan(plan_id=indexed_id)
        if cached and str(cached.get("session_id") or "") == sid:
            _SESSION_INDEX[sid] = indexed_id
            return cached
        from aethos_core.software_delivery.session_delivery_artifact_recovery import restore_issue_plan_for_session

        restored = restore_issue_plan_for_session(session_id=sid)
        if restored:
            pid = str(restored.get("plan_id") or "")
            if pid:
                _SESSION_INDEX[sid] = pid
            return restored
        return None

    cached_id = _SESSION_INDEX.get(sid)
    if cached_id:
        cached = load_issue_plan(plan_id=cached_id)
        if cached and str(cached.get("session_id") or "") == sid:
            return cached
        _SESSION_INDEX.pop(sid, None)

    plans = list_issue_plans_for_session(session_id=sid)
    if not plans:
        from aethos_core.software_delivery.session_delivery_artifact_recovery import restore_issue_plan_for_session

        restored = restore_issue_plan_for_session(session_id=sid)
        if restored:
            pid = str(restored.get("plan_id") or "")
            if pid:
                _SESSION_INDEX[sid] = pid
            return restored
        return None
    if len(plans) == 1:
        best = plans[0]
    else:
        best = max(plans, key=_plan_sort_key)
    pid = str(best.get("plan_id") or "")
    if pid:
        _SESSION_INDEX[sid] = pid
    return best


def save_issue_plan(plan: dict[str, Any]) -> dict[str, Any]:
    plan_id = str(plan.get("plan_id") or "").strip()
    if not plan_id:
        raise ValueError("plan_id required")
    plan.setdefault("schema_version", ISSUE_PLAN_SCHEMA_VERSION)
    plan["mutation_performed"] = False
    plan["autonomous_merge_permitted"] = AUTONOMOUS_MERGE_PERMITTED
    plan["infra_mutation_permitted"] = INFRA_MUTATION_PERMITTED
    plan["code_generation_enabled"] = CODE_GENERATION_ENABLED_FIX_125A
    plan["updated_at"] = datetime.now(UTC).isoformat()
    _path(plan_id).write_text(json.dumps(plan, indent=2), encoding="utf-8")
    session_id = str(plan.get("session_id") or "")
    if session_id:
        _SESSION_INDEX[session_id] = plan_id
        from aethos_core.software_delivery.session_plan_index import persist_session_plan_binding

        persist_session_plan_binding(session_id=session_id, plan_id=plan_id)
    return plan


def append_plan_event(
    plan: dict[str, Any],
    *,
    action: str,
    actor: str = "operator",
    detail: str = "",
) -> dict[str, Any]:
    events = list(plan.get("events") or [])
    events.append(
        {
            "event_id": f"sde-{uuid.uuid4().hex[:10]}",
            "action": action,
            "actor": actor,
            "detail": detail,
            "recorded_at": datetime.now(UTC).isoformat(),
            "mutation_performed": False,
        }
    )
    plan["events"] = events
    return save_issue_plan(plan)
