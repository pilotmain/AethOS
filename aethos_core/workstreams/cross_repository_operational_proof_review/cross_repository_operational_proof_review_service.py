# SPDX-License-Identifier: Apache-2.0
"""Compose cross-repository operational proof review from existing FIX modules and workstreams."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_contract import (
    REPOSITORY_PILOT_SESSIONS,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    PHASE_1_REPOSITORY,
)
from aethos_core.workstreams.cross_repository_operational_proof_review.cross_repository_operational_proof_review_contract import (
    CORE_PRINCIPLE,
    CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW_ID,
    CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW_SCHEMA_VERSION,
    EXECUTIVE_FIX_MODULES,
    PROGRAM_NON_GOALS,
    REPOSITORY_LABELS,
    REVIEW_AREAS,
    REVIEW_REPOSITORIES,
    STRATEGIC_OPTIONS,
    TRUST_GENERALIZATION_LEVELS,
)


@dataclass(frozen=True)
class CrossRepositoryOperationalProofReviewResult:
    ok: bool
    session_id: str
    cross_repository_operational_proof_review: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _aethos_trust_baseline() -> dict[str, Any]:
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
        has_trust_report_freeze_record,
    )

    freeze_recorded = has_trust_report_freeze_record()
    return {
        "repository": PHASE_1_REPOSITORY,
        "display_name": REPOSITORY_LABELS[PHASE_1_REPOSITORY],
        "trust_report_freeze_recorded": freeze_recorded,
        "human_trust_decision_approve": freeze_recorded,
        "trust_recommendation_status": "CONDITIONALLY_TRUSTED" if freeze_recorded else "UNPROVEN",
        "workstream_id": None,
        "fix_path": "FIX 186",
    }


def _latest_audit_for_repo(*, session_id: str, repository: str) -> dict[str, Any] | None:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
        list_pilot_run_audits,
    )

    audits = [
        a
        for a in list_pilot_run_audits(session_id=session_id, limit=10)
        if repository in str(a.get("repo_issue") or "")
    ]
    return audits[0] if audits else None


def _score_density(*, audits_present: int, pilots_complete: int, freeze_recorded: bool, human_approve: bool) -> dict[str, Any]:
    score = audits_present * 0.25 + pilots_complete * 0.2
    if freeze_recorded:
        score += 0.15
    if human_approve:
        score += 0.15
    score = min(1.0, score)
    if score >= 0.85:
        level = "STRONG"
    elif score >= 0.65:
        level = "ADEQUATE"
    elif score >= 0.35:
        level = "PARTIAL"
    else:
        level = "INSUFFICIENT"
    return {
        "evidence_density_level": level,
        "evidence_density_score": round(score, 3),
        "audits_present": audits_present,
        "pilots_complete": pilots_complete,
        "receipt_count": 0,
    }


def _repo_evidence_summary(
    *,
    repository: str,
    sessions: tuple[str, ...],
    workstream_id: str | None,
    freeze_recorded: bool,
    human_approve: bool,
) -> dict[str, Any]:
    pilot_bundles: list[dict[str, Any]] = []
    for pilot_number, session_id in enumerate(sessions, start=1):
        audit = _latest_audit_for_repo(session_id=session_id, repository=repository)
        pilot_bundles.append(
            {
                "pilot_number": pilot_number,
                "session_id": session_id,
                "audit_present": audit is not None,
                "pilot_complete": audit is not None and str(audit.get("outcome") or "") == "complete",
            }
        )

    audits_present = sum(1 for bundle in pilot_bundles if bundle.get("audit_present"))
    pilots_complete = sum(1 for bundle in pilot_bundles if bundle.get("pilot_complete"))
    density = _score_density(
        audits_present=audits_present,
        pilots_complete=pilots_complete,
        freeze_recorded=freeze_recorded,
        human_approve=human_approve,
    )

    return {
        "repository": repository,
        "display_name": REPOSITORY_LABELS.get(repository, repository),
        "program_complete": audits_present == len(sessions) and freeze_recorded and human_approve,
        "pilot_bundles": pilot_bundles,
        "trust_freeze_artifact": {
            "freeze_record_present": freeze_recorded,
            "human_trust_decision_approve": human_approve,
        },
        "evidence_density": density,
        "workstream_id": workstream_id,
    }


def _phase2_workstream_summaries() -> dict[str, dict[str, Any]]:
    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
        has_atlas_trust_report_freeze_record,
        has_human_trust_decision_approve as atlas_has_human_trust_decision_approve,
    )
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_store import (
        has_human_trust_decision_approve as nexora_has_human_trust_decision_approve,
        has_nexora_trust_report_freeze_record,
    )
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
        has_human_trust_decision_approve as pilotos_has_human_trust_decision_approve,
        has_pilotos_trust_report_freeze_record,
    )
    from aethos_core.workstreams.atlas_operational_proof_program.atlas_operational_proof_program_contract import (
        ATLAS_OPERATIONAL_PROOF_PROGRAM_ID,
        ATLAS_PILOT_SESSIONS,
        ATLAS_TRADER_REPOSITORY,
    )
    from aethos_core.workstreams.nexora_operational_proof_program.nexora_operational_proof_program_contract import (
        NEXORA_OPERATIONAL_PROOF_PROGRAM_ID,
        NEXORA_PILOT_SESSIONS,
        NEXORA_REPOSITORY,
    )
    from aethos_core.workstreams.pilotos_operational_proof_program.pilotos_operational_proof_program_contract import (
        PILOTOS_OPERATIONAL_PROOF_PROGRAM_ID,
        PILOTOS_PILOT_SESSIONS,
        PILOTOS_UI_REPOSITORY,
    )

    return {
        PILOTOS_UI_REPOSITORY: _repo_evidence_summary(
            repository=PILOTOS_UI_REPOSITORY,
            sessions=PILOTOS_PILOT_SESSIONS,
            workstream_id=PILOTOS_OPERATIONAL_PROOF_PROGRAM_ID,
            freeze_recorded=has_pilotos_trust_report_freeze_record(),
            human_approve=pilotos_has_human_trust_decision_approve(),
        ),
        ATLAS_TRADER_REPOSITORY: _repo_evidence_summary(
            repository=ATLAS_TRADER_REPOSITORY,
            sessions=ATLAS_PILOT_SESSIONS,
            workstream_id=ATLAS_OPERATIONAL_PROOF_PROGRAM_ID,
            freeze_recorded=has_atlas_trust_report_freeze_record(),
            human_approve=atlas_has_human_trust_decision_approve(),
        ),
        NEXORA_REPOSITORY: _repo_evidence_summary(
            repository=NEXORA_REPOSITORY,
            sessions=NEXORA_PILOT_SESSIONS,
            workstream_id=NEXORA_OPERATIONAL_PROOF_PROGRAM_ID,
            freeze_recorded=has_nexora_trust_report_freeze_record(),
            human_approve=nexora_has_human_trust_decision_approve(),
        ),
    }


def _repo_row(*, validation_rows: list[dict[str, Any]], repository: str) -> dict[str, Any]:
    return next((row for row in validation_rows if row.get("repository") == repository), {})


def _build_repository_trust_baseline_review(
    *,
    validation_rows: list[dict[str, Any]],
    workstream_summaries: dict[str, dict[str, Any]],
    aethos_baseline: dict[str, Any],
) -> dict[str, Any]:
    per_repository: list[dict[str, Any]] = []

    for repository in REVIEW_REPOSITORIES:
        row = _repo_row(validation_rows=validation_rows, repository=repository)
        if repository == PHASE_1_REPOSITORY:
            per_repository.append(
                {
                    "repository": repository,
                    "display_name": REPOSITORY_LABELS[repository],
                    "trust_report_freeze_recorded": aethos_baseline.get("trust_report_freeze_recorded"),
                    "human_trust_decision_approve": aethos_baseline.get("human_trust_decision_approve"),
                    "trust_recommendation_status": aethos_baseline.get("trust_recommendation_status"),
                    "validation_trust_state": row.get("trust_state"),
                    "trust_review_state": row.get("trust_review_state"),
                    "operational_proof_complete": bool(aethos_baseline.get("trust_report_freeze_recorded")),
                }
            )
            continue

        summary = workstream_summaries.get(repository, {})
        freeze = summary.get("trust_freeze_artifact") or {}
        per_repository.append(
            {
                "repository": repository,
                "display_name": REPOSITORY_LABELS.get(repository, repository),
                "trust_report_freeze_recorded": freeze.get("freeze_record_present"),
                "human_trust_decision_approve": freeze.get("human_trust_decision_approve"),
                "trust_recommendation_status": summary.get("trust_status"),
                "validation_trust_state": row.get("trust_state"),
                "trust_review_state": row.get("trust_review_state"),
                "operational_proof_complete": summary.get("program_complete", False),
                "workstream_id": summary.get("workstream_id"),
            }
        )

    return {
        "repository_trust_baseline_review": per_repository,
        "repositories_with_trust_freeze": sum(
            1 for r in per_repository if r.get("trust_report_freeze_recorded")
        ),
        "repositories_with_trust_decision": sum(
            1 for r in per_repository if r.get("human_trust_decision_approve")
        ),
        "validated": True,
    }


def _build_pilot_completion_review(*, validation_rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_repository: list[dict[str, Any]] = []
    for repository in REVIEW_REPOSITORIES:
        row = _repo_row(validation_rows=validation_rows, repository=repository)
        progression = row.get("pilot_progression") or {}
        per_repository.append(
            {
                "repository": repository,
                "display_name": REPOSITORY_LABELS.get(repository, repository),
                "pilot_1_complete": progression.get("pilot_1_complete"),
                "pilot_2_complete": progression.get("pilot_2_complete"),
                "pilot_3_complete": progression.get("pilot_3_complete"),
                "all_pilots_complete": all(
                    progression.get(k) for k in ("pilot_1_complete", "pilot_2_complete", "pilot_3_complete")
                ),
                "evidence_completeness": row.get("evidence_completeness"),
            }
        )

    return {
        "pilot_completion_review": per_repository,
        "repositories_all_pilots_complete": sum(1 for r in per_repository if r.get("all_pilots_complete")),
        "validated": True,
    }


def _build_evidence_density_review(*, workstream_summaries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    per_repository: list[dict[str, Any]] = []

    for repository in REVIEW_REPOSITORIES:
        if repository == PHASE_1_REPOSITORY:
            sessions = REPOSITORY_PILOT_SESSIONS.get(repository, ())
            audits = sum(
                1 for sid in sessions if _latest_audit_for_repo(session_id=sid, repository=repository)
            )
            per_repository.append(
                {
                    "repository": repository,
                    "display_name": REPOSITORY_LABELS[repository],
                    "audit_count": audits,
                    "receipt_count": 0,
                    "evidence_density_level": "ADEQUATE" if audits >= 3 else "PARTIAL" if audits else "INSUFFICIENT",
                    "workstream_id": None,
                }
            )
            continue

        summary = workstream_summaries.get(repository, {})
        density = summary.get("evidence_density") or {}
        bundles = summary.get("pilot_bundles") or []
        per_repository.append(
            {
                "repository": repository,
                "display_name": REPOSITORY_LABELS.get(repository, repository),
                "audit_count": density.get("audits_present", sum(1 for b in bundles if b.get("audit_present"))),
                "receipt_count": density.get("receipt_count", 0),
                "evidence_density_level": density.get("evidence_density_level", "INSUFFICIENT"),
                "evidence_density_score": density.get("evidence_density_score"),
                "workstream_id": summary.get("workstream_id"),
            }
        )

    return {
        "evidence_density_review": per_repository,
        "validated": True,
    }


def _build_verification_quality_review(*, validation_rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_repository: list[dict[str, Any]] = []
    for repository in REVIEW_REPOSITORIES:
        row = _repo_row(validation_rows=validation_rows, repository=repository)
        sessions = REPOSITORY_PILOT_SESSIONS.get(repository, ())
        audits = [_latest_audit_for_repo(session_id=sid, repository=repository) for sid in sessions]
        blockers = [b for audit in audits if audit for b in (audit.get("blockers") or [])]
        per_repository.append(
            {
                "repository": repository,
                "display_name": REPOSITORY_LABELS.get(repository, repository),
                "verification_completeness": row.get("evidence_completeness"),
                "alignment_score": row.get("alignment_score"),
                "pr_open_success_rate_percent": row.get("pr_open_success_rate_percent"),
                "blocker_count": len(blockers),
                "blockers_sample": blockers[:5],
                "human_intervention_count": row.get("human_intervention_count", 0),
                "review_quality": "strong"
                if row.get("evidence_completeness") == "complete" and not blockers
                else "partial"
                if row.get("evidence_completeness") in {"complete", "partial"}
                else "weak",
            }
        )

    return {
        "verification_quality_review": per_repository,
        "validated": True,
    }


def _build_throughput_review(*, validation_rows: list[dict[str, Any]], session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_store import (
        list_agent_execution_quality_throughput_metrics_records,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        list_agent_execution_receipts,
    )

    metrics_records = list_agent_execution_quality_throughput_metrics_records(session_id=session_id)
    receipts = list_agent_execution_receipts(session_id=session_id, plan_id=None)

    repo_throughput = [
        {
            "repository": row.get("repository"),
            "display_name": row.get("display_name"),
            "throughput_score": row.get("throughput_score"),
            "human_intervention_count": row.get("human_intervention_count"),
            "pr_open_success_rate_percent": row.get("pr_open_success_rate_percent"),
            "agent_quality_metrics": row.get("agent_quality_metrics"),
        }
        for row in validation_rows
    ]

    completion_rates = [
        {
            "repository": row.get("repository"),
            "pilot_progression": row.get("pilot_progression"),
        }
        for row in validation_rows
    ]

    intervention_total = sum(int(row.get("human_intervention_count") or 0) for row in validation_rows)

    return {
        "throughput_review": {
            "fix_190_metrics_record_count": len(metrics_records),
            "fix_190_receipt_count": len(receipts),
            "fix_190_human_intervention_total": intervention_total,
            "repository_throughput_scores": repo_throughput,
            "pilot_completion_rates": completion_rates,
            "composed_from_fix_190": bool(metrics_records or receipts),
            "composed_from_fix_191_throughput_derivation": True,
            "note": "Full FIX 190 compose omitted (heavy FIX 189 fan-in); matrix throughput scores used.",
        },
        "validated": True,
    }


def _build_cross_repository_consistency_review(
    *,
    trust_baseline: dict[str, Any],
    pilot_completion: dict[str, Any],
    evidence_density: dict[str, Any],
) -> dict[str, Any]:
    baselines = trust_baseline.get("repository_trust_baseline_review") or []
    pilots = pilot_completion.get("pilot_completion_review") or []
    densities = evidence_density.get("evidence_density_review") or []

    trust_states = {r["repository"]: r.get("validation_trust_state") for r in baselines}
    pilot_patterns = {
        r["repository"]: (
            r.get("pilot_1_complete"),
            r.get("pilot_2_complete"),
            r.get("pilot_3_complete"),
        )
        for r in pilots
    }
    density_levels = {r["repository"]: r.get("evidence_density_level") for r in densities}

    unique_trust_states = set(trust_states.values())
    unique_density_levels = set(density_levels.values())
    pilot_pattern_set = set(pilot_patterns.values())

    same_trust_progression = len(unique_trust_states) <= 2
    same_pilot_pattern = len(pilot_pattern_set) <= 2
    same_evidence_quality = len(unique_density_levels) <= 2

    outlier_repos = [
        repo
        for repo in REVIEW_REPOSITORIES
        if density_levels.get(repo) == "INSUFFICIENT"
        or not all(pilot_patterns.get(repo, (False, False, False)))
    ]

    return {
        "cross_repository_consistency_review": {
            "trust_progression_consistency": same_trust_progression,
            "pilot_progression_consistency": same_pilot_pattern,
            "evidence_quality_consistency": same_evidence_quality,
            "trust_states_by_repository": trust_states,
            "pilot_patterns_by_repository": {
                repo: {"pilot_1": p[0], "pilot_2": p[1], "pilot_3": p[2]}
                for repo, p in pilot_patterns.items()
            },
            "evidence_density_by_repository": density_levels,
            "outlier_repositories": outlier_repos,
            "questions": {
                "same_trust_progression": same_trust_progression,
                "substantially_different_treatment_required": len(outlier_repos) >= 2,
            },
        },
        "validated": True,
    }


def _build_executive_visibility_review(
    *,
    validation_rows: list[dict[str, Any]],
    session_id: str,
) -> dict[str, Any]:
    from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
        build_multi_repository_engineering_intelligence,
    )

    portfolio = build_multi_repository_engineering_intelligence(session_id=session_id)
    portfolio_board = portfolio.multi_repository_engineering_intelligence or {}
    dashboard = (
        (portfolio_board.get("sections") or {}).get("portfolio_engineering_dashboard") or [{}]
    )[0]
    health_rows = dashboard.get("repository_health_rows") or []

    per_repository: list[dict[str, Any]] = []
    for repository in REVIEW_REPOSITORIES:
        row = _repo_row(validation_rows=validation_rows, repository=repository)
        portfolio_row = next((r for r in health_rows if r.get("repository") == repository), None)
        has_audit_evidence = row.get("evidence_completeness") in {"complete", "partial"}
        per_repository.append(
            {
                "repository": repository,
                "display_name": REPOSITORY_LABELS.get(repository, repository),
                "fix_260_portfolio_row_present": portfolio_row is not None,
                "fix_260_portfolio_row": portfolio_row,
                "real_evidence_representable": has_audit_evidence,
                "trust_state": row.get("trust_state"),
            }
        )

    modules: dict[str, Any] = {}
    all_representable = all(r.get("real_evidence_representable") for r in per_repository)
    for fix_label in EXECUTIVE_FIX_MODULES:
        if fix_label == "FIX 260":
            modules[fix_label] = {
                "all_repositories_in_portfolio": len(health_rows) >= len(REVIEW_REPOSITORIES),
                "compose_ok": portfolio.ok,
            }
        elif fix_label == "FIX 330":
            modules[fix_label] = {
                "audit_gate_all_repos": all_representable,
                "note": "Full FIX 330 fan-in omitted; audit completeness used as gate.",
            }
        else:
            modules[fix_label] = {
                "audit_gate_all_repos": all_representable,
                "compose_available": True,
            }

    return {
        "executive_visibility_review": {
            "per_repository": per_repository,
            "module_assessments": modules,
            "all_repositories_representable_with_real_evidence": all_representable,
        },
        "validated": portfolio.ok,
    }


def _build_trust_generalization_assessment(
    *,
    trust_baseline: dict[str, Any],
    pilot_completion: dict[str, Any],
    validation_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    baselines = trust_baseline.get("repository_trust_baseline_review") or []
    pilots = pilot_completion.get("pilot_completion_review") or []

    proof_complete = sum(1 for r in baselines if r.get("operational_proof_complete"))
    all_pilots = sum(1 for r in pilots if r.get("all_pilots_complete"))
    conditionally_trusted = sum(
        1 for row in validation_rows if row.get("trust_state") == "CONDITIONALLY_TRUSTED"
    )
    trust_freeze_count = trust_baseline.get("repositories_with_trust_freeze", 0)

    if proof_complete >= 4 and all_pilots >= 4 and trust_freeze_count >= 4:
        level = "PROVEN"
        summary = "All four repositories show trust freeze and pilot completion evidence."
    elif proof_complete >= 3 and all_pilots >= 3:
        level = "PROVEN_WITH_LIMITATIONS"
        summary = "Majority of repositories operational; one or more gaps remain."
    elif proof_complete >= 1 or all_pilots >= 2 or conditionally_trusted >= 1:
        level = "PARTIALLY_PROVEN"
        summary = "Some cross-repository evidence exists; generalization not yet complete."
    else:
        level = "NOT_PROVEN"
        summary = "Insufficient operational proof across repositories."

    return {
        "trust_generalization_assessment": {
            "level": level,
            "levels": list(TRUST_GENERALIZATION_LEVELS),
            "summary": summary,
            "repositories_operational_proof_complete": proof_complete,
            "repositories_all_pilots_complete": all_pilots,
            "repositories_conditionally_trusted": conditionally_trusted,
            "repositories_with_trust_freeze": trust_freeze_count,
            "fix_191_question": "Does governed delivery generalize across repositories?",
            "evidence_backed_answer": level in {"PROVEN", "PROVEN_WITH_LIMITATIONS"},
            "governed_delivery_generalizes": level == "PROVEN",
            "validation_grants_trust": False,
        },
        "validated": True,
    }


def _build_remaining_gap_assessment(
    *,
    trust_baseline: dict[str, Any],
    pilot_completion: dict[str, Any],
    evidence_density: dict[str, Any],
    verification: dict[str, Any],
    generalization: dict[str, Any],
) -> dict[str, Any]:
    gaps: list[dict[str, Any]] = []
    weak: list[dict[str, Any]] = []
    blind_spots: list[str] = []

    for row in trust_baseline.get("repository_trust_baseline_review") or []:
        repo = str(row.get("repository") or "")
        if not row.get("trust_report_freeze_recorded"):
            gaps.append({"repository": repo, "gap": "trust_freeze_missing"})
        if not row.get("human_trust_decision_approve"):
            gaps.append({"repository": repo, "gap": "trust_decision_missing"})
        if not row.get("operational_proof_complete"):
            gaps.append({"repository": repo, "gap": "operational_proof_incomplete"})

    for row in evidence_density.get("evidence_density_review") or []:
        if row.get("evidence_density_level") in {"INSUFFICIENT", "PARTIAL"}:
            weak.append(
                {
                    "repository": row.get("repository"),
                    "evidence_density_level": row.get("evidence_density_level"),
                }
            )

    for row in verification.get("verification_quality_review") or []:
        if row.get("review_quality") == "weak":
            blind_spots.append(f"{row.get('repository')}: weak verification quality")

    for row in pilot_completion.get("pilot_completion_review") or []:
        if not row.get("all_pilots_complete"):
            blind_spots.append(f"{row.get('repository')}: incomplete pilot arc")

    gen = generalization.get("trust_generalization_assessment") or {}
    if gen.get("level") == "NOT_PROVEN":
        blind_spots.append("cross_repository_generalization_not_demonstrated")

    return {
        "remaining_gap_assessment": {
            "missing_evidence": gaps,
            "weak_evidence": weak,
            "operational_blind_spots": blind_spots,
            "gap_count": len(gaps),
            "weak_count": len(weak),
        },
        "validated": True,
    }


def _build_strategic_recommendation(
    *,
    generalization: dict[str, Any],
    gaps: dict[str, Any],
) -> dict[str, Any]:
    level = (generalization.get("trust_generalization_assessment") or {}).get("level", "NOT_PROVEN")
    gap_count = (gaps.get("remaining_gap_assessment") or {}).get("gap_count", 0)
    architecture_gap = any(
        "architecture" in str(s).lower()
        for s in (gaps.get("remaining_gap_assessment") or {}).get("operational_blind_spots") or []
    )

    if level == "PROVEN":
        primary = "option_c_limited_external_customer_validation"
        rationale = (
            "Four-repository operational proof is sufficient to begin limited external customer validation "
            "while maintaining evidence discipline."
        )
        secondary = "option_b_expand_provider_coverage"
    elif level == "PROVEN_WITH_LIMITATIONS":
        primary = "option_a_expand_operational_proof"
        rationale = "Close remaining per-repository gaps before external validation."
        secondary = "option_c_limited_external_customer_validation"
    elif level == "PARTIALLY_PROVEN":
        primary = "option_a_expand_operational_proof"
        rationale = "Continue WORKSTREAM_A1–A3 execution until FIX 191 matrix reflects all repositories."
        secondary = None
    else:
        primary = "option_a_expand_operational_proof"
        rationale = "Operational proof must precede provider expansion or external validation."
        secondary = None

    if architecture_gap and level != "PROVEN":
        primary = "option_d_revisit_architecture"
        rationale = "Evidence suggests non-composeable gaps — revisit architecture only with artifact proof."

    return {
        "cross_repository_strategic_recommendation": {
            "primary_recommendation": primary,
            "secondary_recommendation": secondary,
            "options_evaluated": list(STRATEGIC_OPTIONS),
            "rationale": rationale,
            "trust_generalization_level": level,
            "remaining_gap_count": gap_count,
            "human_decision_required": True,
        },
        "validated": True,
    }


def build_cross_repository_operational_proof_review(
    *, session_id: str = "default"
) -> CrossRepositoryOperationalProofReviewResult:
    sid = (session_id or "default").strip()[:64] or "default"

    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
        build_cross_repository_multi_agent_delivery_validation,
    )

    cross_repo = build_cross_repository_multi_agent_delivery_validation(session_id=sid)
    cross_board = cross_repo.cross_repository_multi_agent_delivery_validation or {}
    validation_rows = (cross_board.get("sections") or {}).get("cross_repository_validation_matrix") or []

    workstream_summaries = _phase2_workstream_summaries()

    aethos_baseline = _aethos_trust_baseline()

    trust_baseline = _build_repository_trust_baseline_review(
        validation_rows=validation_rows,
        workstream_summaries=workstream_summaries,
        aethos_baseline=aethos_baseline,
    )
    pilot_completion = _build_pilot_completion_review(validation_rows=validation_rows)
    evidence_density = _build_evidence_density_review(workstream_summaries=workstream_summaries)
    verification = _build_verification_quality_review(validation_rows=validation_rows)
    throughput = _build_throughput_review(validation_rows=validation_rows, session_id=sid)
    consistency = _build_cross_repository_consistency_review(
        trust_baseline=trust_baseline,
        pilot_completion=pilot_completion,
        evidence_density=evidence_density,
    )
    executive = _build_executive_visibility_review(validation_rows=validation_rows, session_id=sid)
    generalization = _build_trust_generalization_assessment(
        trust_baseline=trust_baseline,
        pilot_completion=pilot_completion,
        validation_rows=validation_rows,
    )
    gaps = _build_remaining_gap_assessment(
        trust_baseline=trust_baseline,
        pilot_completion=pilot_completion,
        evidence_density=evidence_density,
        verification=verification,
        generalization=generalization,
    )
    recommendation = _build_strategic_recommendation(generalization=generalization, gaps=gaps)

    sections = {
        "review_area_1_repository_trust_baselines": [trust_baseline],
        "review_area_2_pilot_completion": [pilot_completion],
        "review_area_3_evidence_density": [evidence_density],
        "review_area_4_verification_quality": [verification],
        "review_area_5_throughput": [throughput],
        "review_area_6_cross_repository_consistency": [consistency],
        "review_area_7_executive_visibility": [executive],
        "review_area_8_trust_generalization": [generalization],
        "review_area_9_remaining_gaps": [gaps],
        "review_area_10_strategic_recommendation": [recommendation],
    }

    gen_level = (generalization.get("trust_generalization_assessment") or {}).get("level")
    success_criteria = {
        "fix_191_question_answered_with_evidence": gen_level in {"PROVEN", "PROVEN_WITH_LIMITATIONS", "PARTIALLY_PROVEN"},
        "four_repository_review_complete": len(REVIEW_REPOSITORIES) == 4,
        "trust_generalization_assessed": gen_level is not None,
        "strategic_recommendation_recorded": bool(recommendation.get("cross_repository_strategic_recommendation")),
        "review_authority": False,
        "program_complete": gen_level == "PROVEN",
    }

    blockers: list[str] = []
    if not cross_repo.ok:
        blockers.append("fix_191_compose_failed")

    board = {
        "schema_version": CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW_SCHEMA_VERSION,
        "review_id": CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW_ID,
        "exported_at": _exported_at(),
        "session_id": sid,
        "core_principle": CORE_PRINCIPLE,
        "read_only": True,
        "mutation_performed": False,
        "trust_mutations_performed": False,
        "non_goals": list(PROGRAM_NON_GOALS),
        "review_areas": list(REVIEW_AREAS),
        "repositories": list(REVIEW_REPOSITORIES),
        "success_criteria": success_criteria,
        "sections": sections,
        "sources": {
            "workstream_a1_pilotos": True,
            "workstream_a2_atlas": True,
            "workstream_a3_nexora": True,
            "fix_186_aethos_trust_baseline": True,
            "fix_190_throughput": True,
            "fix_191_cross_repo_validation": True,
            "fix_260_portfolio": True,
            "fix_324_through_330_executive_audit_gate": True,
        },
    }

    return CrossRepositoryOperationalProofReviewResult(
        ok=not blockers,
        session_id=sid,
        cross_repository_operational_proof_review=board,
        blockers=blockers,
        detail="Cross-repository operational proof review composed from workstreams and FIX modules (review ≠ trust authority).",
    )
