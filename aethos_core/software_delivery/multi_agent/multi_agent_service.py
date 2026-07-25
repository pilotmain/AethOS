# SPDX-License-Identifier: Apache-2.0
"""FIX 127 — bounded multi-agent collaboration service."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from aethos_core.software_delivery.issue_plan_store import append_plan_event, load_issue_plan_for_session
from aethos_core.software_delivery.multi_agent.multi_agent_contract import BOUNDED_AGENT_ROLE_IDS
from aethos_core.software_delivery.multi_agent.multi_agent_receipts import record_multi_agent_receipt
from aethos_core.software_delivery.multi_agent.multi_agent_roles import ROLE_RUNNERS
from aethos_core.software_delivery.multi_agent.multi_agent_store import (
    load_collaboration_for_plan,
    save_collaboration,
)

_COLLAB_RX = re.compile(
    r"\brun\s+software\s+delivery\s+agent\s+collaboration\b",
    re.I,
)
_ROLE_RX = re.compile(
    r"\brun\s+software\s+delivery\s+(planner|reviewer|verification|risk|diff\s+audit)\s+agent\b",
    re.I,
)
_STATUS_RX = re.compile(r"\bshow\s+software\s+delivery\s+agent\s+collaboration\s+status\b", re.I)
_REPORT_RX = re.compile(r"\bshow\s+software\s+delivery\s+agent\s+collaboration\s+report\b", re.I)

_ROLE_ALIAS: dict[str, str] = {
    "planner": "planner_agent",
    "reviewer": "reviewer_agent",
    "verification": "verification_agent",
    "risk": "risk_agent",
    "diff audit": "diff_audit_agent",
    "diff_audit": "diff_audit_agent",
}


@dataclass(frozen=True)
class MultiAgentResult:
    ok: bool
    record: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_multi_agent_collaboration_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _COLLAB_RX.search(raw)
        or _ROLE_RX.search(raw)
        or _STATUS_RX.search(raw)
        or _REPORT_RX.search(raw)
    )


def load_multi_agent_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "software_delivery_multi_agent_enabled", True)),
    }


def _resolve_role_ids(raw: str) -> list[str]:
    match = _ROLE_RX.search(raw or "")
    if not match:
        return list(BOUNDED_AGENT_ROLE_IDS)
    alias = (match.group(1) or "").lower().replace("_", " ")
    role_id = _ROLE_ALIAS.get(alias)
    return [role_id] if role_id else list(BOUNDED_AGENT_ROLE_IDS)


def run_agent_collaboration(*, session_id: str, user_text: str) -> MultiAgentResult:
    cfg = load_multi_agent_config()
    if not cfg["enabled"]:
        return MultiAgentResult(ok=False, record={}, blockers=["multi_agent_disabled"])

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return MultiAgentResult(ok=False, record={}, blockers=["issue_plan_missing"])

    plan_id = str(plan.get("plan_id") or "")
    role_ids = _resolve_role_ids(user_text)

    record = load_collaboration_for_plan(plan_id=plan_id) or {
        "collaboration_id": f"sdmac-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "session_id": session_id,
        "agent_outputs": [],
        "events": [],
    }
    record_multi_agent_receipt(
        plan_id=plan_id,
        phase="collaboration_started",
        collaboration_id=str(record.get("collaboration_id") or ""),
        detail=f"roles={','.join(role_ids)}",
    )

    outputs: list[dict[str, Any]] = []
    for role_id in role_ids:
        runner = ROLE_RUNNERS.get(role_id)
        if not runner:
            continue
        output = runner(session_id=session_id, plan_id=plan_id)
        outputs.append(output)
        record_multi_agent_receipt(
            plan_id=plan_id,
            phase="agent_role_completed",
            collaboration_id=str(record.get("collaboration_id") or ""),
            agent_role_id=role_id,
            detail=str(output.get("title") or ""),
        )

    record["status"] = "completed"
    record["agent_outputs"] = outputs
    record = save_collaboration(record)
    record_multi_agent_receipt(
        plan_id=plan_id,
        phase="collaboration_completed",
        collaboration_id=str(record.get("collaboration_id") or ""),
        detail=f"{len(outputs)} agents",
    )
    append_plan_event(plan, action="agent_collaboration_completed", detail=str(record.get("collaboration_id") or ""))

    return MultiAgentResult(
        ok=True,
        record=record,
        detail=f"Completed {len(outputs)} advisory agent role(s); no mutations performed.",
    )


def show_agent_collaboration(*, session_id: str) -> MultiAgentResult:
    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return MultiAgentResult(ok=False, record={}, blockers=["issue_plan_missing"])
    record = load_collaboration_for_plan(plan_id=str(plan.get("plan_id") or ""))
    if not record:
        return MultiAgentResult(
            ok=False,
            record={},
            blockers=["agent_collaboration_missing"],
            detail="Run `run software delivery agent collaboration` after issue plan exists.",
        )
    return MultiAgentResult(ok=True, record=record)
