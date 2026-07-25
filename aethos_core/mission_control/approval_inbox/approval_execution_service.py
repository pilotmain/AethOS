# SPDX-License-Identifier: Apache-2.0
"""FIX 133–134 — governed UI approval execution via chat routes (no bypass)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_audit_service import (
    clear_ui_approval_audit_for_tests,
    find_replay_audit,
    persist_ui_approval_audit,
)
from aethos_core.mission_control.approval_inbox.approval_execution_contract import (
    CHAT_GOVERNANCE_REQUIRED,
    ui_approval_eligible,
)
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
from aethos_core.mission_control.approval_inbox.approval_phrase_templates import (
    GATE_CHAT_PREFIX,
    build_copy_phrase_text,
)


def get_chat_command_prefix(gate_id: str) -> str | None:
    return GATE_CHAT_PREFIX.get(gate_id)


def build_governed_chat_message(*, gate_id: str, required_phrases: list[str]) -> str:
    from aethos_core.mission_control.approval_inbox.approval_execution_contract import UI_APPROVAL_ORIGIN

    body = build_copy_phrase_text(gate_id=gate_id, required_phrases=required_phrases)
    if not GATE_CHAT_PREFIX.get(gate_id):
        raise ValueError(f"gate_not_eligible_for_ui_approval:{gate_id}")
    if not [p for p in required_phrases if (p or "").strip()]:
        raise ValueError("required_phrases_missing")
    return f"[{UI_APPROVAL_ORIGIN}]\n{body}"


@dataclass(frozen=True)
class ApprovalExecutionResult:
    ok: bool
    session_id: str
    inbox_id: str
    gate_id: str = ""
    chat_intent: str = ""
    reply: str = ""
    route_id: str = ""
    mutation_performed: bool = False
    audit_id: str = ""
    detail: str = ""
    outcome: str = ""
    blockers: list[str] = field(default_factory=list)
    replay_protected: bool = False


def _find_inbox_item(*, session_id: str, inbox_id: str) -> dict[str, Any] | None:
    inbox = build_approval_inbox(session_id=session_id)
    if not inbox.ok:
        return None
    for item in inbox.items:
        if str(item.get("inbox_id") or "") == inbox_id:
            return item
    return None


def _audit_and_return(
    *,
    result: ApprovalExecutionResult,
    audit_fields: dict[str, Any],
) -> ApprovalExecutionResult:
    audit = persist_ui_approval_audit(audit_fields)
    return ApprovalExecutionResult(
        ok=result.ok,
        session_id=result.session_id,
        inbox_id=result.inbox_id,
        gate_id=result.gate_id,
        chat_intent=result.chat_intent,
        reply=result.reply,
        route_id=result.route_id,
        mutation_performed=result.mutation_performed,
        audit_id=str(audit.get("approval_id") or ""),
        detail=result.detail,
        outcome=str(audit.get("outcome") or result.outcome),
        blockers=result.blockers,
        replay_protected=result.replay_protected,
    )


def execute_governed_ui_approval(*, session_id: str, inbox_id: str) -> ApprovalExecutionResult:
    prior = find_replay_audit(session_id=session_id, inbox_id=inbox_id)
    if prior:
        return ApprovalExecutionResult(
            ok=True,
            session_id=session_id,
            inbox_id=inbox_id,
            gate_id=str(prior.get("gate_id") or ""),
            outcome="replay_protected",
            replay_protected=True,
            audit_id=str(prior.get("approval_id") or ""),
            detail="Duplicate UI approval suppressed — prior successful audit exists.",
            blockers=[],
            chat_intent=str(prior.get("chat_intent") or ""),
            route_id=str(prior.get("route_id") or ""),
            mutation_performed=bool(prior.get("mutation_performed")),
        )

    item = _find_inbox_item(session_id=session_id, inbox_id=inbox_id)
    if not item:
        return ApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            outcome="failed",
            blockers=["inbox_item_not_found"],
            detail="Pending approval item not found for session.",
        )

    lane = str(item.get("lane") or "")
    gate_id = str(item.get("gate_id") or "")
    phrases = list(item.get("required_phrases") or [])

    if not ui_approval_eligible(lane=lane, gate_id=gate_id):
        return _audit_and_return(
            result=ApprovalExecutionResult(
                ok=False,
                session_id=session_id,
                inbox_id=inbox_id,
                gate_id=gate_id,
                outcome="failed",
                blockers=["ui_approval_not_eligible"],
                detail=(
                    "This gate must be completed in chat. Branch push and PR open couple approval "
                    "phrases to governed mutations and are not available from the inbox UI."
                ),
            ),
            audit_fields={
                "session_id": session_id,
                "inbox_id": inbox_id,
                "lane": lane,
                "gate_id": gate_id,
                "outcome": "failed",
                "gate_satisfied": False,
                "blockers": ["ui_approval_not_eligible"],
                "failure_reason": "ineligible_for_ui_execution",
            },
        )

    if _gate_already_satisfied(gate_id=gate_id, session_id=session_id):
        return _audit_and_return(
            result=ApprovalExecutionResult(
                ok=True,
                session_id=session_id,
                inbox_id=inbox_id,
                gate_id=gate_id,
                outcome="gate_already_cleared",
                detail="Gate already satisfied — no chat dispatch required.",
            ),
            audit_fields={
                "session_id": session_id,
                "inbox_id": inbox_id,
                "lane": lane,
                "gate_id": gate_id,
                "outcome": "gate_already_cleared",
                "gate_satisfied": True,
                "copy_phrase_text": build_copy_phrase_text(gate_id=gate_id, required_phrases=phrases),
                "failure_reason": "",
            },
        )

    try:
        message = build_governed_chat_message(gate_id=gate_id, required_phrases=phrases)
    except ValueError as exc:
        return _audit_and_return(
            result=ApprovalExecutionResult(
                ok=False,
                session_id=session_id,
                inbox_id=inbox_id,
                gate_id=gate_id,
                outcome="failed",
                blockers=[str(exc)],
            ),
            audit_fields={
                "session_id": session_id,
                "inbox_id": inbox_id,
                "lane": lane,
                "gate_id": gate_id,
                "outcome": "failed",
                "gate_satisfied": False,
                "blockers": [str(exc)],
                "failure_reason": str(exc),
            },
        )

    from aethos_core.chat.service import resolve_chat_turn

    turn = resolve_chat_turn(message, session_id=session_id, apply_relational_layer=False)
    meta = turn.meta or {}
    route_id = str(meta.get("route_id") or "")
    mutation_performed = str(meta.get("mutation_performed", "false")).lower() == "true"
    gate_satisfied = _gate_satisfied_after_turn(gate_id=gate_id, session_id=session_id, turn=turn)
    outcome = "success" if gate_satisfied else "failed"
    blockers = [] if gate_satisfied else ["gate_not_satisfied_after_chat"]
    failure_detail = "Approval routed through governed chat." if gate_satisfied else (
        (turn.reply or "").strip()[:800] or "Chat handled request but gate not satisfied."
    )

    return _audit_and_return(
        result=ApprovalExecutionResult(
            ok=gate_satisfied,
            session_id=session_id,
            inbox_id=inbox_id,
            gate_id=gate_id,
            chat_intent=turn.intent or "",
            reply=turn.reply or "",
            route_id=route_id,
            mutation_performed=mutation_performed,
            outcome=outcome,
            detail=failure_detail,
            blockers=blockers,
        ),
        audit_fields={
            "session_id": session_id,
            "inbox_id": inbox_id,
            "lane": lane,
            "gate_id": gate_id,
            "outcome": outcome,
            "gate_satisfied": gate_satisfied,
                "chat_message_prefix": GATE_CHAT_PREFIX.get(gate_id),
            "copy_phrase_text": build_copy_phrase_text(gate_id=gate_id, required_phrases=phrases),
            "required_phrase_count": len(phrases),
            "chat_intent": turn.intent,
            "route_id": route_id,
            "mutation_performed": mutation_performed,
            "direct_provider_mutation": False,
            "reply_excerpt": (turn.reply or "")[:500],
            "blockers": blockers,
            "failure_reason": blockers[0] if blockers else "",
        },
    )


def _gate_already_satisfied(*, gate_id: str, session_id: str) -> bool:
    from aethos_core.chat.service import ChatTurnResult

    return _gate_satisfied_after_turn(
        gate_id=gate_id,
        session_id=session_id,
        turn=ChatTurnResult(reply="", intent="precheck"),
    )


def _gate_satisfied_after_turn(*, gate_id: str, session_id: str, turn: Any) -> bool:
    from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan
    from aethos_core.software_delivery.github_pr_preflight_store import github_pr_creation_approved_for_plan
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
    from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan
    from aethos_core.software_delivery.workspace_application_store import load_workspace_application_for_plan

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return False
    plan_id = str(plan.get("plan_id") or "")

    if gate_id == "planning_approved":
        return str(plan.get("status") or "") == "planning_approved"
    if gate_id == "branch_create":
        return bool(load_branch_context_for_plan(plan_id=plan_id))
    if gate_id == "patch_proposal_approved":
        proposal = load_patch_proposal_for_plan(plan_id=plan_id)
        return bool(proposal and proposal.get("patch_proposal_approved"))
    if gate_id == "workspace_apply":
        application = load_workspace_application_for_plan(plan_id=plan_id)
        return str((application or {}).get("status") or "") == "applied"
    if gate_id == "github_preflight_approved":
        return github_pr_creation_approved_for_plan(plan_id=plan_id)

    intent = str(getattr(turn, "intent", "") or "")
    return "approved" in intent and "blocked" not in intent


# Re-export for tests
__all__ = [
    "ApprovalExecutionResult",
    "build_copy_phrase_text",
    "build_governed_chat_message",
    "clear_ui_approval_audit_for_tests",
    "execute_governed_ui_approval",
    "get_chat_command_prefix",
]
