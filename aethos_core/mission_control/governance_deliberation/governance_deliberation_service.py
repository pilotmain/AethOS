# SPDX-License-Identifier: Apache-2.0
"""FIX 148 — governance deliberation workspace from readiness review + institutional memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_deliberation.governance_deliberation_contract import (
    AUTOMATIC_APPROVAL_ENABLED_FIX_148,
    AUTOMATIC_REJECTION_ENABLED_FIX_148,
    AUTONOMOUS_POLICY_EVOLUTION_ENABLED_FIX_148,
    DEFAULT_REVIEW_CHECKLIST,
    DELEGATED_AUTHORITY_ENABLED_FIX_148,
    GOVERNANCE_DELIBERATION_FIX,
    GOVERNANCE_DELIBERATION_INVARIANT,
    GOVERNANCE_DELIBERATION_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_148,
    MUTATION_PERFORMED_FIX_148,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_store import (
    list_governance_deliberation_records,
)
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
    build_mission_readiness_review,
)


@dataclass(frozen=True)
class GovernanceDeliberationResult:
    ok: bool
    session_id: str
    workspace: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _alternative_path_comparison(*, review: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths: list[dict[str, Any]] = []
    go_rec = ((review.get("sections") or {}).get("go_no_go_hold_recommendation") or {})
    advisory = str(go_rec.get("recommendation") or "hold")

    for label, description in (
        ("go", "Proceed when readiness elevated and human authority confirms."),
        ("hold", "Pause for approvals, evidence, or incident resolution."),
        ("no-go", "Defer when critical blockers or incidents prevent safe advance."),
    ):
        paths.append(
            {
                "path": label,
                "description": description,
                "advisory_alignment": label == advisory,
                "read_only": True,
            }
        )

    for rec in _by_kind(records, "alternative_path"):
        paths.append(
            {
                "path": rec.get("metadata", {}).get("path_label") or "recorded_alternative",
                "description": rec.get("content"),
                "recorded": True,
                "record_id": rec.get("record_id"),
                "read_only": True,
            }
        )
    return paths


def _review_checklist(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    persisted = {str(r.get("metadata", {}).get("checklist_key") or ""): r for r in _by_kind(records, "checklist_item")}
    checklist: list[dict[str, Any]] = []
    for key in DEFAULT_REVIEW_CHECKLIST:
        row = persisted.get(key)
        checklist.append(
            {
                "checklist_key": key,
                "label": key.replace("_", " "),
                "checked": bool(row),
                "note": (row or {}).get("content"),
                "record_id": (row or {}).get("record_id"),
                "human_confirmed": bool(row),
                "read_only": not bool(row),
            }
        )
    return checklist


def _governance_discussion_timeline(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for rec in records:
        timeline.append(
            {
                "recorded_at": rec.get("recorded_at"),
                "kind": rec.get("kind"),
                "author": rec.get("author"),
                "content": rec.get("content"),
                "record_id": rec.get("record_id"),
                "deliberation_memory_only": True,
            }
        )
    return timeline


def build_governance_deliberation_workspace(*, session_id: str) -> GovernanceDeliberationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    readiness_result = build_mission_readiness_review(session_id=sid)
    review = readiness_result.review if readiness_result.ok else {}
    plan_id = str(review.get("plan_id") or "") or None
    correlation_id = str(review.get("correlation_id") or "") or None

    records = list_governance_deliberation_records(session_id=sid, plan_id=plan_id)

    sections = {
        "readiness_review_context": {
            "go_no_go_hold": review.get("go_no_go_hold"),
            "readiness_score_summary": (review.get("sections") or {}).get("readiness_score_summary"),
            "blocker_count": len((review.get("sections") or {}).get("blockers") or []),
            "pending_approval_count": len((review.get("sections") or {}).get("pending_approvals") or []),
            "read_only": True,
        },
        "operator_notes": _by_kind(records, "operator_note"),
        "reviewer_annotations": _by_kind(records, "reviewer_annotation"),
        "structured_concerns": _by_kind(records, "structured_concern"),
        "dissent_tracking": _by_kind(records, "dissent"),
        "rationale_capture": _by_kind(records, "rationale"),
        "alternative_path_comparison": _alternative_path_comparison(review=review, records=records),
        "review_checklist": _review_checklist(records=records),
        "approval_rejection_rationale": _by_kind(records, "approval_rejection_rationale"),
        "governance_discussion_timeline": _governance_discussion_timeline(records),
        "decision_justification_records": _by_kind(records, "decision_justification"),
    }

    workspace: dict[str, Any] = {
        "schema_version": GOVERNANCE_DELIBERATION_SCHEMA_VERSION,
        "fix": GOVERNANCE_DELIBERATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_148,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_148,
        "automatic_approval_enabled": AUTOMATIC_APPROVAL_ENABLED_FIX_148,
        "automatic_rejection_enabled": AUTOMATIC_REJECTION_ENABLED_FIX_148,
        "autonomous_policy_evolution_enabled": AUTONOMOUS_POLICY_EVOLUTION_ENABLED_FIX_148,
        "delegated_authority_enabled": DELEGATED_AUTHORITY_ENABLED_FIX_148,
        "invariant": GOVERNANCE_DELIBERATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "deliberation_record_count": len(records),
        "institutional_governance_memory": True,
        "sources": {
            "mission_readiness_review": readiness_result.ok,
            "deliberation_records": len(records),
        },
    }
    return GovernanceDeliberationResult(
        ok=True,
        session_id=sid,
        workspace=workspace,
        detail="Governance deliberation workspace assembled (collaborative reasoning — no approval automation).",
    )
