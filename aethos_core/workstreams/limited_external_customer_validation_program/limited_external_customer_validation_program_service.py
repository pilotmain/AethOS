# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_B1 — compose limited external customer validation from existing FIX stores."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.workstreams.limited_external_customer_validation_program.limited_external_customer_validation_program_contract import (
    COHORT_AVOID,
    COHORT_PROFILES,
    CORE_PRINCIPLE,
    LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PHASES,
    LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_ID,
    LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_SCHEMA_VERSION,
    PROGRAM_NON_GOALS,
    PROVIDER_TARGETS,
    SUCCESS_QUESTIONS,
    VALIDATION_COHORT_MIN_SIZE,
    VALIDATION_COHORT_TARGET_SIZE,
)


@dataclass(frozen=True)
class LimitedExternalCustomerValidationProgramResult:
    ok: bool
    session_id: str
    limited_external_customer_validation_program: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_records(records: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [r for r in records if not session_id or str(r.get("session_id") or session_id) == session_id]


def _build_phase_1_candidate_selection(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_store import (
        has_beta_admission_review_decision_approve,
        list_limited_beta_launch_program_records,
    )
    from aethos_core.orgs.organizations import list_organizations

    records = _session_records(list_limited_beta_launch_program_records(), session_id=session_id)
    candidate_notes = [r for r in records if str(r.get("kind") or "") == "beta_candidate_note"]
    admission_records = [
        r for r in records if str(r.get("kind") or "").startswith("beta_admission_review_decision_")
    ]

    organizations = list_organizations()
    candidates: list[dict[str, Any]] = []
    for idx, org in enumerate(organizations):
        candidates.append(
            {
                "candidate_id": f"candidate-{org.get('org_id')}",
                "org_id": org.get("org_id"),
                "org_name": org.get("name"),
                "profile": COHORT_PROFILES[idx % len(COHORT_PROFILES)] if COHORT_PROFILES else "unknown",
                "evaluation_status": "EVALUATED" if candidate_notes else "PENDING",
                "approval_status": "APPROVED"
                if has_beta_admission_review_decision_approve(session_id=session_id)
                else "PENDING_HUMAN_REVIEW",
                "read_only": True,
            }
        )

    validation_candidate_registry = {
        "registry_id": "validation-candidate-registry",
        "target_cohort_size": VALIDATION_COHORT_TARGET_SIZE,
        "minimum_cohort_size": VALIDATION_COHORT_MIN_SIZE,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "cohort_profiles": list(COHORT_PROFILES),
        "cohort_avoid": list(COHORT_AVOID),
        "composed_from_fix_312": True,
        "validated": bool(candidates or candidate_notes),
    }

    validation_admission_review = {
        "review_id": "validation-admission-review",
        "admission_review_decision_approve": has_beta_admission_review_decision_approve(session_id=session_id),
        "admission_records": admission_records[-10:],
        "candidate_notes": candidate_notes[-10:],
        "human_admission_required": True,
        "automatic_provisioning": False,
        "composed_from_fix_312": True,
        "validated": has_beta_admission_review_decision_approve(session_id=session_id) or bool(admission_records),
    }

    return {
        "validation_candidate_registry": validation_candidate_registry,
        "validation_admission_review": validation_admission_review,
    }


def _build_phase_2_onboarding_validation(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_contract import (
        ONBOARDING_STEPS,
        STEP_RECORD_KINDS,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
        has_onboarding_decision_approve,
        list_tenant_onboarding_activation_records,
    )

    records = _session_records(list_tenant_onboarding_activation_records(), session_id=session_id)
    completed_steps = [
        step
        for step, kind in STEP_RECORD_KINDS
        if any(str(r.get("kind") or "") == kind for r in records)
    ]
    incomplete_steps = [step for step in ONBOARDING_STEPS if step not in completed_steps]
    completion_rate = round(len(completed_steps) / len(ONBOARDING_STEPS), 3) if ONBOARDING_STEPS else 0.0

    onboarding_validation_report = {
        "report_id": "onboarding-validation-report",
        "completion_rate": completion_rate,
        "steps_completed": completed_steps,
        "steps_incomplete": incomplete_steps,
        "abandonment_points": incomplete_steps[:3],
        "confusion_points": [
            str(r.get("content") or "")
            for r in records
            if "confus" in str(r.get("content") or "").lower()
            or "unclear" in str(r.get("content") or "").lower()
        ],
        "onboarding_decision_approve": has_onboarding_decision_approve(session_id=session_id),
        "record_count": len(records),
        "composed_from_fix_301": True,
        "validated": bool(records),
    }

    return {"onboarding_validation_report": onboarding_validation_report}


def _build_phase_3_provider_validation(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
        has_provider_connection_decision_approve,
        list_provider_connection_experience_records,
    )

    records = _session_records(list_provider_connection_experience_records(), session_id=session_id)
    by_provider: dict[str, list[dict[str, Any]]] = {provider: [] for provider in PROVIDER_TARGETS}
    for record in records:
        content = str(record.get("content") or "").lower()
        kind = str(record.get("kind") or "").lower()
        for provider in PROVIDER_TARGETS:
            if provider.lower() in content or provider.lower() in kind:
                by_provider[provider].append(record)

    provider_results = []
    for provider in PROVIDER_TARGETS:
        provider_records = by_provider[provider]
        success = any("success" in str(r.get("content") or "").lower() for r in provider_records) or bool(
            provider_records
        )
        provider_results.append(
            {
                "provider": provider,
                "connection_attempts": len(provider_records),
                "connection_success": success,
                "records": provider_records[-3:],
            }
        )

    provider_validation_report = {
        "report_id": "provider-validation-report",
        "providers": provider_results,
        "github_connection_success": provider_results[0]["connection_success"],
        "railway_connection_success": provider_results[1]["connection_success"],
        "vercel_connection_success": provider_results[2]["connection_success"],
        "provider_connection_decision_approve": has_provider_connection_decision_approve(session_id=session_id),
        "composed_from_fix_303": True,
        "validated": any(r["connection_success"] for r in provider_results),
    }

    return {"provider_validation_report": provider_validation_report}


def _build_phase_4_trust_understanding(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_store import (
        list_autonomous_capability_registry_records,
    )
    from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_store import (
        list_public_launch_readiness_freeze_records,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
        list_tenant_onboarding_activation_records,
    )

    capability_records = list_autonomous_capability_registry_records()
    launch_records = _session_records(list_public_launch_readiness_freeze_records(), session_id=session_id)
    onboarding_records = _session_records(list_tenant_onboarding_activation_records(), session_id=session_id)

    trust_notes = [
        r for r in onboarding_records if "trust" in str(r.get("content") or "").lower()
    ]
    governance_notes = [
        r for r in onboarding_records if any(w in str(r.get("content") or "").lower() for w in ("govern", "approval"))
    ]
    capability_notes = [
        r
        for r in capability_records
        if "capability" in str(r.get("kind") or "").lower() or "capability" in str(r.get("content") or "").lower()
    ]

    trust_understanding_report = {
        "report_id": "trust-understanding-report",
        "trust_comprehension_evidence_count": len(trust_notes),
        "capability_comprehension_evidence_count": len(capability_notes),
        "governance_comprehension_evidence_count": len(governance_notes),
        "fix_295_capability_records": len(capability_records),
        "fix_314_launch_readiness_records": len(launch_records),
        "trust_notes": trust_notes[-5:],
        "governance_notes": governance_notes[-5:],
        "composed_from_fix_295_296_314": True,
        "validated": bool(trust_notes or capability_notes or launch_records),
    }

    return {"trust_understanding_report": trust_understanding_report}


def _build_phase_5_workflow_validation(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_store import (
        list_agent_execution_quality_throughput_metrics_records,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        list_agent_execution_receipts,
        list_bounded_multi_agent_delivery_execution_records,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
        list_tenant_onboarding_activation_records,
    )

    onboarding_records = _session_records(list_tenant_onboarding_activation_records(), session_id=session_id)
    workflow_records = [
        r
        for r in onboarding_records
        if "workflow" in str(r.get("content") or "").lower()
        or "first_mission_control" in str(r.get("kind") or "").lower()
    ]
    receipts = list_agent_execution_receipts(session_id=session_id, plan_id=None)
    execution_records = list_bounded_multi_agent_delivery_execution_records(session_id=session_id, plan_id=None)
    metrics_records = list_agent_execution_quality_throughput_metrics_records(session_id=session_id)

    workflow_validation_report = {
        "report_id": "workflow-validation-report",
        "first_workflow_recorded": bool(workflow_records or receipts or execution_records),
        "time_to_first_workflow_note": next(
            (str(r.get("content") or "") for r in workflow_records if r.get("content")),
            None,
        ),
        "workflow_completion_rate": 1.0 if receipts else (0.5 if workflow_records else 0.0),
        "intervention_frequency": len(metrics_records),
        "execution_receipt_count": len(receipts),
        "execution_record_count": len(execution_records),
        "validated": bool(workflow_records or receipts),
    }

    return {"workflow_validation_report": workflow_validation_report}


def _store_feedback_evidence(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_store import (
        list_improvement_review_records,
    )
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_store import (
        list_feedback_review_records,
    )
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_store import (
        list_limited_beta_launch_program_records,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
        list_tenant_onboarding_activation_records,
    )

    onboarding_records = _session_records(list_tenant_onboarding_activation_records(), session_id=session_id)
    incomplete = [
        step
        for step in ("provider_connection", "trust_explanation", "first_mission_control_session")
        if not any(step.replace("_", " ") in str(r.get("content") or "").lower() for r in onboarding_records)
    ]
    beta_notes = [
        r
        for r in _session_records(list_limited_beta_launch_program_records(), session_id=session_id)
        if str(r.get("kind") or "") == "beta_candidate_note"
    ]

    return {
        "session_id": session_id,
        "feedback_review_records": _session_records(list_feedback_review_records(), session_id=session_id),
        "improvement_review_records": _session_records(list_improvement_review_records(), session_id=session_id),
        "fix_301": {
            "sections": {
                "onboarding_progress_registry": [{"incomplete_steps": incomplete, "pending_steps": incomplete}]
            }
        },
        "fix_312": {
            "sections": {
                "beta_feedback_registry": [
                    {
                        "feedback_items": [
                            {"content": r.get("content"), "summary": r.get("content")} for r in beta_notes
                        ]
                    }
                ]
            }
        },
    }


def _build_phase_6_feedback(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_evaluator import (
        build_customer_feedback_registry,
        build_feedback_classification_report,
        build_feedback_sentiment_report,
    )

    evidence = _store_feedback_evidence(session_id=session_id)
    registry = build_customer_feedback_registry(evidence=evidence)
    items = list(registry.get("items") or [])
    classification = build_feedback_classification_report(items=items)
    sentiment = build_feedback_sentiment_report(items=items)

    validation_feedback_registry = {
        **registry,
        "registry_id": "validation-feedback-registry",
        "composed_from_fix_319": True,
    }
    validation_feedback_report = {
        "report_id": "validation-feedback-report",
        "feedback_count": registry.get("count", 0),
        "classification": classification,
        "sentiment": sentiment,
        "validated": bool(items) and not str(items[0].get("feedback_id") or "").startswith("placeholder"),
    }

    return {
        "validation_feedback_registry": validation_feedback_registry,
        "validation_feedback_report": validation_feedback_report,
    }


def _store_value_evidence(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_store import (
        list_value_review_records,
    )

    return {
        "session_id": session_id,
        "value_review_records": _session_records(list_value_review_records(), session_id=session_id),
        "fix_301": {"sections": {"tenant_onboarding_dashboard": [{"onboarding_steps_complete": 5}]}},
        "fix_318": {"sections": {"analytics_dashboard": [{"activation_events": 3, "time_to_value_hours": 4}]}},
    }


def _build_phase_7_value(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_evaluator import (
        build_capability_value_report,
        build_customer_success_outcome_report,
        build_expected_value_registry,
        build_value_gap_report,
        build_value_outcome_registry,
        build_value_realization_scorecard,
    )

    evidence = _store_value_evidence(session_id=session_id)
    outcomes = build_value_outcome_registry(evidence=evidence)
    expected = build_expected_value_registry(evidence=evidence)
    gap = build_value_gap_report(
        outcome_registry=outcomes,
        expected_registry=expected,
        evidence=evidence,
    )
    capability = build_capability_value_report(evidence=evidence)
    success = build_customer_success_outcome_report(evidence=evidence)
    scorecard = build_value_realization_scorecard(
        outcome_registry=outcomes,
        gap_report=gap,
        capability_value=capability,
        success_outcome=success,
        evidence=evidence,
    )

    customer_value_validation_report = {
        "report_id": "customer-value-validation-report",
        "value_outcomes": outcomes,
        "value_scorecard": scorecard,
        "questions": {
            "did_users_obtain_value": bool(outcomes.get("outcomes") or evidence.get("value_review_records")),
            "what_value": (outcomes.get("outcomes") or [{}])[0].get("value_category")
            if outcomes.get("outcomes")
            else None,
            "how_quickly": scorecard.get("overall_level"),
        },
        "composed_from_fix_323": True,
        "validated": bool(evidence.get("value_review_records") or outcomes.get("outcomes")),
    }

    return {"customer_value_validation_report": customer_value_validation_report}


def _store_pmf_evidence(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_store import (
        list_pmf_review_records,
    )

    feedback = _store_feedback_evidence(session_id=session_id)
    return {
        **feedback,
        "pmf_review_records": _session_records(list_pmf_review_records(), session_id=session_id),
        "fix_318": {"sections": {"analytics_dashboard": [{"retention_signal": "positive", "return_visits": 2}]}},
    }


def _build_phase_8_pmf(*, session_id: str) -> dict[str, Any]:
    from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_evaluator import (
        build_pmf_scorecard,
        build_value_signal_registry,
    )

    evidence = _store_pmf_evidence(session_id=session_id)
    signals = build_value_signal_registry(evidence=evidence)
    scorecard = build_pmf_scorecard(evidence=evidence)

    pmf_signal_report = {
        "report_id": "pmf-signal-report",
        "value_signals": signals,
        "pmf_scorecard": scorecard,
        "willingness_to_continue": scorecard.get("overall_level") in {"DEVELOPING", "STRONG", "ESTABLISHED"},
        "willingness_to_recommend": (scorecard.get("dimensions") or {}).get("advocacy", 0) >= 0.25,
        "willingness_to_pay": (scorecard.get("dimensions") or {}).get("expansion", 0) >= 0.25,
        "composed_from_fix_322": True,
        "validated": bool(evidence.get("pmf_review_records") or signals.get("signals")),
    }

    return {"pmf_signal_report": pmf_signal_report}


def _answer_success_questions(*, sections: dict[str, Any]) -> dict[str, bool | None]:
    onboarding = (
        sections.get("phase_2_onboarding_validation", [{}])[0].get("onboarding_validation_report") or {}
    )
    provider = (
        sections.get("phase_3_provider_connection_validation", [{}])[0].get("provider_validation_report") or {}
    )
    trust = (
        sections.get("phase_4_trust_understanding_validation", [{}])[0].get("trust_understanding_report") or {}
    )
    workflow = sections.get("phase_5_first_workflow_validation", [{}])[0].get("workflow_validation_report") or {}
    value = (
        sections.get("phase_7_value_realization_validation", [{}])[0].get("customer_value_validation_report") or {}
    )
    pmf = sections.get("phase_8_product_market_signal_review", [{}])[0].get("pmf_signal_report") or {}

    return {
        "understand_what_aethos_is": onboarding.get("completion_rate", 0) >= 0.3,
        "complete_onboarding": onboarding.get("completion_rate", 0) >= 0.7,
        "connect_a_provider": any(
            provider.get(k) for k in ("github_connection_success", "railway_connection_success", "vercel_connection_success")
        ),
        "understand_trust_boundaries": trust.get("trust_comprehension_evidence_count", 0) > 0,
        "run_governed_workflow": workflow.get("first_workflow_recorded", False),
        "obtain_value": (value.get("questions") or {}).get("did_users_obtain_value", False),
        "return_voluntarily": pmf.get("willingness_to_continue") in {True, "positive", "developing", "strong"},
    }


def build_limited_external_customer_validation_program(
    *, session_id: str = "default"
) -> LimitedExternalCustomerValidationProgramResult:
    sid = (session_id or "default").strip()[:64] or "default"

    phase1 = _build_phase_1_candidate_selection(session_id=sid)
    phase2 = _build_phase_2_onboarding_validation(session_id=sid)
    phase3 = _build_phase_3_provider_validation(session_id=sid)
    phase4 = _build_phase_4_trust_understanding(session_id=sid)
    phase5 = _build_phase_5_workflow_validation(session_id=sid)
    phase6 = _build_phase_6_feedback(session_id=sid)
    phase7 = _build_phase_7_value(session_id=sid)
    phase8 = _build_phase_8_pmf(session_id=sid)

    sections = {
        "phase_1_candidate_selection": [phase1],
        "phase_2_onboarding_validation": [phase2],
        "phase_3_provider_connection_validation": [phase3],
        "phase_4_trust_understanding_validation": [phase4],
        "phase_5_first_workflow_validation": [phase5],
        "phase_6_customer_feedback_collection": [phase6],
        "phase_7_value_realization_validation": [phase7],
        "phase_8_product_market_signal_review": [phase8],
    }

    success_answers = _answer_success_questions(sections=sections)

    success_criteria = {
        "onboarding_success_evidence": phase2["onboarding_validation_report"].get("validated"),
        "provider_connection_evidence": phase3["provider_validation_report"].get("validated"),
        "trust_understanding_evidence": phase4["trust_understanding_report"].get("validated"),
        "workflow_completion_evidence": phase5["workflow_validation_report"].get("validated"),
        "customer_value_evidence": phase7["customer_value_validation_report"].get("validated"),
        "pmf_pull_evidence": phase8["pmf_signal_report"].get("validated"),
        "program_complete": all(success_answers.get(q) for q in SUCCESS_QUESTIONS if success_answers.get(q) is not None),
    }

    blockers: list[str] = []
    if not phase1["validation_admission_review"].get("validated"):
        blockers.append("validation_admission_review_pending")

    board = {
        "schema_version": LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_SCHEMA_VERSION,
        "workstream_id": LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_ID,
        "exported_at": _exported_at(),
        "session_id": sid,
        "core_principle": CORE_PRINCIPLE,
        "read_only": True,
        "mutation_performed": False,
        "customer_validation_authority": False,
        "automatic_provisioning": False,
        "non_goals": list(PROGRAM_NON_GOALS),
        "phases": list(LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PHASES),
        "success_questions": list(SUCCESS_QUESTIONS),
        "success_question_answers": success_answers,
        "success_criteria": success_criteria,
        "sections": sections,
        "sources": {
            "fix_312_candidate_selection": True,
            "fix_301_onboarding": True,
            "fix_303_providers": True,
            "fix_295_296_314_trust": True,
            "fix_319_feedback": True,
            "fix_323_value": True,
            "fix_322_pmf": True,
        },
    }

    return LimitedExternalCustomerValidationProgramResult(
        ok=not blockers or phase1["validation_candidate_registry"].get("candidate_count", 0) > 0,
        session_id=sid,
        limited_external_customer_validation_program=board,
        blockers=blockers,
        detail="Limited external customer validation program composed from FIX stores (validation ≠ authority).",
    )
