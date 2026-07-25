# SPDX-License-Identifier: Apache-2.0
"""FIX 194 — Atlas Trader trust report freeze service (compose-only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_194_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
    ATLAS_PILOT_SESSIONS,
    ATLAS_TRADER_REPOSITORY,
)
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_store import (
    has_pilot_arc_trust_decision,
    list_atlas_trader_pilot_arc_orchestrator_records,
    registered_repo_issue,
)
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_contract import (
    ATLAS_TRADER_REPO_ISSUE,
    ATLAS_TRADER_TRUST_REPORT_FREEZE_FIX,
    ATLAS_TRADER_TRUST_REPORT_FREEZE_INVARIANT,
    ATLAS_TRADER_TRUST_REPORT_FREEZE_ORIGIN,
    ATLAS_TRADER_TRUST_REPORT_FREEZE_PRINCIPLES,
    ATLAS_TRADER_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
    AUTOMATIC_EXPANSION_ENABLED_FIX_194,
    CROSS_REPO_AUTHORITY_FIX_194,
    EXECUTION_PERFORMED_FIX_194,
    FORBIDDEN_ATLAS_TRUST_FREEZE_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_194,
    GOVERNANCE_MUTATION_PERFORMED_FIX_194,
    NEXORA_EXPANSION_BLOCKED_BY_DEFAULT_FIX_194,
    PILOT_EXECUTION_AUTHORITY_FIX_194,
    PILOT_REEXECUTION_PERFORMED_FIX_194,
    TRUST_GRANTING_AUTHORITY_FIX_194,
    TRUST_INHERITANCE_ENABLED_FIX_194,
    TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_194,
)
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
    has_atlas_trust_report_freeze_record,
    has_human_trust_decision_approve,
    has_human_trust_decision_reject,
    list_atlas_trader_trust_report_freeze_records,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    list_pilot_run_audits,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    list_issue_intent_alignment_records,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import replay_link_key, timeline_link_ref
from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline
from aethos_core.software_delivery.github_pr_open_store import load_github_pr_open_for_plan

_PILOT_TIMELINE: tuple[dict[str, str], ...] = (
    {
        "pilot_id": "atlas-pilot-1",
        "phase": "1",
        "question": "Can the governed loop run on Atlas Trader?",
        "default_answer": "Pending evidence",
    },
    {
        "pilot_id": "atlas-pilot-2",
        "phase": "2",
        "question": "Can drift be detected before patch authority?",
        "default_answer": "Pending evidence",
    },
    {
        "pilot_id": "atlas-pilot-3",
        "phase": "3",
        "question": "Can the correct change complete to PR Open?",
        "default_answer": "Pending evidence",
    },
)


@dataclass(frozen=True)
class AtlasTraderTrustReportFreezeResult:
    ok: bool
    session_id: str
    atlas_trader_trust_report_freeze: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _latest_audit_for_session(session_id: str) -> dict[str, Any] | None:
    audits = [
        a
        for a in list_pilot_run_audits(session_id=session_id, limit=20)
        if ATLAS_TRADER_REPOSITORY in str(a.get("repo_issue") or "")
        or session_id in str(a.get("session_id") or "")
    ]
    return audits[0] if audits else None


def _discover_atlas_audits() -> dict[str, dict[str, Any] | None]:
    return {sid: _latest_audit_for_session(sid) for sid in ATLAS_PILOT_SESSIONS}


def _pilot_complete(*, audit: dict[str, Any] | None, require_pr_open: bool = False) -> bool:
    if not audit:
        return False
    outcome = str(audit.get("outcome") or "")
    report = dict(audit.get("pilot_report") or {})
    stages = list(report.get("stages_satisfied") or audit.get("stages_completed") or [])
    if require_pr_open:
        return outcome == "complete" and "pr_open" in stages
    return outcome == "complete" or bool(stages)


def _pilot2_alignment_demonstrated(*, audit: dict[str, Any] | None, session_id: str) -> bool:
    if not audit:
        return False
    if str(audit.get("outcome") or "") == "partial":
        blockers = audit.get("blockers") or []
        if any("intent_alignment" in str(b) for b in blockers):
            return True
    if list_issue_intent_alignment_records(session_id=session_id):
        return True
    report = dict(audit.get("pilot_report") or {})
    return "intent_alignment" in list(report.get("stages_satisfied") or [])


def _infer_arc_state_for_trust_freeze() -> str:
    if has_pilot_arc_trust_decision():
        return "CONDITIONALLY_TRUSTED"

    audits = _discover_atlas_audits()
    p1 = _pilot_complete(audit=audits.get(ATLAS_PILOT_SESSIONS[0]))
    p2 = _pilot2_alignment_demonstrated(
        audit=audits.get(ATLAS_PILOT_SESSIONS[1]), session_id=ATLAS_PILOT_SESSIONS[1]
    )
    p3 = _pilot_complete(audit=audits.get(ATLAS_PILOT_SESSIONS[2]), require_pr_open=True)

    if p3:
        return "TRUST_REVIEW_PENDING"
    if audits.get(ATLAS_PILOT_SESSIONS[2]):
        return "PILOT_3_RUNNING"
    if p2:
        return "PILOT_2_COMPLETE"
    if audits.get(ATLAS_PILOT_SESSIONS[1]):
        return "PILOT_2_RUNNING"
    if p1:
        return "PILOT_1_COMPLETE"
    if audits.get(ATLAS_PILOT_SESSIONS[0]):
        return "PILOT_1_RUNNING"
    return "UNPROVEN"


def _pilot_answer(*, pilot_id: str, audit: dict[str, Any] | None) -> str:
    if not audit:
        return "Pending evidence"
    outcome = str(audit.get("outcome") or "")
    if pilot_id == "atlas-pilot-2" and outcome == "partial":
        blockers = audit.get("blockers") or []
        if any("intent_alignment" in str(b) for b in blockers):
            return "Yes — alignment gate blocked drift"
    if outcome == "complete":
        return "Yes"
    if outcome == "partial":
        return "Partial"
    return "No"


def _compose_pilot_evidence(
    *,
    pilot_id: str,
    template: dict[str, str],
    audit: dict[str, Any] | None,
) -> dict[str, Any]:
    report = dict(audit.get("pilot_report") or {}) if audit else {}
    stages_satisfied = list(report.get("stages_satisfied") or [])
    if not stages_satisfied and audit:
        stages_satisfied = list(audit.get("stages_completed") or [])
    stages_pending = list(report.get("stages_pending") or [])
    blockers = list(audit.get("blockers") or []) if audit else []

    alignment_records = (
        list_issue_intent_alignment_records(session_id=pilot_id) if pilot_id == "atlas-pilot-2" else []
    )

    pr_meta: dict[str, Any] = {}
    if pilot_id == "atlas-pilot-3" and audit:
        timeline = build_software_delivery_timeline(session_id=pilot_id)
        plan_id = str((timeline.get("plan") or {}).get("plan_id") or "")
        if plan_id:
            pr_open = load_github_pr_open_for_plan(plan_id=plan_id) or {}
            pr_meta = {
                "pr_url": pr_open.get("pr_url") or pr_open.get("html_url"),
                "pr_number": pr_open.get("pr_number"),
                "status": pr_open.get("status"),
                "branch_name": pr_open.get("branch_name"),
            }

    finding = ""
    if audit:
        finding = str(report.get("failure_class") or "")
        if not finding and blockers:
            finding = str(blockers[0])
        if not finding:
            outcome = str(audit.get("outcome") or "")
            if outcome:
                finding = f"pilot_outcome:{outcome}"

    return {
        "pilot_id": pilot_id,
        "phase": template.get("phase"),
        "question": template.get("question"),
        "answer": _pilot_answer(pilot_id=pilot_id, audit=audit),
        "finding": finding or "Awaiting live pilot evidence",
        "audit_id": audit.get("audit_id") if audit else None,
        "pilot_outcome": audit.get("outcome") if audit else None,
        "stages_satisfied": stages_satisfied,
        "stages_pending": stages_pending,
        "blockers": blockers,
        "alignment_record_count": len(alignment_records),
        "pr_metadata": pr_meta or None,
        "read_only": True,
    }


def _agent_metrics_summary() -> dict[str, Any]:
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_store import (
        list_agent_execution_quality_throughput_metrics_records,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        list_bounded_multi_agent_delivery_execution_records,
    )

    intervention_count = 0
    receipt_count = 0
    for sid in ATLAS_PILOT_SESSIONS:
        for record in list_agent_execution_quality_throughput_metrics_records(session_id=sid):
            if str(record.get("author") or "") == "operator":
                intervention_count += 1
        receipt_count += len(list_bounded_multi_agent_delivery_execution_records(session_id=sid))
    return {
        "intervention_count": intervention_count,
        "agent_execution_record_count": receipt_count,
        "composed_from_fix_189_190": True,
        "read_only": True,
    }


def _trust_boundary_matrix(*, trust_status: str) -> list[dict[str, Any]]:
    return [
        {
            "matrix_id": "atlas-conditionally-trusted",
            "status": "conditionally_trusted"
            if trust_status == "CONDITIONALLY_TRUSTED"
            else "trust_review_pending"
            if trust_status == "TRUST_REVIEW_PENDING"
            else "not_trusted"
            if trust_status == "NOT_TRUSTED"
            else "unproven",
            "scope": ATLAS_TRADER_REPOSITORY,
            "capabilities": [
                "Bounded documentation changes (when operator approves trust)",
                "Single-file modifications (when operator approves trust)",
                "Low blast-radius Atlas Trader work",
                "Governed path through FIX 193 pilot arc",
            ],
            "expansion_blocked": trust_status != "CONDITIONALLY_TRUSTED",
            "read_only": True,
        },
        {
            "matrix_id": "atlas-not-yet-trusted",
            "status": "not_yet_trusted",
            "scope": "Requires independent evidence — never inherited from AethOS or PilotOS UI",
            "capabilities": [
                "Multi-file refactors",
                "Cross-subsystem changes",
                "Provider integrations",
                "Production-impacting changes",
                "pilotmain/nexora-monorepo-starter (until Atlas Trader trust freeze complete)",
            ],
            "read_only": True,
        },
    ]


def _expansion_recommendation(
    *,
    freeze_recorded: bool,
    human_trust_approved: bool,
    pilot3_complete: bool,
    arc_state: str,
) -> dict[str, Any]:
    if human_trust_approved and pilot3_complete:
        value = "CONDITIONALLY_EXPAND"
        reason = (
            "Operator approved Atlas Trader trust after review. "
            "Nexora pilot may proceed under independent evidence requirements."
        )
        nexora_blocked = False
    elif freeze_recorded and arc_state == "TRUST_REVIEW_PENDING":
        value = "EXPAND_WITH_REVIEW"
        reason = "Atlas Trader trust freeze recorded — complete human trust decision before Nexora."
        nexora_blocked = True
    elif pilot3_complete or arc_state == "TRUST_REVIEW_PENDING":
        value = "EXPAND_WITH_REVIEW"
        reason = "Atlas pilot arc evidence available — record trust freeze and human trust decision."
        nexora_blocked = True
    else:
        value = "DO_NOT_EXPAND"
        reason = "Atlas Trader pilot arc incomplete — Nexora remains blocked."
        nexora_blocked = True

    return {
        "recommendation_id": "atlas-trader-expansion",
        "recommendation": value,
        "nexora_expansion_blocked": nexora_blocked,
        "trust_report_freeze_recorded": freeze_recorded,
        "human_trust_decision_approve": human_trust_approved,
        "reason": reason,
        "read_only": True,
    }


def _derive_trust_status(
    *,
    arc_state: str,
    human_trust_approved: bool,
    human_trust_rejected: bool,
    pilot3_complete: bool,
    any_evidence: bool,
) -> str:
    if human_trust_rejected:
        return "NOT_TRUSTED"
    if human_trust_approved and pilot3_complete:
        return "CONDITIONALLY_TRUSTED"
    if arc_state == "TRUST_REVIEW_PENDING" or pilot3_complete:
        return "TRUST_REVIEW_PENDING"
    if any_evidence:
        return "TRUST_REVIEW_PENDING"
    return "UNPROVEN"


def _evidence_index(
    *,
    audits: dict[str, dict[str, Any] | None],
    pilot_evidence: list[dict[str, Any]],
    arc_board: dict[str, Any],
    metrics: dict[str, Any],
    freeze_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for pilot_id, audit in audits.items():
        if audit:
            entries.append(
                {
                    "ref_id": f"audit-{pilot_id}",
                    "kind": "pilot_run_audit",
                    "pilot_id": pilot_id,
                    "audit_id": audit.get("audit_id"),
                    "read_only": True,
                }
            )
    for item in pilot_evidence:
        if item.get("pr_metadata"):
            entries.append(
                {
                    "ref_id": f"pr-{item.get('pilot_id')}",
                    "kind": "github_pr_reference",
                    **(item.get("pr_metadata") or {}),
                    "read_only": True,
                }
            )
    entries.append(
        {
            "ref_id": "atlas-issue",
            "kind": "github_issue",
            "repo_issue": arc_board.get("repo_issue") or ATLAS_TRADER_REPO_ISSUE,
            "repository": ATLAS_TRADER_REPOSITORY,
            "read_only": True,
        }
    )
    entries.append(
        {
            "ref_id": "fix-193-pilot-arc",
            "kind": "atlas_trader_pilot_arc_orchestrator",
            "arc_state": arc_board.get("arc_state"),
            "read_only": True,
        }
    )
    if metrics.get("agent_execution_record_count"):
        entries.append({"ref_id": "fix-189-190-metrics", "kind": "agent_execution_metrics", **metrics})
    for record in freeze_records[-5:]:
        entries.append(
            {
                "ref_id": f"freeze-{record.get('record_id')}",
                "kind": str(record.get("kind") or "operator_note"),
                "content": record.get("content"),
                "read_only": True,
            }
        )
    return entries


def build_atlas_trader_trust_report_freeze(*, session_id: str) -> AtlasTraderTrustReportFreezeResult:
    sid = (session_id or "default").strip()[:64] or "default"
    exported_at = _exported_at()

    arc_state = _infer_arc_state_for_trust_freeze()
    repo_issue = str(registered_repo_issue() or ATLAS_TRADER_REPO_ISSUE)

    audits = _discover_atlas_audits()
    pilot_evidence = [
        _compose_pilot_evidence(pilot_id=t["pilot_id"], template=t, audit=audits.get(t["pilot_id"]))
        for t in _PILOT_TIMELINE
    ]

    pilot3_audit = audits.get(ATLAS_PILOT_SESSIONS[2])
    pilot3_report = dict(pilot3_audit.get("pilot_report") or {}) if pilot3_audit else {}
    pilot3_stages = (
        list(pilot3_report.get("stages_satisfied") or pilot3_audit.get("stages_completed") or [])
        if pilot3_audit
        else []
    )
    pilot3_complete = (
        pilot3_audit is not None
        and str(pilot3_audit.get("outcome") or "") == "complete"
        and "pr_open" in pilot3_stages
    )

    freeze_records = list_atlas_trader_trust_report_freeze_records()
    freeze_recorded = has_atlas_trust_report_freeze_record() or bool(freeze_records)
    human_trust_approved = has_human_trust_decision_approve()
    human_trust_rejected = has_human_trust_decision_reject()
    any_evidence = any(audits.values())

    trust_status = _derive_trust_status(
        arc_state=arc_state,
        human_trust_approved=human_trust_approved,
        human_trust_rejected=human_trust_rejected,
        pilot3_complete=pilot3_complete,
        any_evidence=any_evidence,
    )

    metrics = _agent_metrics_summary()
    intervention_notes = [r for r in freeze_records if str(r.get("kind") or "") == "intervention_note"]
    operator_observations = [
        r for r in list_atlas_trader_pilot_arc_orchestrator_records()
        if str(r.get("kind") or "") == "atlas_pilot_observation"
    ]

    blockers: list[str] = []
    if not any_evidence and not freeze_recorded:
        blockers.append("no_atlas_pilot_artifacts")

    timeline_ref = timeline_link_ref(
        lane="software_delivery",
        action="atlas_trader_trust_report_freeze",
        timestamp=exported_at,
    )
    replay_key = replay_link_key(
        source=ATLAS_TRADER_TRUST_REPORT_FREEZE_ORIGIN,
        lane="software_delivery",
        action="atlas_trader_trust_report_freeze",
        timestamp=exported_at,
        anchor=ATLAS_TRADER_REPOSITORY,
    )

    executive_summary = (
        f"Atlas Trader trust baseline for {ATLAS_TRADER_REPOSITORY}. "
        f"Arc state: {arc_state}. Trust status: {trust_status}. "
        "Trust freeze composes evidence only — humans grant trust."
    )

    sections = {
        "atlas_trust_report": [
            {
                "report_id": "atlas-trader-trust-report-freeze",
                "repository": ATLAS_TRADER_REPOSITORY,
                "repo_issue": repo_issue,
                "executive_summary": executive_summary,
                "evidence_summary": (
                    f"{sum(1 for a in audits.values() if a)} pilot audits, "
                    f"{metrics.get('agent_execution_record_count', 0)} execution receipts, "
                    f"{len(operator_observations)} operator observations."
                ),
                "pilot_progression": {
                    "pilot_1_complete": _pilot_complete(audit=audits.get(ATLAS_PILOT_SESSIONS[0])),
                    "pilot_2_complete": _pilot2_alignment_demonstrated(
                        audit=audits.get(ATLAS_PILOT_SESSIONS[1]),
                        session_id=ATLAS_PILOT_SESSIONS[1],
                    ),
                    "pilot_3_complete": pilot3_complete,
                },
                "successes": [e for e in pilot_evidence if e.get("answer") == "Yes"],
                "failures": [e for e in pilot_evidence if e.get("answer") in {"No", "Partial"}],
                "fixes_applied": [],
                "intervention_analysis": {
                    "intervention_note_count": len(intervention_notes),
                    "operator_observation_count": len(operator_observations),
                    "metrics_intervention_count": metrics.get("intervention_count", 0),
                },
                "trust_status": trust_status,
                "arc_state": arc_state,
                "separate_from_aethos_and_pilotos": True,
                "read_only": True,
            }
        ],
        "atlas_evidence_timeline": pilot_evidence,
        "trust_review_dashboard": [
            {
                "dashboard_id": "atlas-trust-review",
                "arc_state": arc_state,
                "trust_status": trust_status,
                "freeze_recorded": freeze_recorded,
                "human_trust_decision_required": arc_state == "TRUST_REVIEW_PENDING"
                and not human_trust_approved,
                "human_trust_approved": human_trust_approved,
                "human_trust_rejected": human_trust_rejected,
                "intervention_note_count": len(intervention_notes),
                "evidence_completeness": "complete" if pilot3_complete else "partial" if any_evidence else "none",
                "trust_review_state": trust_status,
                "read_only": True,
            }
        ],
        "trust_boundary_matrix": _trust_boundary_matrix(trust_status=trust_status),
        "atlas_trust_recommendation": [
            {
                "recommendation_id": "atlas-trust-status",
                "trust_status": trust_status,
                "trust_granting_authority": False,
                "trust_rationale": (
                    "Independent Atlas Trader pilot evidence required. "
                    "Human trust decision required before CONDITIONALLY_TRUSTED."
                ),
                "read_only": True,
            }
        ],
        "expansion_recommendation": [
            _expansion_recommendation(
                freeze_recorded=freeze_recorded,
                human_trust_approved=human_trust_approved,
                pilot3_complete=pilot3_complete,
                arc_state=arc_state,
            )
        ],
        "evidence_index": _evidence_index(
            audits=audits,
            pilot_evidence=pilot_evidence,
            arc_board={"arc_state": arc_state, "repo_issue": repo_issue},
            metrics=metrics,
            freeze_records=freeze_records,
        ),
        "fix_193_upstream_composition": [
            {
                "composition_id": "fix-193-pilot-arc-read",
                "arc_state": arc_state,
                "composed_from_arc_state_inference": True,
                "pilot_reexecution_performed": False,
                "read_only": True,
            }
        ],
        "fix_189_190_metrics_composition": [metrics],
        "fix_191_260_portfolio_composition": [
            {
                "composition_id": "fix-191-260-read",
                "cross_repo_validation_consumes_atlas_trust": True,
                "portfolio_intelligence_available": True,
                "read_only": True,
            }
        ],
        "audit_replay_linkage_at_trust_freeze": [
            {
                "link_id": "atlas-trust-freeze-audit-replay",
                "timeline_link_ref": timeline_ref,
                "replay_link_key": replay_key,
                "focus_pilot_id": "atlas-pilot-3",
                "focus_audit_id": pilot3_audit.get("audit_id") if pilot3_audit else None,
                "read_only": True,
            }
        ],
        "forbidden_atlas_trust_freeze_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_ATLAS_TRUST_FREEZE_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": ATLAS_TRADER_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        "fix": ATLAS_TRADER_TRUST_REPORT_FREEZE_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": False,
        "execution_performed": EXECUTION_PERFORMED_FIX_194,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_194,
        "trust_granting_authority": TRUST_GRANTING_AUTHORITY_FIX_194,
        "trust_inheritance_enabled": TRUST_INHERITANCE_ENABLED_FIX_194,
        "pilot_execution_authority": PILOT_EXECUTION_AUTHORITY_FIX_194,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_194,
        "automatic_expansion_enabled": AUTOMATIC_EXPANSION_ENABLED_FIX_194,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_194,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_194,
        "trust_report_composes_artifacts_only": TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_194,
        "nexora_expansion_blocked": NEXORA_EXPANSION_BLOCKED_BY_DEFAULT_FIX_194
        and not human_trust_approved,
        "invariant": ATLAS_TRADER_TRUST_REPORT_FREEZE_INVARIANT,
        "session_id": sid,
        "repository": ATLAS_TRADER_REPOSITORY,
        "repo_issue": repo_issue,
        "sections": sections,
        "trust_status": trust_status,
        "trust_report_freeze_recorded": freeze_recorded,
        "human_trust_decision_approve": human_trust_approved,
        "pilot_3_complete": pilot3_complete,
        "arc_state": arc_state,
        "freeze_record_count": len(freeze_records),
        "fix_194_certification_requirements": list(FIX_194_CERTIFICATION_REQUIREMENTS),
        "atlas_trader_trust_report_freeze_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in ATLAS_TRADER_TRUST_REPORT_FREEZE_PRINCIPLES
        ],
        "sources": {
            "pilot_sessions": list(ATLAS_PILOT_SESSIONS),
            "pilot_audits_discovered": sum(1 for a in audits.values() if a),
            "composes_fix_193_pilot_arc_state": True,
            "composes_fix_189_190_metrics": True,
            "composes_fix_191_260": True,
            "pilot_reexecution_performed": False,
        },
    }

    return AtlasTraderTrustReportFreezeResult(
        ok=True,
        session_id=sid,
        atlas_trader_trust_report_freeze=payload,
        blockers=blockers,
        detail="Atlas Trader trust report freeze composed from pilot arc artifacts (trust_freeze ≠ trust_granting)."
        if any_evidence or freeze_recorded
        else "Advisory trust report — Atlas Trader pilot evidence not yet captured.",
    )
