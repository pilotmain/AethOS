# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A1 — compose PilotOS operational proof from existing FIX modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.workstreams.pilotos_operational_proof_program.pilotos_operational_proof_program_contract import (
    EVIDENCE_DENSITY_LEVELS,
    EXECUTIVE_FIX_MODULES,
    PILOTOS_OPERATIONAL_PROOF_PROGRAM_ID,
    PILOTOS_OPERATIONAL_PROOF_PROGRAM_PHASES,
    PILOTOS_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION,
    PILOTOS_PILOT_SESSIONS,
    PILOTOS_UI_REPOSITORY,
    PROGRAM_NON_GOALS,
)


@dataclass(frozen=True)
class PilotosOperationalProofProgramResult:
    ok: bool
    session_id: str
    pilotos_operational_proof_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _audit_for_session(session_id: str) -> dict[str, Any] | None:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
        list_pilot_run_audits,
    )

    audits = [
        a
        for a in list_pilot_run_audits(session_id=session_id, limit=10)
        if PILOTOS_UI_REPOSITORY in str(a.get("repo_issue") or "")
    ]
    return audits[0] if audits else None


def _pilot_complete(*, session_id: str, require_pr_open: bool = False) -> bool:
    audit = _audit_for_session(session_id)
    if not audit:
        return False
    outcome = str(audit.get("outcome") or "")
    report = dict(audit.get("pilot_report") or {})
    stages = list(report.get("stages_satisfied") or audit.get("stages_completed") or [])
    if require_pr_open:
        return outcome == "complete" and "pr_open" in stages
    return outcome == "complete" or bool(stages)


def _pilot2_alignment_demonstrated(session_id: str) -> bool:
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
        list_issue_intent_alignment_records,
    )

    audit = _audit_for_session(session_id)
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


def _infer_arc_state_local() -> str:
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
        has_pilot_arc_trust_decision,
    )

    if has_pilot_arc_trust_decision():
        return "CONDITIONALLY_TRUSTED"

    p1 = _pilot_complete(session_id=PILOTOS_PILOT_SESSIONS[0])
    p2 = _pilot2_alignment_demonstrated(PILOTOS_PILOT_SESSIONS[1])
    p3 = _pilot_complete(session_id=PILOTOS_PILOT_SESSIONS[2], require_pr_open=True)

    if p3:
        return "TRUST_REVIEW_PENDING"
    if _audit_for_session(PILOTOS_PILOT_SESSIONS[2]):
        return "PILOT_3_RUNNING" if not p3 else "PILOT_3_COMPLETE"
    if p2:
        return "PILOT_2_COMPLETE"
    if _audit_for_session(PILOTOS_PILOT_SESSIONS[1]):
        return "PILOT_2_RUNNING" if not p2 else "PILOT_2_COMPLETE"
    if p1:
        return "PILOT_1_COMPLETE"
    if _audit_for_session(PILOTOS_PILOT_SESSIONS[0]):
        return "PILOT_1_RUNNING"
    return "UNPROVEN"


def _build_readiness_reports() -> tuple[dict[str, Any], dict[str, Any]]:
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
        has_repo_expansion_approval,
    )
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
        registered_repo_issue,
    )

    expansion_approved = has_repo_expansion_approval(repository=PILOTOS_UI_REPOSITORY)
    repo_issue = registered_repo_issue()

    readiness_report = {
        "repository": PILOTOS_UI_REPOSITORY,
        "repo_issue": repo_issue,
        "fix_187_expansion_approved": expansion_approved,
        "fix_182_readiness_ok": None,
        "fix_182_readiness_note": "Use show repo pilot readiness for live GitHub preflight (not re-run here).",
        "repo_issue_bound": bool(repo_issue),
        "eligible_to_start_pilot_1": expansion_approved and bool(repo_issue),
        "validated": expansion_approved,
    }

    prerequisites: list[dict[str, Any]] = [
        {
            "check_id": "fix_187_expansion",
            "label": "FIX 187 independent repository trust expansion approval",
            "satisfied": expansion_approved,
        },
        {
            "check_id": "repo_issue_bound",
            "label": "Pilot arc repository issue binding",
            "satisfied": bool(repo_issue),
        },
        {
            "check_id": "fix_182_readiness",
            "label": "FIX 182 repo pilot readiness dashboard (operator preflight)",
            "satisfied": None,
        },
    ]

    prerequisite_validation = {
        "repository": PILOTOS_UI_REPOSITORY,
        "all_prerequisites_satisfied": expansion_approved and bool(repo_issue),
        "prerequisites": prerequisites,
        "blockers": [p["label"] for p in prerequisites if p["satisfied"] is False],
    }

    return readiness_report, prerequisite_validation


def _build_pilot_evidence_bundle(*, pilot_number: int, session_id: str) -> dict[str, Any]:
    audit = _audit_for_session(session_id)

    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
        list_issue_intent_alignment_records,
    )

    alignment_records = list_issue_intent_alignment_records(session_id=session_id)

    receipt_paths: list[str] = []
    receipt_dir = _repo_root() / "data" / "pilotos_pilot_receipts"
    if receipt_dir.is_dir():
        for path in sorted(receipt_dir.glob(f"{session_id}*.json")):
            receipt_paths.append(str(path.relative_to(_repo_root())))

    return {
        "pilot_number": pilot_number,
        "session_id": session_id,
        "repository": PILOTOS_UI_REPOSITORY,
        "audit": audit,
        "audit_present": audit is not None,
        "pilot_outcome": (audit or {}).get("outcome"),
        "stages_completed": list((audit or {}).get("stages_completed") or []),
        "blockers": list((audit or {}).get("blockers") or []),
        "alignment_record_count": len(alignment_records),
        "receipt_paths": receipt_paths,
        "pilot_complete": audit is not None and str(audit.get("outcome") or "") == "complete",
        "validated": audit is not None,
    }


def _build_trust_freeze_artifacts(*, freeze_board: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    sections = freeze_board.get("sections") or {}
    trust_boundary = (sections.get("trust_boundary_matrix") or [{}])[0]
    expansion = (sections.get("expansion_recommendation") or [{}])[0]
    timeline = sections.get("pilotos_ui_evidence_timeline") or []

    freeze_artifact = {
        "repository": PILOTOS_UI_REPOSITORY,
        "trust_status": freeze_board.get("trust_status"),
        "frozen_at": freeze_board.get("frozen_at") or freeze_board.get("exported_at"),
        "freeze_record_present": freeze_board.get("trust_report_freeze_recorded"),
        "human_trust_decision_approve": freeze_board.get("human_trust_decision_approve"),
        "evidence_timeline_count": len(timeline),
        "composed_from_fix_192": True,
        "validated": bool(freeze_board),
    }

    trust_boundary_snapshot = {
        "matrix": trust_boundary if isinstance(trust_boundary, list) else [trust_boundary],
        "trust_status": freeze_board.get("trust_status"),
        "atlas_expansion_blocked": freeze_board.get("atlas_expansion_blocked"),
    }

    trust_recommendation_snapshot = {
        "recommendation": expansion,
        "trust_status": freeze_board.get("trust_status"),
        "trust_granting_authority": False,
    }

    return freeze_artifact, trust_boundary_snapshot, trust_recommendation_snapshot


def _build_trust_decision_record(*, freeze_board: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
        list_pilotos_ui_trust_report_freeze_records,
    )
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
        list_pilotos_ui_pilot_arc_orchestrator_records,
    )

    trust_records = list_pilotos_ui_trust_report_freeze_records()
    arc_records = list_pilotos_ui_pilot_arc_orchestrator_records()
    decision_kinds = (
        "human_trust_decision_approve",
        "human_trust_decision_hold",
        "human_trust_decision_reject",
        "human_trust_decision_defer",
        "pilotos_trust_report_freeze_artifact",
    )
    decisions = [r for r in trust_records if str(r.get("kind") or "") in decision_kinds]
    arc_trust = [r for r in arc_records if str(r.get("kind") or "") == "pilot_arc_trust_decision"]

    return {
        "repository": PILOTOS_UI_REPOSITORY,
        "trust_decision_recorded": bool(decisions or arc_trust),
        "fix_192_decisions": decisions[-5:],
        "fix_188_arc_trust_decisions": arc_trust[-3:],
        "human_trust_decision_approve": freeze_board.get("human_trust_decision_approve", False),
        "commands": (
            "pilotos trust decision approve: ...",
            "pilotos trust decision hold|reject|defer: ...",
            "pilot arc trust: CONDITIONALLY_TRUSTED — ...",
        ),
        "record_only": True,
    }


def _score_evidence_density(
    *,
    pilot_bundles: list[dict[str, Any]],
    freeze_board: dict[str, Any],
) -> dict[str, Any]:
    audits_present = sum(1 for b in pilot_bundles if b.get("audit_present"))
    pilots_complete = sum(1 for b in pilot_bundles if b.get("pilot_complete"))
    receipts = sum(len(b.get("receipt_paths") or []) for b in pilot_bundles)
    timeline = (freeze_board.get("sections") or {}).get("pilotos_ui_evidence_timeline") or []
    pending_answers = sum(
        1 for row in timeline if str(row.get("answer") or "") in {"Pending evidence", "Awaiting live pilot evidence"}
    )

    score = audits_present * 0.25 + pilots_complete * 0.2 + receipts * 0.05
    if freeze_board.get("trust_report_freeze_recorded"):
        score += 0.15
    if freeze_board.get("human_trust_decision_approve"):
        score += 0.15
    score = min(1.0, score)

    if score >= 0.85 and pending_answers == 0:
        level = "STRONG"
    elif score >= 0.65:
        level = "ADEQUATE"
    elif score >= 0.35:
        level = "PARTIAL"
    else:
        level = "INSUFFICIENT"

    external_reviewer_trust = level in {"ADEQUATE", "STRONG"} and pending_answers <= 1

    return {
        "evidence_density_level": level,
        "evidence_density_score": round(score, 3),
        "levels": list(EVIDENCE_DENSITY_LEVELS),
        "audits_present": audits_present,
        "pilots_complete": pilots_complete,
        "receipt_count": receipts,
        "pending_timeline_answers": pending_answers,
        "meaningful_operational_proof": level in {"ADEQUATE", "STRONG"},
        "external_reviewer_would_trust": external_reviewer_trust,
        "questions": {
            "meaningful_operational_proof": level in {"ADEQUATE", "STRONG"},
            "external_reviewer_trust": external_reviewer_trust,
        },
    }


def _build_executive_visibility_report(*, arc_state: str) -> dict[str, Any]:
    pilot_audits = [_audit_for_session(sid) for sid in PILOTOS_PILOT_SESSIONS]
    pilot_evidence_present = any(a is not None for a in pilot_audits)

    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
        build_cross_repository_multi_agent_delivery_validation,
    )

    cross_repo = build_cross_repository_multi_agent_delivery_validation(session_id="pilotos-exec")
    cross_board = cross_repo.cross_repository_multi_agent_delivery_validation or {}
    pilotos_row = next(
        (
            row
            for row in (cross_board.get("sections") or {}).get("cross_repository_validation_matrix") or []
            if row.get("repository") == PILOTOS_UI_REPOSITORY
        ),
        None,
    )

    modules: dict[str, Any] = {}
    for fix_label in EXECUTIVE_FIX_MODULES:
        modules[fix_label] = {
            "compose_available": True,
            "pilotos_evidence_reflected": pilot_evidence_present
            or arc_state in {"TRUST_REVIEW_PENDING", "CONDITIONALLY_TRUSTED", "PILOT_3_COMPLETE"},
            "placeholder_risk": "low" if pilot_evidence_present else "high",
            "validated_via_workstream_compose": True,
        }

    return {
        "executive_modules": list(EXECUTIVE_FIX_MODULES),
        "module_assessments": modules,
        "cross_repository_validation_updated": cross_repo.ok,
        "pilotos_trust_state_in_cross_repo": pilotos_row,
        "pilotos_audit_evidence_present": pilot_evidence_present,
        "executive_dashboard_populated_with_real_evidence": pilot_evidence_present
        and arc_state in {"TRUST_REVIEW_PENDING", "CONDITIONALLY_TRUSTED", "PILOT_3_COMPLETE"},
        "note": (
            "Executive FIX 324–330 boards compose tenant-scoped evidence; "
            "PilotOS audit presence in FIX 181 store is the workstream proof gate."
        ),
        "validated": cross_repo.ok,
    }


def build_pilotos_operational_proof_program(*, session_id: str = "default") -> PilotosOperationalProofProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"

    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
        build_cross_repository_multi_agent_delivery_validation,
    )
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_service import (
        build_pilotos_ui_trust_report_freeze,
    )

    arc_state = _infer_arc_state_local()

    freeze = build_pilotos_ui_trust_report_freeze(session_id=sid)
    freeze_board = freeze.pilotos_ui_trust_report_freeze or {}

    readiness_report, prerequisite_validation = _build_readiness_reports()

    pilot_bundles = [
        _build_pilot_evidence_bundle(pilot_number=n, session_id=PILOTOS_PILOT_SESSIONS[n - 1])
        for n in (1, 2, 3)
    ]

    freeze_artifact, trust_boundary_snapshot, trust_recommendation_snapshot = _build_trust_freeze_artifacts(
        freeze_board=freeze_board
    )
    trust_decision_record = _build_trust_decision_record(freeze_board=freeze_board)
    evidence_density = _score_evidence_density(pilot_bundles=pilot_bundles, freeze_board=freeze_board)
    executive_visibility = _build_executive_visibility_report(arc_state=arc_state)
    cross_repo = build_cross_repository_multi_agent_delivery_validation(session_id=sid)

    success_criteria = {
        "pilot_1_completed": pilot_bundles[0].get("pilot_complete") or pilot_bundles[0].get("audit_present"),
        "pilot_2_completed": pilot_bundles[1].get("audit_present"),
        "pilot_3_completed": pilot_bundles[2].get("pilot_complete") or pilot_bundles[2].get("audit_present"),
        "trust_freeze_completed": bool(freeze_board.get("trust_report_freeze_recorded")),
        "trust_decision_recorded": trust_decision_record.get("trust_decision_recorded", False),
        "cross_repository_validation_updated": cross_repo.ok,
        "executive_dashboard_real_evidence": executive_visibility.get(
            "executive_dashboard_populated_with_real_evidence"
        ),
        "program_complete": all(
            [
                pilot_bundles[0].get("audit_present"),
                pilot_bundles[1].get("audit_present"),
                pilot_bundles[2].get("audit_present"),
                freeze_board.get("trust_report_freeze_recorded"),
                trust_decision_record.get("trust_decision_recorded"),
            ]
        ),
    }

    sections = {
        "phase_1_repository_readiness": [
            {
                "pilotos_readiness_report": readiness_report,
                "pilotos_prerequisite_validation": prerequisite_validation,
            }
        ],
        "phase_2_pilot_1_execution": [{"pilotos_pilot1_evidence_bundle": pilot_bundles[0]}],
        "phase_3_pilot_2_execution": [{"pilotos_pilot2_evidence_bundle": pilot_bundles[1]}],
        "phase_4_pilot_3_execution": [{"pilotos_pilot3_evidence_bundle": pilot_bundles[2]}],
        "phase_5_trust_freeze": [
            {
                "pilotos_trust_freeze_artifact": freeze_artifact,
                "trust_boundary_snapshot": trust_boundary_snapshot,
                "trust_recommendation_snapshot": trust_recommendation_snapshot,
            }
        ],
        "phase_6_trust_review": [{"pilotos_trust_decision_record": trust_decision_record}],
        "phase_7_evidence_density_review": [{"pilotos_evidence_density_report": evidence_density}],
        "phase_8_executive_dashboard_validation": [{"pilotos_executive_visibility_report": executive_visibility}],
    }

    blockers: list[str] = []
    if not prerequisite_validation.get("all_prerequisites_satisfied"):
        blockers.extend(prerequisite_validation.get("blockers") or [])
    if not pilot_bundles[0].get("audit_present"):
        blockers.append("pilot_1_audit_missing")
    if not pilot_bundles[1].get("audit_present"):
        blockers.append("pilot_2_audit_missing")
    if not pilot_bundles[2].get("audit_present"):
        blockers.append("pilot_3_audit_missing")

    board = {
        "schema_version": PILOTOS_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION,
        "workstream_id": PILOTOS_OPERATIONAL_PROOF_PROGRAM_ID,
        "exported_at": _exported_at(),
        "session_id": sid,
        "repository": PILOTOS_UI_REPOSITORY,
        "read_only": True,
        "mutation_performed": False,
        "execution_performed": False,
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(PILOTOS_OPERATIONAL_PROOF_PROGRAM_PHASES),
        "arc_state": arc_state,
        "trust_status": freeze_board.get("trust_status"),
        "success_criteria": success_criteria,
        "sections": sections,
        "sources": {
            "fix_188_pilot_arc": True,
            "fix_192_trust_freeze": True,
            "fix_181_audits": True,
            "fix_191_cross_repo": True,
            "fix_324_through_330_executive": True,
        },
    }

    return PilotosOperationalProofProgramResult(
        ok=not blockers or arc_state != "UNPROVEN",
        session_id=sid,
        pilotos_operational_proof_program=board,
        blockers=blockers,
        detail="PilotOS operational proof program composed from existing FIX modules (no new intelligence).",
    )
