# SPDX-License-Identifier: Apache-2.0
"""FIX 149 — multi-operator governance collaboration workspace."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_collaboration.governance_collaboration_contract import (
    AUTOMATIC_MERGE_DEPLOY_ENABLED_FIX_149,
    AUTOMATIC_QUORUM_APPROVAL_ENABLED_FIX_149,
    AUTONOMOUS_ORGANIZATIONAL_DECISIONS_ENABLED_FIX_149,
    DEFAULT_QUORUM_ADVISORY_SIZE,
    DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_149,
    GOVERNANCE_COLLABORATION_FIX,
    GOVERNANCE_COLLABORATION_INVARIANT,
    GOVERNANCE_COLLABORATION_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_149,
    MUTATION_PERFORMED_FIX_149,
    REVIEWER_ROLES,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_store import (
    list_governance_collaboration_records,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_service import (
    build_governance_deliberation_workspace,
)


@dataclass(frozen=True)
class GovernanceCollaborationResult:
    ok: bool
    session_id: str
    collaboration: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _named_reviewers(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    reviewers: list[dict[str, Any]] = []
    for rec in records:
        name = str(rec.get("reviewer_name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        reviewers.append(
            {
                "reviewer_name": name,
                "reviewer_role": rec.get("reviewer_role"),
                "first_seen_at": rec.get("recorded_at"),
                "read_only": True,
            }
        )
    for rec in _by_kind(records, "named_reviewer"):
        name = str(rec.get("reviewer_name") or rec.get("content") or "").strip()
        if name and name not in seen:
            seen.add(name)
            reviewers.append(
                {
                    "reviewer_name": name,
                    "reviewer_role": rec.get("reviewer_role"),
                    "first_seen_at": rec.get("recorded_at"),
                    "read_only": True,
                }
            )
    return reviewers


def _role_aware_deliberation(*, records: list[dict[str, Any]], deliberation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rec in _by_kind(records, "role_deliberation"):
        rows.append(
            {
                "reviewer_name": rec.get("reviewer_name"),
                "reviewer_role": rec.get("reviewer_role"),
                "content": rec.get("content"),
                "recorded_at": rec.get("recorded_at"),
                "read_only": True,
            }
        )
    for role in REVIEWER_ROLES:
        role_records = [r for r in records if str(r.get("reviewer_role") or "") == role]
        if role_records:
            rows.append(
                {
                    "reviewer_role": role,
                    "participation_count": len(role_records),
                    "latest_at": role_records[-1].get("recorded_at"),
                    "read_only": True,
                }
            )
    concerns = (deliberation.get("sections") or {}).get("structured_concerns") or []
    if concerns and not rows:
        rows.append(
            {
                "signal": "deliberation_concerns_present",
                "concern_count": len(concerns),
                "detail": "Role-aware review should address structured concerns from FIX 148.",
                "read_only": True,
            }
        )
    return rows[:20]


def _quorum_aware_discussion(*, records: list[dict[str, Any]]) -> dict[str, Any]:
    acknowledgments = _by_kind(records, "reviewer_acknowledgment")
    assignments = _by_kind(records, "reviewer_assignment")
    unique_reviewers = {str(r.get("reviewer_name") or "") for r in acknowledgments if r.get("reviewer_name")}
    advisory_quorum = DEFAULT_QUORUM_ADVISORY_SIZE
    met = len(unique_reviewers) >= advisory_quorum
    return {
        "advisory_quorum_size": advisory_quorum,
        "acknowledgment_count": len(acknowledgments),
        "unique_reviewers_acknowledged": len(unique_reviewers),
        "assignment_count": len(assignments),
        "quorum_advisory_met": met,
        "automatic_quorum_approval": False,
        "discussion_notes": _by_kind(records, "quorum_discussion"),
        "read_only": True,
    }


def _review_ownership(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "owner": rec.get("reviewer_name") or rec.get("content"),
            "reviewer_role": rec.get("reviewer_role"),
            "content": rec.get("content"),
            "recorded_at": rec.get("recorded_at"),
            "record_id": rec.get("record_id"),
            "read_only": True,
        }
        for rec in _by_kind(records, "review_ownership")
    ]


def _decision_participation_graph(*, records: list[dict[str, Any]], deliberation: dict[str, Any]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = [{"id": "mission_review", "kind": "review_root", "read_only": True}]
    edges: list[dict[str, Any]] = []

    for reviewer in _named_reviewers(records):
        node_id = f"reviewer:{reviewer['reviewer_name']}"
        nodes.append(
            {
                "id": node_id,
                "kind": "reviewer",
                "reviewer_name": reviewer["reviewer_name"],
                "reviewer_role": reviewer.get("reviewer_role"),
                "read_only": True,
            }
        )
        edges.append({"from": "mission_review", "to": node_id, "kind": "participates", "read_only": True})

    for rec in _by_kind(records, "governance_handoff"):
        target = str(rec.get("metadata", {}).get("handoff_to") or rec.get("content") or "")
        if target:
            edges.append(
                {
                    "from": f"reviewer:{rec.get('reviewer_name') or 'unknown'}",
                    "to": f"reviewer:{target}",
                    "kind": "handoff",
                    "read_only": True,
                }
            )

    timeline = (deliberation.get("sections") or {}).get("governance_discussion_timeline") or []
    for entry in timeline[:10]:
        author = str(entry.get("author") or "operator")
        node_id = f"deliberation:{author}"
        if not any(n.get("id") == node_id for n in nodes):
            nodes.append({"id": node_id, "kind": "deliberation_author", "author": author, "read_only": True})
        edges.append({"from": node_id, "to": "mission_review", "kind": "contributed", "read_only": True})

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes[:30],
        "edges": edges[:30],
        "read_only": True,
    }


def build_governance_collaboration_workspace(*, session_id: str) -> GovernanceCollaborationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    deliberation_result = build_governance_deliberation_workspace(session_id=sid)
    deliberation = deliberation_result.workspace if deliberation_result.ok else {}
    plan_id = str(deliberation.get("plan_id") or "") or None
    correlation_id = str(deliberation.get("correlation_id") or "") or None

    records = list_governance_collaboration_records(session_id=sid, plan_id=plan_id)

    sections = {
        "named_reviewers": _named_reviewers(records),
        "role_aware_deliberation": _role_aware_deliberation(records=records, deliberation=deliberation),
        "quorum_aware_discussion": _quorum_aware_discussion(records=records),
        "review_ownership": _review_ownership(records),
        "delegated_review_requests": _by_kind(records, "delegated_review_request"),
        "reviewer_assignments": _by_kind(records, "reviewer_assignment"),
        "reviewer_acknowledgments": _by_kind(records, "reviewer_acknowledgment"),
        "governance_handoff_tracking": _by_kind(records, "governance_handoff"),
        "unresolved_concern_escalation": _by_kind(records, "unresolved_concern_escalation"),
        "decision_participation_graph": _decision_participation_graph(
            records=records, deliberation=deliberation
        ),
        "deliberation_workspace_context": {
            "deliberation_record_count": deliberation.get("deliberation_record_count", 0),
            "go_no_go_hold": (deliberation.get("sections") or {})
            .get("readiness_review_context", {})
            .get("go_no_go_hold"),
            "read_only": True,
        },
    }

    collaboration: dict[str, Any] = {
        "schema_version": GOVERNANCE_COLLABORATION_SCHEMA_VERSION,
        "fix": GOVERNANCE_COLLABORATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_149,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_149,
        "delegated_execution_authority_enabled": DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_149,
        "automatic_quorum_approval_enabled": AUTOMATIC_QUORUM_APPROVAL_ENABLED_FIX_149,
        "automatic_merge_deploy_enabled": AUTOMATIC_MERGE_DEPLOY_ENABLED_FIX_149,
        "autonomous_organizational_decisions_enabled": AUTONOMOUS_ORGANIZATIONAL_DECISIONS_ENABLED_FIX_149,
        "invariant": GOVERNANCE_COLLABORATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "collaboration_record_count": len(records),
        "institutional_collaborative_governance": True,
        "sources": {
            "governance_deliberation": deliberation_result.ok,
            "collaboration_records": len(records),
        },
    }
    return GovernanceCollaborationResult(
        ok=True,
        session_id=sid,
        collaboration=collaboration,
        detail="Multi-operator governance collaboration assembled (no delegated execution authority).",
    )
