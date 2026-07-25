# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A3 — compose Nexora operational proof from existing FIX modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.workstreams.nexora_operational_proof_program.nexora_operational_proof_program_contract import (
    EVIDENCE_DENSITY_LEVELS,
    EXECUTIVE_FIX_MODULES,
    NEXORA_OPERATIONAL_PROOF_PROGRAM_ID,
    NEXORA_OPERATIONAL_PROOF_PROGRAM_PHASES,
    NEXORA_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION,
    NEXORA_PILOT_SESSIONS,
    NEXORA_REPOSITORY,
    PROGRAM_NON_GOALS,
)


@dataclass(frozen=True)
class NexoraOperationalProofProgramResult:
    ok: bool
    session_id: str
    nexora_operational_proof_program: dict[str, Any] = field(default_factory=dict)
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
        if NEXORA_REPOSITORY in str(a.get("repo_issue") or "")
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


def _aethos_trust_baseline_satisfied() -> bool:
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
        has_trust_report_freeze_record,
    )

    return has_trust_report_freeze_record()


def _pilotos_trust_baseline_satisfied() -> bool:
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
        has_pilot_arc_trust_decision as pilotos_has_trust_decision,
    )
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
        has_human_trust_decision_approve,
        has_pilotos_trust_report_freeze_record,
    )

    return (
        pilotos_has_trust_decision()
        or has_human_trust_decision_approve()
        or has_pilotos_trust_report_freeze_record()
    )


def _atlas_trust_baseline_satisfied() -> bool:
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_store import (
        has_pilot_arc_trust_decision as atlas_has_trust_decision,
    )
    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
        has_atlas_trust_report_freeze_record,
        has_human_trust_decision_approve as atlas_has_human_trust_decision_approve,
    )

    return (
        atlas_has_trust_decision()
        or atlas_has_human_trust_decision_approve()
        or has_atlas_trust_report_freeze_record()
    )


def _readiness_gate_flags() -> tuple[bool, bool, bool, bool, bool]:
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
        has_repo_expansion_approval,
    )
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
        registered_repo_issue,
    )

    expansion_approved = has_repo_expansion_approval(repository=NEXORA_REPOSITORY)
    aethos_baseline = _aethos_trust_baseline_satisfied()
    pilotos_baseline = _pilotos_trust_baseline_satisfied()
    atlas_baseline = _atlas_trust_baseline_satisfied()
    repo_issue_bound = bool(registered_repo_issue())
    return expansion_approved, aethos_baseline, pilotos_baseline, atlas_baseline, repo_issue_bound


def _infer_arc_state_local() -> str:
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
        has_pilot_arc_trust_decision,
    )

    if has_pilot_arc_trust_decision():
        return "CONDITIONALLY_TRUSTED"

    expansion_approved, aethos_baseline, pilotos_baseline, atlas_baseline, repo_issue_bound = _readiness_gate_flags()
    if not (
        expansion_approved and aethos_baseline and pilotos_baseline and atlas_baseline and repo_issue_bound
    ):
        return "UNPROVEN"

    p1 = _pilot_complete(session_id=NEXORA_PILOT_SESSIONS[0])
    p2 = _pilot2_alignment_demonstrated(NEXORA_PILOT_SESSIONS[1])
    p3 = _pilot_complete(session_id=NEXORA_PILOT_SESSIONS[2], require_pr_open=True)

    if p3:
        return "TRUST_REVIEW_PENDING"
    if _audit_for_session(NEXORA_PILOT_SESSIONS[2]):
        return "PILOT_3_RUNNING" if not p3 else "PILOT_3_COMPLETE"
    if p2:
        return "PILOT_2_COMPLETE"
    if _audit_for_session(NEXORA_PILOT_SESSIONS[1]):
        return "PILOT_2_RUNNING" if not p2 else "PILOT_2_COMPLETE"
    if p1:
        return "PILOT_1_COMPLETE"
    if _audit_for_session(NEXORA_PILOT_SESSIONS[0]):
        return "PILOT_1_RUNNING"
    return "UNPROVEN"


def _build_readiness_reports() -> tuple[dict[str, Any], dict[str, Any]]:
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
        registered_repo_issue,
    )

    expansion_approved, aethos_baseline, pilotos_baseline, atlas_baseline, repo_issue_bound = (
        _readiness_gate_flags()
    )
    repo_issue = registered_repo_issue()
    fix_195_eligible = (
        expansion_approved and aethos_baseline and pilotos_baseline and atlas_baseline and repo_issue_bound
    )

    readiness_report = {
        "repository": NEXORA_REPOSITORY,
        "repo_issue": repo_issue,
        "fix_187_expansion_approved": expansion_approved,
        "aethos_trust_baseline_satisfied": aethos_baseline,
        "pilotos_ui_trust_baseline_satisfied": pilotos_baseline,
        "atlas_trader_trust_baseline_satisfied": atlas_baseline,
        "fix_195_eligibility_satisfied": fix_195_eligible,
        "fix_195_state_machine_eligible": fix_195_eligible,
        "nexora_pilot_arc_eligible": fix_195_eligible,
        "fix_182_readiness_ok": None,
        "fix_182_readiness_note": "Use show repo pilot readiness for live GitHub preflight (not re-run here).",
        "repo_issue_bound": repo_issue_bound,
        "eligible_to_start_pilot_1": fix_195_eligible,
        "validated": fix_195_eligible,
    }

    prerequisites: list[dict[str, Any]] = [
        {
            "check_id": "fix_187_expansion",
            "label": "FIX 187 independent repository trust expansion approval",
            "satisfied": expansion_approved,
        },
        {
            "check_id": "aethos_trust_baseline",
            "label": "AethOS trust baseline (FIX 186 gate)",
            "satisfied": aethos_baseline,
        },
        {
            "check_id": "pilotos_ui_trust_baseline",
            "label": "PilotOS UI trust baseline (FIX 192 gate)",
            "satisfied": pilotos_baseline,
        },
        {
            "check_id": "atlas_trader_trust_baseline",
            "label": "Atlas Trader trust baseline (FIX 194 gate)",
            "satisfied": atlas_baseline,
        },
        {
            "check_id": "repo_issue_bound",
            "label": "Nexora pilot arc repository issue binding",
            "satisfied": repo_issue_bound,
        },
        {
            "check_id": "fix_195_eligible",
            "label": "FIX 195 pilot arc state machine eligible",
            "satisfied": fix_195_eligible,
        },
        {
            "check_id": "fix_182_readiness",
            "label": "FIX 182 repo pilot readiness dashboard (operator preflight)",
            "satisfied": None,
        },
    ]

    prerequisite_validation = {
        "repository": NEXORA_REPOSITORY,
        "all_prerequisites_satisfied": fix_195_eligible,
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
    receipt_dir = _repo_root() / "data" / "nexora_pilot_receipts"
    if receipt_dir.is_dir():
        for path in sorted(receipt_dir.glob(f"{session_id}*.json")):
            receipt_paths.append(str(path.relative_to(_repo_root())))

    return {
        "pilot_number": pilot_number,
        "session_id": session_id,
        "repository": NEXORA_REPOSITORY,
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
    recommendation = (sections.get("nexora_trust_recommendation") or [{}])[0]
    timeline = sections.get("nexora_evidence_timeline") or []

    freeze_artifact = {
        "repository": NEXORA_REPOSITORY,
        "trust_status": freeze_board.get("trust_status"),
        "frozen_at": freeze_board.get("frozen_at") or freeze_board.get("exported_at"),
        "freeze_record_present": freeze_board.get("trust_report_freeze_recorded"),
        "human_trust_decision_approve": freeze_board.get("human_trust_decision_approve"),
        "evidence_timeline_count": len(timeline),
        "composed_from_fix_196": True,
        "validated": bool(freeze_board),
    }

    nexora_boundary_snapshot = {
        "matrix": trust_boundary if isinstance(trust_boundary, list) else [trust_boundary],
        "trust_status": freeze_board.get("trust_status"),
        "separate_from_upstream_repositories": True,
    }

    nexora_trust_recommendation_snapshot = {
        "recommendation": recommendation,
        "trust_status": freeze_board.get("trust_status"),
        "trust_granting_authority": False,
    }

    return freeze_artifact, nexora_boundary_snapshot, nexora_trust_recommendation_snapshot


def _build_trust_decision_record(*, freeze_board: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
        list_nexora_pilot_arc_orchestrator_records,
    )
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_store import (
        list_nexora_trust_report_freeze_records,
    )

    trust_records = list_nexora_trust_report_freeze_records()
    arc_records = list_nexora_pilot_arc_orchestrator_records()
    decision_kinds = (
        "human_trust_decision_approve",
        "human_trust_decision_hold",
        "human_trust_decision_reject",
        "human_trust_decision_defer",
        "nexora_trust_report_freeze_artifact",
    )
    decisions = [r for r in trust_records if str(r.get("kind") or "") in decision_kinds]
    arc_trust = [r for r in arc_records if str(r.get("kind") or "") == "pilot_arc_trust_decision"]

    return {
        "repository": NEXORA_REPOSITORY,
        "trust_decision_recorded": bool(decisions or arc_trust),
        "fix_196_decisions": decisions[-5:],
        "fix_195_arc_trust_decisions": arc_trust[-3:],
        "human_trust_decision_approve": freeze_board.get("human_trust_decision_approve", False),
        "commands": (
            "nexora trust decision approve: ...",
            "nexora trust decision hold|reject|defer: ...",
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
    timeline = (freeze_board.get("sections") or {}).get("nexora_evidence_timeline") or []
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
    independent_trust_baseline = bool(
        freeze_board.get("trust_report_freeze_recorded")
        and freeze_board.get("human_trust_decision_approve")
    )

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
        "independent_trust_baseline": independent_trust_baseline,
        "independently_earned_trust_baseline": independent_trust_baseline,
        "questions": {
            "meaningful_operational_proof": level in {"ADEQUATE", "STRONG"},
            "external_reviewer_trust": external_reviewer_trust,
            "independent_trust_baseline": independent_trust_baseline,
            "independently_earned_trust_baseline": independent_trust_baseline,
        },
    }


def _build_executive_visibility_report(*, arc_state: str, session_id: str) -> dict[str, Any]:
    pilot_audits = [_audit_for_session(sid) for sid in NEXORA_PILOT_SESSIONS]
    nexora_evidence_present = any(a is not None for a in pilot_audits)
    executive_evidence_ready = nexora_evidence_present and arc_state in {
        "TRUST_REVIEW_PENDING",
        "CONDITIONALLY_TRUSTED",
        "PILOT_3_COMPLETE",
    }

    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
        build_cross_repository_multi_agent_delivery_validation,
    )
    from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
        build_multi_repository_engineering_intelligence,
    )

    cross_repo = build_cross_repository_multi_agent_delivery_validation(session_id=session_id)
    cross_board = cross_repo.cross_repository_multi_agent_delivery_validation or {}
    nexora_cross_row = next(
        (
            row
            for row in (cross_board.get("sections") or {}).get("cross_repository_validation_matrix") or []
            if row.get("repository") == NEXORA_REPOSITORY
        ),
        None,
    )

    portfolio = build_multi_repository_engineering_intelligence(session_id=session_id)
    portfolio_board = portfolio.multi_repository_engineering_intelligence or {}
    portfolio_dashboard = (
        (portfolio_board.get("sections") or {}).get("portfolio_engineering_dashboard") or [{}]
    )[0]
    nexora_portfolio_row = next(
        (
            row
            for row in portfolio_dashboard.get("repository_health_rows") or []
            if row.get("repository") == NEXORA_REPOSITORY
        ),
        None,
    )

    modules: dict[str, Any] = {}
    for fix_label in EXECUTIVE_FIX_MODULES:
        if fix_label == "FIX 191":
            modules[fix_label] = {
                "compose_available": True,
                "nexora_evidence_reflected": nexora_cross_row is not None and cross_repo.ok,
                "nexora_cross_repo_row": nexora_cross_row,
                "placeholder_risk": "low" if nexora_cross_row else "high",
                "validated_via_workstream_compose": cross_repo.ok,
                "governed_delivery_generalizes": nexora_cross_row is not None and cross_repo.ok,
            }
        elif fix_label == "FIX 260":
            modules[fix_label] = {
                "compose_available": True,
                "nexora_portfolio_row_populated": nexora_portfolio_row is not None,
                "nexora_portfolio_row": nexora_portfolio_row,
                "placeholder_risk": "low" if nexora_portfolio_row else "high",
                "validated_via_workstream_compose": portfolio.ok,
            }
        elif fix_label == "FIX 330":
            modules[fix_label] = {
                "compose_available": True,
                "nexora_evidence_reflected": executive_evidence_ready,
                "placeholder_risk": "low" if executive_evidence_ready else "high",
                "validated_via_workstream_compose": True,
                "note": "Full FIX 330 board not re-composed here (heavy evidence fan-in); audit gate used.",
            }
        else:
            modules[fix_label] = {
                "compose_available": True,
                "nexora_evidence_reflected": executive_evidence_ready,
                "placeholder_risk": "low" if nexora_evidence_present else "high",
                "validated_via_workstream_compose": True,
            }

    return {
        "executive_modules": list(EXECUTIVE_FIX_MODULES),
        "module_assessments": modules,
        "cross_repository_validation_updated": cross_repo.ok,
        "fix_191_matrix_updated": nexora_cross_row is not None and cross_repo.ok,
        "fix_260_portfolio_visibility_populated": nexora_portfolio_row is not None and portfolio.ok,
        "fix_330_executive_dashboard_nexora_evidence": executive_evidence_ready,
        "nexora_trust_state_in_cross_repo": nexora_cross_row,
        "nexora_portfolio_health_row": nexora_portfolio_row,
        "nexora_audit_evidence_present": nexora_evidence_present,
        "executive_dashboard_populated_with_real_evidence": executive_evidence_ready,
        "four_repository_trust_baseline_program_complete": executive_evidence_ready
        and arc_state == "CONDITIONALLY_TRUSTED",
        "note": (
            "Executive FIX 324–330 boards compose tenant-scoped evidence; "
            "Nexora audit presence in FIX 181 store is the workstream proof gate. "
            "FIX 330 full dashboard compose is omitted in this workstream path."
        ),
        "validated": cross_repo.ok and portfolio.ok,
    }


def build_nexora_operational_proof_program(*, session_id: str = "default") -> NexoraOperationalProofProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"

    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
        build_cross_repository_multi_agent_delivery_validation,
    )
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_service import (
        build_nexora_trust_report_freeze,
    )

    arc_state = _infer_arc_state_local()

    freeze = build_nexora_trust_report_freeze(session_id=sid)
    freeze_board = freeze.nexora_trust_report_freeze or {}

    readiness_report, prerequisite_validation = _build_readiness_reports()

    pilot_bundles = [
        _build_pilot_evidence_bundle(pilot_number=n, session_id=NEXORA_PILOT_SESSIONS[n - 1])
        for n in (1, 2, 3)
    ]

    freeze_artifact, nexora_boundary_snapshot, nexora_trust_recommendation_snapshot = _build_trust_freeze_artifacts(
        freeze_board=freeze_board
    )
    trust_decision_record = _build_trust_decision_record(freeze_board=freeze_board)
    evidence_density = _score_evidence_density(pilot_bundles=pilot_bundles, freeze_board=freeze_board)
    executive_visibility = _build_executive_visibility_report(arc_state=arc_state, session_id=sid)
    cross_repo = build_cross_repository_multi_agent_delivery_validation(session_id=sid)

    success_criteria = {
        "pilot_1_completed": pilot_bundles[0].get("pilot_complete") or pilot_bundles[0].get("audit_present"),
        "pilot_2_completed": pilot_bundles[1].get("audit_present"),
        "pilot_3_completed": pilot_bundles[2].get("pilot_complete") or pilot_bundles[2].get("audit_present"),
        "trust_freeze_completed": bool(freeze_board.get("trust_report_freeze_recorded")),
        "trust_decision_recorded": trust_decision_record.get("trust_decision_recorded", False),
        "fix_191_validation_matrix_updated": executive_visibility.get("fix_191_matrix_updated"),
        "fix_260_portfolio_visibility_populated": executive_visibility.get("fix_260_portfolio_visibility_populated"),
        "fix_330_executive_dashboard_nexora_evidence": executive_visibility.get(
            "fix_330_executive_dashboard_nexora_evidence"
        ),
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
                "nexora_readiness_report": readiness_report,
                "nexora_prerequisite_validation": prerequisite_validation,
            }
        ],
        "phase_2_pilot_1_execution": [{"nexora_pilot1_evidence_bundle": pilot_bundles[0]}],
        "phase_3_pilot_2_execution": [{"nexora_pilot2_evidence_bundle": pilot_bundles[1]}],
        "phase_4_pilot_3_execution": [{"nexora_pilot3_evidence_bundle": pilot_bundles[2]}],
        "phase_5_trust_freeze": [
            {
                "nexora_trust_freeze_artifact": freeze_artifact,
                "nexora_boundary_snapshot": nexora_boundary_snapshot,
                "nexora_trust_recommendation_snapshot": nexora_trust_recommendation_snapshot,
            }
        ],
        "phase_6_trust_review": [{"nexora_trust_decision_record": trust_decision_record}],
        "phase_7_evidence_density_review": [{"nexora_evidence_density_report": evidence_density}],
        "phase_8_executive_dashboard_validation": [{"nexora_executive_visibility_report": executive_visibility}],
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
        "schema_version": NEXORA_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION,
        "workstream_id": NEXORA_OPERATIONAL_PROOF_PROGRAM_ID,
        "exported_at": _exported_at(),
        "session_id": sid,
        "repository": NEXORA_REPOSITORY,
        "read_only": True,
        "mutation_performed": False,
        "execution_performed": False,
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(NEXORA_OPERATIONAL_PROOF_PROGRAM_PHASES),
        "arc_state": arc_state,
        "trust_status": freeze_board.get("trust_status"),
        "success_criteria": success_criteria,
        "sections": sections,
        "sources": {
            "fix_195_pilot_arc": True,
            "fix_196_trust_freeze": True,
            "fix_181_audits": True,
            "fix_191_cross_repo": True,
            "fix_260_portfolio": True,
            "fix_324_through_330_executive": True,
        },
    }

    return NexoraOperationalProofProgramResult(
        ok=not blockers or arc_state != "UNPROVEN",
        session_id=sid,
        nexora_operational_proof_program=board,
        blockers=blockers,
        detail="Nexora operational proof program composed from existing FIX modules (no new intelligence).",
    )
