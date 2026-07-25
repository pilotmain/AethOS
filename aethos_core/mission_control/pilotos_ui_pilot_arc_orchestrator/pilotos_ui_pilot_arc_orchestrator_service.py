# SPDX-License-Identifier: Apache-2.0
"""FIX 188 — PilotOS UI pilot arc orchestrator service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_188_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    list_pilot_run_audits,
)
from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
    has_repo_expansion_approval,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    list_issue_intent_alignment_records,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_service import (
    build_pilot_validation_trust_board,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188,
    DEPLOY_ENABLED_FIX_188,
    FORBIDDEN_PILOT_ARC_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_188,
    GOVERNANCE_MUTATION_PERFORMED_FIX_188,
    HIDDEN_PILOT_EXECUTION_ENABLED_FIX_188,
    MERGE_ENABLED_FIX_188,
    PILOTOS_PILOT_SESSIONS,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_FIX,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_INVARIANT,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ORIGIN,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_PRINCIPLES,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
    PILOTOS_UI_REPOSITORY,
    PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_188,
    PILOT_ARC_STATES,
    RAILWAY_MUTATION_ENABLED_FIX_188,
    TRUST_TRANSFER_ENABLED_FIX_188,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
    has_pilot_arc_trust_decision,
    list_pilotos_ui_pilot_arc_orchestrator_records,
    registered_repo_issue,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
    build_repo_pilot_readiness_dashboard,
)


@dataclass(frozen=True)
class PilotosUiPilotArcOrchestratorResult:
    ok: bool
    session_id: str
    pilotos_ui_pilot_arc_orchestrator: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class PilotosUiPilotArcRunResult:
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


def _audits_for_session(session_id: str) -> list[dict[str, Any]]:
    return [
        a
        for a in list_pilot_run_audits(session_id=session_id, limit=20)
        if PILOTOS_UI_REPOSITORY in str(a.get("repo_issue") or "")
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
    records = list_issue_intent_alignment_records(session_id=session_id)
    if records:
        return True
    report = dict(audit.get("pilot_report") or {})
    return "intent_alignment" in list(report.get("stages_satisfied") or [])


def _expansion_gates() -> dict[str, Any]:
    expansion_approved = has_repo_expansion_approval(repository=PILOTOS_UI_REPOSITORY)
    readiness = build_repo_pilot_readiness_dashboard(session_id="default")
    readiness_ok = readiness.ok and not readiness.blockers
    return {
        "fix_187_expansion_approved": expansion_approved,
        "fix_182_readiness_ok": readiness_ok,
        "repo_issue_bound": bool(registered_repo_issue()),
        "eligible_to_start_pilot_1": expansion_approved and readiness_ok,
        "read_only": True,
    }


def _infer_arc_state(*, running_pilot: int | None = None) -> str:
    if has_pilot_arc_trust_decision():
        return "CONDITIONALLY_TRUSTED"

    p1 = _pilot_complete(session_id=PILOTOS_PILOT_SESSIONS[0])
    p2 = _pilot2_alignment_demonstrated(PILOTOS_PILOT_SESSIONS[1])
    p3 = _pilot_complete(session_id=PILOTOS_PILOT_SESSIONS[2], require_pr_open=True)

    if running_pilot == 3:
        return "PILOT_3_RUNNING"
    if running_pilot == 2:
        return "PILOT_2_RUNNING"
    if running_pilot == 1:
        return "PILOT_1_RUNNING"

    if p3:
        return "TRUST_REVIEW_PENDING"
    if _latest_audit(PILOTOS_PILOT_SESSIONS[2]):
        return "PILOT_3_RUNNING" if not p3 else "PILOT_3_COMPLETE"
    if p2:
        return "PILOT_2_COMPLETE"
    if _latest_audit(PILOTOS_PILOT_SESSIONS[1]):
        return "PILOT_2_RUNNING" if not p2 else "PILOT_2_COMPLETE"
    if p1:
        return "PILOT_1_COMPLETE"
    if _latest_audit(PILOTOS_PILOT_SESSIONS[0]):
        return "PILOT_1_RUNNING"
    return "UNPROVEN"


def _pilot_evidence_registry() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for idx, session_id in enumerate(PILOTOS_PILOT_SESSIONS, start=1):
        audit = _latest_audit(session_id)
        bundle_ok = False
        if audit:
            bundle = build_evidence_bundle(session_id=session_id)
            bundle_ok = bundle.ok if bundle else False
        alignment = list_issue_intent_alignment_records(session_id=session_id)
        validation = build_pilot_validation_trust_board(session_id=session_id) if audit else None
        entries.append(
            {
                "evidence_id": f"pilotos-pilot-{idx}",
                "pilot_number": idx,
                "session_id": session_id,
                "repository": PILOTOS_UI_REPOSITORY,
                "audit_id": audit.get("audit_id") if audit else None,
                "pilot_outcome": audit.get("outcome") if audit else None,
                "alignment_record_count": len(alignment),
                "evidence_bundle_ok": bundle_ok,
                "human_effort_score": validation.pilot_validation_trust_board.get("human_effort_score")
                if validation and validation.ok
                else None,
                "independent_evidence": True,
                "read_only": True,
            }
        )
    receipt_dir = _repo_root() / "data" / "pilotos_pilot_receipts"
    if receipt_dir.is_dir():
        for path in sorted(receipt_dir.glob("pilotos-pilot-*.json"))[-3:]:
            entries.append(
                {
                    "evidence_id": f"receipt-{path.stem}",
                    "kind": "live_receipt",
                    "receipt_path": str(path.relative_to(_repo_root())),
                    "read_only": True,
                }
            )
    return entries


def _trust_recommendation(*, arc_state: str) -> dict[str, Any]:
    if arc_state == "CONDITIONALLY_TRUSTED":
        return {
            "recommendation_id": "pilotos-trust-recommendation",
            "trust_status": "CONDITIONALLY_TRUSTED",
            "trust_granted_automatically": False,
            "rationale": "Operator recorded pilot arc trust decision after review.",
            "read_only": True,
        }
    if arc_state == "TRUST_REVIEW_PENDING":
        return {
            "recommendation_id": "pilotos-trust-recommendation",
            "trust_status": "PENDING_OPERATOR_REVIEW",
            "trust_granted_automatically": False,
            "rationale": "Pilot 1–3 evidence complete — operator must record pilot arc trust decision.",
            "read_only": True,
        }
    return {
        "recommendation_id": "pilotos-trust-recommendation",
        "trust_status": "UNPROVEN",
        "trust_granted_automatically": False,
        "rationale": "Pilot arc incomplete — trust cannot be recommended yet.",
        "read_only": True,
    }


def _expansion_readiness(*, arc_state: str, gates: dict[str, Any]) -> dict[str, Any]:
    atlas_next = arc_state == "CONDITIONALLY_TRUSTED"
    return {
        "assessment_id": "pilotos-expansion-readiness",
        "pilotos_ui_arc_state": arc_state,
        "ready_for_atlas_trader_pilot": atlas_next,
        "requires_pilotos_trust_freeze_first": arc_state == "TRUST_REVIEW_PENDING",
        "fix_187_gates": gates,
        "read_only": True,
    }


def build_pilotos_ui_pilot_arc_orchestrator(*, session_id: str) -> PilotosUiPilotArcOrchestratorResult:
    sid = (session_id or "default").strip()[:64] or "default"
    exported_at = _exported_at()
    gates = _expansion_gates()
    arc_state = _infer_arc_state()
    repo_issue = registered_repo_issue()

    blockers: list[str] = []
    if not gates["fix_187_expansion_approved"]:
        blockers.append("fix_187_expansion_not_approved")

    sections = {
        "repository_registration": [
            {
                "registration_id": "pilotos-ui",
                "repository": PILOTOS_UI_REPOSITORY,
                "repo_issue": repo_issue,
                "pilot_sessions": list(PILOTOS_PILOT_SESSIONS),
                "trust_inherited_from": None,
                "read_only": True,
            }
        ],
        "pilot_arc_state_machine": [
            {
                "state_id": "pilotos-ui-arc",
                "current_state": arc_state,
                "states": list(PILOT_ARC_STATES),
                "pilot_1_complete": _pilot_complete(session_id=PILOTOS_PILOT_SESSIONS[0]),
                "pilot_2_complete": _pilot2_alignment_demonstrated(PILOTOS_PILOT_SESSIONS[1]),
                "pilot_3_complete": _pilot_complete(
                    session_id=PILOTOS_PILOT_SESSIONS[2], require_pr_open=True
                ),
                "read_only": True,
            }
        ],
        "expansion_gates": [gates],
        "pilot_evidence_registry": _pilot_evidence_registry(),
        "pilotos_ui_trust_report": [
            {
                "report_id": "pilotos-ui-trust-report",
                "repository": PILOTOS_UI_REPOSITORY,
                "arc_state": arc_state,
                "repo_issue": repo_issue,
                "separate_from_aethos_trust_report": True,
                "read_only": True,
            }
        ],
        "pilotos_ui_evidence_bundle": [
            {
                "bundle_id": "pilotos-ui-evidence",
                "sessions": list(PILOTOS_PILOT_SESSIONS),
                "composed_from_fix_181_audits": True,
                "read_only": True,
            }
        ],
        "pilotos_ui_trust_recommendation": [_trust_recommendation(arc_state=arc_state)],
        "expansion_readiness_assessment": [_expansion_readiness(arc_state=arc_state, gates=gates)],
        "forbidden_pilot_arc_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_PILOT_ARC_ACTIONS
        ],
    }

    pilotos_ui_pilot_arc_orchestrator: dict[str, Any] = {
        "schema_version": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
        "fix": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": False,
        "execution_performed": False,
        "pilot_execution_performed": False,
        "automatic_trust_granting_enabled": AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188,
        "trust_transfer_enabled": TRUST_TRANSFER_ENABLED_FIX_188,
        "pilot_arc_routes_through_fix_181": PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_188,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_188,
        "merge_enabled": MERGE_ENABLED_FIX_188,
        "deploy_enabled": DEPLOY_ENABLED_FIX_188,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_188,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_188,
        "invariant": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_INVARIANT,
        "session_id": sid,
        "repository": PILOTOS_UI_REPOSITORY,
        "repo_issue": repo_issue,
        "arc_state": arc_state,
        "sections": sections,
        "expansion_gates_satisfied": gates["eligible_to_start_pilot_1"],
        "orchestrator_record_count": len(list_pilotos_ui_pilot_arc_orchestrator_records()),
        "fix_188_certification_requirements": list(FIX_188_CERTIFICATION_REQUIREMENTS),
        "pilotos_ui_pilot_arc_orchestrator_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_PRINCIPLES
        ],
        "sources": {
            "composes_fix_181_through_187": True,
            "pilot_sessions": list(PILOTOS_PILOT_SESSIONS),
        },
    }

    ok = True
    return PilotosUiPilotArcOrchestratorResult(
        ok=ok,
        session_id=sid,
        pilotos_ui_pilot_arc_orchestrator=pilotos_ui_pilot_arc_orchestrator,
        blockers=blockers,
        detail="PilotOS UI pilot arc orchestrator assembled (pilot arc orchestration ≠ trust granting).",
    )


def run_pilotos_ui_pilot_arc_pilot(*, pilot_number: int) -> PilotosUiPilotArcRunResult:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        run_end_to_end_repo_development_pilot,
    )
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
        append_pilotos_ui_pilot_arc_orchestrator_record,
    )

    if pilot_number not in (1, 2, 3):
        return PilotosUiPilotArcRunResult(
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
    if pilot_number == 2 and not _pilot_complete(session_id=PILOTOS_PILOT_SESSIONS[0]):
        blockers.append("pilot_1_not_complete")
    if pilot_number == 3 and not _pilot2_alignment_demonstrated(PILOTOS_PILOT_SESSIONS[1]):
        blockers.append("pilot_2_not_complete")
    if blockers:
        return PilotosUiPilotArcRunResult(
            ok=False,
            pilot_number=pilot_number,
            session_id="",
            blockers=blockers,
            detail="Pilot arc prerequisites not satisfied.",
        )

    session_id = PILOTOS_PILOT_SESSIONS[pilot_number - 1]
    repo_issue = registered_repo_issue()

    append_pilotos_ui_pilot_arc_orchestrator_record(
        session_id=session_id,
        kind="pilot_arc_transition",
        content=f"PILOT_{pilot_number}_RUNNING",
        repo_issue=repo_issue,
        metadata={"pilot_number": pilot_number, "state": f"PILOT_{pilot_number}_RUNNING"},
    )

    outcome = run_end_to_end_repo_development_pilot(session_id=session_id, repo_issue=repo_issue)

    append_pilotos_ui_pilot_arc_orchestrator_record(
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

    return PilotosUiPilotArcRunResult(
        ok=outcome.ok,
        pilot_number=pilot_number,
        session_id=session_id,
        audit_id=outcome.audit_id,
        stages_completed=list(outcome.stages_completed),
        blockers=list(outcome.blockers),
        detail="PilotOS UI pilot routed through FIX 181 harness.",
    )
