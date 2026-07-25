# SPDX-License-Identifier: Apache-2.0
"""FIX 193 — Atlas Trader pilot arc orchestrator service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_193_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
    ATLAS_PILOT_SESSIONS,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_FIX,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_INVARIANT,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_ORIGIN,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_PRINCIPLES,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
    ATLAS_TRADER_REPOSITORY,
    CROSS_REPO_AUTHORITY_FIX_193,
    DEPLOY_AUTHORITY_FIX_193,
    FORBIDDEN_PILOT_ARC_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_193,
    GOVERNANCE_MUTATION_PERFORMED_FIX_193,
    HIDDEN_PILOT_EXECUTION_ENABLED_FIX_193,
    MERGE_AUTHORITY_FIX_193,
    PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_193,
    PILOT_ARC_STATES,
    PILOT_EXECUTION_BYPASS_ENABLED_FIX_193,
    RAILWAY_MUTATION_ENABLED_FIX_193,
    ROLLBACK_AUTHORITY_FIX_193,
    TRUST_GRANTING_AUTHORITY_FIX_193,
    TRUST_INHERITANCE_ENABLED_FIX_193,
)
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_store import (
    has_pilot_arc_trust_decision,
    list_atlas_trader_pilot_arc_orchestrator_records,
    registered_repo_issue,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    list_pilot_run_audits,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
    has_repo_expansion_approval,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    list_issue_intent_alignment_records,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
    has_pilot_arc_trust_decision as pilotos_has_trust_decision,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
    has_human_trust_decision_approve,
    has_pilotos_trust_report_freeze_record,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
    build_repo_pilot_readiness_dashboard,
)


@dataclass(frozen=True)
class AtlasTraderPilotArcOrchestratorResult:
    ok: bool
    session_id: str
    atlas_trader_pilot_arc_orchestrator: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class AtlasTraderPilotArcRunResult:
    ok: bool
    pilot_number: int
    session_id: str
    audit_id: str = ""
    stages_completed: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _pilotos_trust_baseline_satisfied() -> bool:
    return (
        pilotos_has_trust_decision()
        or has_human_trust_decision_approve()
        or has_pilotos_trust_report_freeze_record()
    )


def _audits_for_session(session_id: str) -> list[dict[str, Any]]:
    return [
        a
        for a in list_pilot_run_audits(session_id=session_id, limit=20)
        if ATLAS_TRADER_REPOSITORY in str(a.get("repo_issue") or "")
        or session_id in str(a.get("session_id") or "")
    ]


def _latest_audit(session_id: str) -> dict[str, Any] | None:
    audits = _audits_for_session(session_id)
    return audits[0] if audits else None


def _pilot_complete(*, session_id: str, require_pr_open: bool = False) -> bool:
    audit = _latest_audit(session_id)
    if not audit:
        return False
    outcome = str(audit.get("outcome") or "")
    report = dict(audit.get("pilot_report") or {})
    stages = list(report.get("stages_satisfied") or audit.get("stages_completed") or [])
    if require_pr_open:
        return outcome == "complete" and "pr_open" in stages
    return outcome == "complete" or bool(stages)


def _pilot2_alignment_demonstrated(session_id: str) -> bool:
    audit = _latest_audit(session_id)
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


def _expansion_gates() -> dict[str, Any]:
    expansion_approved = has_repo_expansion_approval(repository=ATLAS_TRADER_REPOSITORY)
    pilotos_baseline = _pilotos_trust_baseline_satisfied()
    readiness = build_repo_pilot_readiness_dashboard(session_id="default")
    readiness_ok = readiness.ok and not readiness.blockers
    eligible = expansion_approved and pilotos_baseline and readiness_ok
    return {
        "fix_187_expansion_approved": expansion_approved,
        "pilotos_ui_trust_baseline_satisfied": pilotos_baseline,
        "fix_182_readiness_ok": readiness_ok,
        "repo_issue_bound": bool(registered_repo_issue()),
        "eligible_to_start_pilot_1": eligible,
        "read_only": True,
    }


def _infer_arc_state(*, running_pilot: int | None = None) -> str:
    gates = _expansion_gates()
    if has_pilot_arc_trust_decision():
        return "CONDITIONALLY_TRUSTED"

    if not gates["eligible_to_start_pilot_1"]:
        return "UNPROVEN"

    p1 = _pilot_complete(session_id=ATLAS_PILOT_SESSIONS[0])
    p2 = _pilot2_alignment_demonstrated(ATLAS_PILOT_SESSIONS[1])
    p3 = _pilot_complete(session_id=ATLAS_PILOT_SESSIONS[2], require_pr_open=True)

    if running_pilot == 3:
        return "PILOT_3_RUNNING"
    if running_pilot == 2:
        return "PILOT_2_RUNNING"
    if running_pilot == 1:
        return "PILOT_1_RUNNING"

    if p3:
        return "TRUST_REVIEW_PENDING"
    if _latest_audit(ATLAS_PILOT_SESSIONS[2]):
        return "PILOT_3_RUNNING" if not p3 else "PILOT_3_COMPLETE"
    if p2:
        return "PILOT_2_COMPLETE"
    if _latest_audit(ATLAS_PILOT_SESSIONS[1]):
        return "PILOT_2_RUNNING" if not p2 else "PILOT_2_COMPLETE"
    if p1:
        return "PILOT_1_COMPLETE"
    if _latest_audit(ATLAS_PILOT_SESSIONS[0]):
        return "PILOT_1_RUNNING"
    return "PILOT_1_READY"


def _trust_recommendation_status(*, arc_state: str) -> str:
    if arc_state == "TRUST_REVIEW_PENDING":
        return "TRUST_REVIEW_PENDING"
    if arc_state in {"PILOT_1_READY", "UNPROVEN"}:
        return "NOT_READY"
    return "PILOTING"


def _atlas_evidence_registry() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for idx, session_id in enumerate(ATLAS_PILOT_SESSIONS, start=1):
        audit = _latest_audit(session_id)
        alignment = list_issue_intent_alignment_records(session_id=session_id)
        entries.append(
            {
                "evidence_id": f"atlas-pilot-{idx}",
                "pilot_number": idx,
                "session_id": session_id,
                "repository": ATLAS_TRADER_REPOSITORY,
                "audit_id": audit.get("audit_id") if audit else None,
                "pilot_outcome": audit.get("outcome") if audit else None,
                "alignment_record_count": len(alignment),
                "independent_evidence": True,
                "read_only": True,
            }
        )
    receipt_dir = _repo_root() / "data" / "atlas_trader_pilot_receipts"
    if receipt_dir.is_dir():
        for path in sorted(receipt_dir.glob("atlas-pilot-*.json"))[-3:]:
            entries.append(
                {
                    "evidence_id": f"receipt-{path.stem}",
                    "kind": "live_receipt",
                    "receipt_path": str(path.relative_to(_repo_root())),
                    "read_only": True,
                }
            )
    return entries


def _pilot_progress_timeline(*, arc_state: str) -> list[dict[str, Any]]:
    return [
        {
            "timeline_id": "atlas-pilot-progress",
            "arc_state": arc_state,
            "pilot_1_complete": _pilot_complete(session_id=ATLAS_PILOT_SESSIONS[0]),
            "pilot_2_complete": _pilot2_alignment_demonstrated(ATLAS_PILOT_SESSIONS[1]),
            "pilot_3_complete": _pilot_complete(
                session_id=ATLAS_PILOT_SESSIONS[2], require_pr_open=True
            ),
            "read_only": True,
        }
    ]


def _trust_recommendation(*, arc_state: str) -> dict[str, Any]:
    status = _trust_recommendation_status(arc_state=arc_state)
    rationales = {
        "NOT_READY": "Atlas expansion gates or PilotOS UI trust baseline not satisfied.",
        "PILOTING": "Atlas pilot arc in progress — independent evidence collection.",
        "TRUST_REVIEW_PENDING": "Pilot 1–3 complete — human trust decision occurs in FIX 194.",
    }
    return {
        "recommendation_id": "atlas-trust-recommendation",
        "trust_status": status,
        "trust_granted_automatically": False,
        "rationale": rationales.get(status, "Advisory only."),
        "read_only": True,
    }


def _pilot_readiness_summary(*, gates: dict[str, Any], arc_state: str) -> dict[str, Any]:
    return {
        "summary_id": "atlas-pilot-readiness",
        "arc_state": arc_state,
        "eligible_to_start_pilot_1": gates["eligible_to_start_pilot_1"],
        "pilotos_baseline_required": True,
        "pilotos_baseline_satisfied": gates["pilotos_ui_trust_baseline_satisfied"],
        "fix_187_required": True,
        "fix_187_satisfied": gates["fix_187_expansion_approved"],
        "trust_review_ready": arc_state == "TRUST_REVIEW_PENDING",
        "read_only": True,
    }


def build_atlas_trader_pilot_arc_orchestrator(*, session_id: str) -> AtlasTraderPilotArcOrchestratorResult:
    sid = (session_id or "default").strip()[:64] or "default"
    exported_at = _exported_at()
    gates = _expansion_gates()
    arc_state = _infer_arc_state()
    repo_issue = registered_repo_issue()

    blockers: list[str] = []
    if not gates["fix_187_expansion_approved"]:
        blockers.append("fix_187_expansion_not_approved")
    if not gates["pilotos_ui_trust_baseline_satisfied"]:
        blockers.append("pilotos_ui_trust_baseline_not_complete")

    sections = {
        "repository_registration": [
            {
                "registration_id": "atlas-trader",
                "repository": ATLAS_TRADER_REPOSITORY,
                "repo_issue": repo_issue,
                "pilot_sessions": list(ATLAS_PILOT_SESSIONS),
                "trust_inherited_from": None,
                "read_only": True,
            }
        ],
        "pilot_arc_state_machine": [
            {
                "state_id": "atlas-trader-arc",
                "current_state": arc_state,
                "states": list(PILOT_ARC_STATES),
                "pilot_1_complete": _pilot_complete(session_id=ATLAS_PILOT_SESSIONS[0]),
                "pilot_2_complete": _pilot2_alignment_demonstrated(ATLAS_PILOT_SESSIONS[1]),
                "pilot_3_complete": _pilot_complete(
                    session_id=ATLAS_PILOT_SESSIONS[2], require_pr_open=True
                ),
                "read_only": True,
            }
        ],
        "expansion_gates": [gates],
        "atlas_evidence_registry": _atlas_evidence_registry(),
        "atlas_pilot_dashboard": [
            {
                "dashboard_id": "atlas-trader-pilot-dashboard",
                "repository": ATLAS_TRADER_REPOSITORY,
                "arc_state": arc_state,
                "repo_issue": repo_issue,
                "last_pilot_result": _latest_audit(ATLAS_PILOT_SESSIONS[2])
                or _latest_audit(ATLAS_PILOT_SESSIONS[1])
                or _latest_audit(ATLAS_PILOT_SESSIONS[0]),
                "read_only": True,
            }
        ],
        "pilot_progress_timeline": _pilot_progress_timeline(arc_state=arc_state),
        "atlas_trust_recommendation": [_trust_recommendation(arc_state=arc_state)],
        "pilot_readiness_summary": [_pilot_readiness_summary(gates=gates, arc_state=arc_state)],
        "forbidden_pilot_arc_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_PILOT_ARC_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
        "fix": ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": False,
        "execution_performed": False,
        "pilot_execution_performed": False,
        "trust_granting_authority": TRUST_GRANTING_AUTHORITY_FIX_193,
        "trust_inheritance_enabled": TRUST_INHERITANCE_ENABLED_FIX_193,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_193,
        "pilot_execution_bypass_enabled": PILOT_EXECUTION_BYPASS_ENABLED_FIX_193,
        "pilot_arc_routes_through_fix_181": PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_193,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_193,
        "merge_authority": MERGE_AUTHORITY_FIX_193,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_193,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_193,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_193,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_193,
        "invariant": ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_INVARIANT,
        "session_id": sid,
        "repository": ATLAS_TRADER_REPOSITORY,
        "repo_issue": repo_issue,
        "arc_state": arc_state,
        "sections": sections,
        "expansion_gates_satisfied": gates["eligible_to_start_pilot_1"],
        "orchestrator_record_count": len(list_atlas_trader_pilot_arc_orchestrator_records()),
        "fix_193_certification_requirements": list(FIX_193_CERTIFICATION_REQUIREMENTS),
        "atlas_trader_pilot_arc_orchestrator_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_PRINCIPLES
        ],
        "sources": {
            "composes_fix_181_through_191_and_260": True,
            "pilot_sessions": list(ATLAS_PILOT_SESSIONS),
        },
    }

    return AtlasTraderPilotArcOrchestratorResult(
        ok=True,
        session_id=sid,
        atlas_trader_pilot_arc_orchestrator=payload,
        blockers=blockers,
        detail="Atlas Trader pilot arc orchestrator assembled (pilot arc orchestration ≠ trust granting).",
    )


def run_atlas_trader_pilot_arc_pilot(*, pilot_number: int) -> AtlasTraderPilotArcRunResult:
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_store import (
        append_atlas_trader_pilot_arc_orchestrator_record,
    )
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        run_end_to_end_repo_development_pilot,
    )

    if pilot_number not in (1, 2, 3):
        return AtlasTraderPilotArcRunResult(
            ok=False,
            pilot_number=pilot_number,
            session_id="",
            blockers=["invalid_pilot_number"],
            detail="Pilot number must be 1, 2, or 3.",
        )

    gates = _expansion_gates()
    blockers: list[str] = []
    if not gates["fix_187_expansion_approved"]:
        blockers.append("fix_187_expansion_not_approved")
    if not gates["pilotos_ui_trust_baseline_satisfied"]:
        blockers.append("pilotos_ui_trust_baseline_not_complete")
    if pilot_number == 2 and not _pilot_complete(session_id=ATLAS_PILOT_SESSIONS[0]):
        blockers.append("pilot_1_not_complete")
    if pilot_number == 3 and not _pilot2_alignment_demonstrated(ATLAS_PILOT_SESSIONS[1]):
        blockers.append("pilot_2_not_complete")
    if blockers:
        return AtlasTraderPilotArcRunResult(
            ok=False,
            pilot_number=pilot_number,
            session_id="",
            blockers=blockers,
            detail="Atlas pilot arc prerequisites not satisfied.",
        )

    session_id = ATLAS_PILOT_SESSIONS[pilot_number - 1]
    repo_issue = registered_repo_issue()

    append_atlas_trader_pilot_arc_orchestrator_record(
        session_id=session_id,
        kind="pilot_arc_transition",
        content=f"PILOT_{pilot_number}_RUNNING",
        repo_issue=repo_issue,
        metadata={"pilot_number": pilot_number, "state": f"PILOT_{pilot_number}_RUNNING"},
    )

    outcome = run_end_to_end_repo_development_pilot(session_id=session_id, repo_issue=repo_issue)

    append_atlas_trader_pilot_arc_orchestrator_record(
        session_id=session_id,
        kind="pilot_arc_transition",
        content=f"PILOT_{pilot_number}_{'COMPLETE' if outcome.ok else 'PARTIAL'}",
        repo_issue=repo_issue,
        metadata={
            "pilot_number": pilot_number,
            "audit_id": outcome.audit_id,
            "outcome_ok": outcome.ok,
            "stages_completed": outcome.stages_completed,
        },
    )

    return AtlasTraderPilotArcRunResult(
        ok=outcome.ok,
        pilot_number=pilot_number,
        session_id=session_id,
        audit_id=outcome.audit_id,
        stages_completed=list(outcome.stages_completed),
        blockers=list(outcome.blockers),
        detail="Atlas Trader pilot routed through FIX 181 harness.",
    )
