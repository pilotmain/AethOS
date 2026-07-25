# SPDX-License-Identifier: Apache-2.0
"""FIX 174 — governed lane entry recommendation (composes FIX 169 + FIX 173)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_174_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_service import (
    build_gate_routed_package_outcome_review,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_174,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_174,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_174,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_174,
    CODE_WRITE_ENABLED_FIX_174,
    EXECUTION_PERFORMED_FIX_174,
    FORBIDDEN_RECOMMENDATION_ACTIONS,
    FORBIDDEN_RECOMMENDATION_LANES,
    GATE_BYPASS_ENABLED_FIX_174,
    GOVERNANCE_MUTATION_PERFORMED_FIX_174,
    GOVERNED_LANE_ENTRY_RECOMMENDATION_FIX,
    GOVERNED_LANE_ENTRY_RECOMMENDATION_INVARIANT,
    GOVERNED_LANE_ENTRY_RECOMMENDATION_PRINCIPLES,
    GOVERNED_LANE_ENTRY_RECOMMENDATION_SCHEMA_VERSION,
    LANE_ADMISSION_PERFORMED_FIX_174,
    MERGE_DEPLOY_ENABLED_FIX_174,
    MUTATION_PERFORMED_FIX_174,
    PR_ACTION_ENABLED_FIX_174,
    RAILWAY_MUTATION_ENABLED_FIX_174,
    RECOMMENDATION_TIER,
    TIER_ESCALATION_ENABLED_FIX_174,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_169,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_173,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
    list_governed_lane_entry_recommendation_records,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_service import (
    build_work_package_readiness_lane_admission,
)


@dataclass(frozen=True)
class GovernedLaneEntryRecommendationResult:
    ok: bool
    session_id: str
    governed_lane_entry_recommendation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _readiness_upstream_read(*, readiness: dict[str, Any]) -> list[dict[str, Any]]:
    admission_pkg = (_sections(readiness).get("lane_admission_package") or [{}])[-1]
    return [
        {
            "read_id": "fix-169-readiness-read",
            "upstream_fix": "FIX 169",
            "ready_agent_count": readiness.get("ready_agent_count"),
            "eligible_lane_count": readiness.get("eligible_lane_count"),
            "admission_ready": admission_pkg.get("admission_ready"),
            "read_only": True,
            "recomputed_by_fix_174": False,
        }
    ]


def _gate_review_upstream_read(*, review: dict[str, Any]) -> list[dict[str, Any]]:
    packet = (_sections(review).get("gate_review_packet") or [{}])[0]
    return [
        {
            "read_id": "fix-173-gate-review-read",
            "upstream_fix": "FIX 173",
            "review_ready": review.get("review_ready"),
            "outcome_count": review.get("outcome_count"),
            "incomplete_package_count": review.get("incomplete_package_count"),
            "outcomes_complete": packet.get("outcomes_complete"),
            "outcomes_incomplete": packet.get("outcomes_incomplete"),
            "read_only": True,
            "reclassified_by_fix_174": False,
        }
    ]


def _quality_by_role(review: dict[str, Any]) -> dict[str, str]:
    return {
        str(row.get("agent_role_id")): str(row.get("outcome_quality") or "")
        for row in _sections(review).get("outcome_quality_classification") or []
        if row.get("agent_role_id")
    }


def _admission_by_role(readiness: dict[str, Any]) -> dict[str, bool]:
    return {
        str(row.get("agent_role_id")): bool(row.get("admission_eligible"))
        for row in _sections(readiness).get("lane_admission_analysis") or []
        if row.get("agent_role_id")
    }


def _lane_entry_candidates(
    *,
    readiness: dict[str, Any],
    review: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "lane_recommendation_artifact")]
    admission_by_role = _admission_by_role(readiness)
    quality_by_role = _quality_by_role(review)
    candidates: list[dict[str, Any]] = list(stored)

    for route in _sections(review).get("gate_handler_routing") or []:
        gate_id = str(route.get("handling_gate") or route.get("gate_id") or "")
        role = str(route.get("agent_role_id") or "")
        lane = str(route.get("lane") or "software_delivery")
        if any(forbidden in lane for forbidden in FORBIDDEN_RECOMMENDATION_LANES):
            continue
        if not gate_id:
            continue
        quality = quality_by_role.get(role, "unknown")
        admission_eligible = admission_by_role.get(role, False)
        blocked = quality in {"incomplete", "blocked"} or not admission_eligible
        candidates.append(
            {
                "candidate_id": route.get("route_id") or f"candidate-{gate_id}",
                "agent_role_id": role or None,
                "package_id": route.get("package_id"),
                "recommended_lane": lane,
                "recommended_gate": gate_id,
                "outcome_quality_upstream": quality,
                "admission_eligible_upstream": admission_eligible,
                "recommendation_status": "blocked" if blocked else "eligible",
                "lane_entry": False,
                "lane_admission_performed": False,
                "gate_bypass": False,
                "read_only": True,
            }
        )

    if not candidates:
        candidates.append(
            {
                "candidate_id": "no-candidates",
                "detail": "Lane entry candidates unavailable until FIX 169 readiness and FIX 173 gate review are ready.",
                "read_only": True,
            }
        )
    return candidates[:12]


def _eligibility_rationale(
    *,
    readiness: dict[str, Any],
    review: dict[str, Any],
    candidates: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "eligibility_rationale_note")]
    rows: list[dict[str, Any]] = list(stored)
    admission_pkg = (_sections(readiness).get("lane_admission_package") or [{}])[-1]
    packet = (_sections(review).get("gate_review_packet") or [{}])[0]

    for cand in candidates:
        if not cand.get("candidate_id") or cand.get("candidate_id") == "no-candidates":
            continue
        status = cand.get("recommendation_status")
        rows.append(
            {
                "rationale_id": f"rationale-{cand.get('candidate_id')}",
                "agent_role_id": cand.get("agent_role_id"),
                "recommended_gate": cand.get("recommended_gate"),
                "recommendation_status": status,
                "detail": (
                    f"Upstream FIX 169 admission_eligible={cand.get('admission_eligible_upstream')}; "
                    f"FIX 173 outcome_quality={cand.get('outcome_quality_upstream')}; "
                    f"FIX 169 admission_ready={admission_pkg.get('admission_ready')}; "
                    f"FIX 173 outcomes_complete={packet.get('outcomes_complete')}."
                ),
                "lane_admission_performed": False,
                "read_only": True,
            }
        )
    if len(rows) == len(stored):
        rows.append(
            {
                "rationale_id": "pending-upstream",
                "detail": "Eligibility rationale requires FIX 169 readiness and FIX 173 gate review context.",
                "read_only": True,
            }
        )
    return rows


def _blocked_lane_explanations(
    *,
    readiness: dict[str, Any],
    review: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "blocked_lane_note")]
    blocked: list[dict[str, Any]] = list(stored)

    for row in _sections(readiness).get("admission_blockers") or []:
        if row.get("blocker_id"):
            blocked.append(
                {
                    "explanation_id": f"blocked-169-{row.get('blocker_id')}",
                    "upstream_fix": "FIX 169",
                    "blocker_id": row.get("blocker_id"),
                    "detail": row.get("detail"),
                    "lane_entry": False,
                    "read_only": True,
                }
            )

    for row in _sections(review).get("incomplete_package_detection") or []:
        if row.get("incomplete"):
            blocked.append(
                {
                    "explanation_id": f"blocked-173-{row.get('detection_id')}",
                    "upstream_fix": "FIX 173",
                    "package_id": row.get("package_id"),
                    "detail": row.get("detail") or "Incomplete package blocks lane entry recommendation.",
                    "lane_entry": False,
                    "read_only": True,
                }
            )

    if not blocked:
        blocked.append(
            {
                "explanation_id": "no-blocked-lanes",
                "detail": "No blocked lanes detected in upstream FIX 169/173 context.",
                "read_only": True,
            }
        )
    return blocked[:16]


def _missing_prerequisites_references(*, readiness: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for row in _sections(readiness).get("admission_blockers") or []:
        missing = row.get("missing_prerequisites")
        if not missing:
            continue
        refs.append(
            {
                "reference_id": row.get("blocker_id"),
                "upstream_fix": "FIX 169",
                "agent_role_id": row.get("agent_role_id"),
                "missing_prerequisites": missing,
                "detail": row.get("detail"),
                "recomputed_by_fix_174": False,
                "read_only": True,
            }
        )
    if not refs:
        refs.append(
            {
                "reference_id": "no-missing-prerequisites",
                "detail": "No missing prerequisites referenced from FIX 169.",
                "read_only": True,
            }
        )
    return refs


def _escalation_requirements(*, review: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "escalation_recommendation_note")]
    reqs: list[dict[str, Any]] = list(stored)
    for row in _sections(review).get("escalation_trigger_detection") or []:
        if row.get("escalation_required") or row.get("trigger_id") or row.get("monitor_id"):
            reqs.append({**row, "upstream_fix": "FIX 173", "read_only": True})
    if not reqs:
        reqs.append(
            {
                "requirement_id": "no-escalation",
                "detail": "No escalation requirements from upstream FIX 173.",
                "read_only": True,
            }
        )
    return reqs


def _recommended_next_gate(
    *,
    review: dict[str, Any],
    candidates: list[dict[str, Any]],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "next_gate_note")]
    gates: list[dict[str, Any]] = list(stored)
    seen: set[str] = set()

    eligible = [
        c for c in candidates if c.get("recommendation_status") == "eligible" and c.get("recommended_gate")
    ]
    for cand in eligible[:4]:
        gate = str(cand.get("recommended_gate"))
        if gate in seen:
            continue
        seen.add(gate)
        gates.append(
            {
                "gate_id": gate,
                "agent_role_id": cand.get("agent_role_id"),
                "lane": cand.get("recommended_lane"),
                "upstream_handler": "FIX 173 gate_handler_routing",
                "gate_bypass": False,
                "lane_admission_performed": False,
                "detail": f"Recommended next gate `{gate}` — frozen gate decides admission.",
                "read_only": True,
            }
        )

    if not gates:
        for row in _sections(review).get("gate_handler_routing") or []:
            gate = str(row.get("handling_gate") or "")
            if gate and gate not in seen:
                seen.add(gate)
                gates.append(
                    {
                        "gate_id": gate,
                        "upstream_handler": "FIX 173",
                        "gate_bypass": False,
                        "detail": "Gate from upstream handler routing — admission not performed.",
                        "read_only": True,
                    }
                )
    return gates[:8]


def _forbidden_lane_recommendation_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "forbidden_recommendation_note")]
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_RECOMMENDATION_ACTIONS
    ]
    return stored + catalog


def _next_step_lane_recommendation_sequence(*, recommendation_ready: bool) -> list[dict[str, Any]]:
    if not recommendation_ready:
        return [
            {
                "step": 1,
                "command_hint": "lane admission readiness — complete FIX 169 evaluation",
                "lane_admission_performed": False,
                "read_only": True,
            },
            {
                "step": 2,
                "command_hint": "gate-routed package outcome review — complete FIX 173 review",
                "read_only": True,
            },
        ]
    return [
        {
            "step": 1,
            "command_hint": "lane recommendation artifact: <summary> — persist recommendation record",
            "lane_admission_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "review lane entry candidates and blocked explanations — human decides admission",
            "read_only": True,
        },
        {
            "step": 3,
            "command_hint": "hand recommended gate to frozen software delivery — gate decides lane entry",
            "lane_entry": False,
            "read_only": True,
        },
    ]


def _lane_recommendation_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    recommendation_ready: bool,
    candidate_count: int,
    eligible_count: int,
) -> list[dict[str, Any]]:
    score = 20 + (30 if recommendation_ready else 0) + min(candidate_count * 5, 25)
    if eligible_count:
        score += min(eligible_count * 5, 15)
    if _by_kind(records, "lane_recommendation_artifact"):
        score += 10
    score = min(100, score)
    label = "recommendation_ready" if score >= 80 else "partial" if score >= 50 else "blocked"
    return [
        {
            "score_id": "governed-lane-entry-recommendation-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "lane_admission_performed": LANE_ADMISSION_PERFORMED_FIX_174,
            "lane_entry": False,
            "execution_performed": EXECUTION_PERFORMED_FIX_174,
            "composes_upstream_layers": True,
            "detail": "Lane recommendation integrity — composes FIX 169 + FIX 173 without admission authority.",
            "read_only": True,
        }
    ]


def build_governed_lane_entry_recommendation(*, session_id: str) -> GovernedLaneEntryRecommendationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    readiness_result = build_work_package_readiness_lane_admission(session_id=sid)
    review_result = build_gate_routed_package_outcome_review(session_id=sid)
    readiness = (
        readiness_result.work_package_readiness_lane_admission if readiness_result.ok else {}
    )
    review = review_result.gate_routed_package_outcome_review if review_result.ok else {}

    plan_id = str(review.get("plan_id") or readiness.get("plan_id") or "") or None
    correlation_id = str(review.get("correlation_id") or readiness.get("correlation_id") or "") or None

    records = list_governed_lane_entry_recommendation_records(session_id=sid, plan_id=plan_id)
    review_ready = bool(review.get("review_ready"))
    admission_pkg = (_sections(readiness).get("lane_admission_package") or [{}])[-1]
    admission_ready_upstream = bool(admission_pkg.get("admission_ready"))
    recommendation_ready = review_ready and readiness_result.ok and review_result.ok

    candidates = _lane_entry_candidates(readiness=readiness, review=review, records=records)
    eligible_count = sum(1 for c in candidates if c.get("recommendation_status") == "eligible")

    sections = {
        "readiness_upstream_read": _readiness_upstream_read(readiness=readiness),
        "gate_review_upstream_read": _gate_review_upstream_read(review=review),
        "lane_entry_candidates": candidates,
        "eligibility_rationale": _eligibility_rationale(
            readiness=readiness,
            review=review,
            candidates=candidates,
            records=records,
        ),
        "blocked_lane_explanations": _blocked_lane_explanations(
            readiness=readiness,
            review=review,
            records=records,
        ),
        "missing_prerequisites_references": _missing_prerequisites_references(readiness=readiness),
        "escalation_requirements": _escalation_requirements(review=review, records=records),
        "recommended_next_gate": _recommended_next_gate(
            review=review,
            candidates=candidates,
            records=records,
        ),
        "forbidden_lane_recommendation_actions": _forbidden_lane_recommendation_actions(records=records),
        "next_step_lane_recommendation_sequence": _next_step_lane_recommendation_sequence(
            recommendation_ready=recommendation_ready,
        ),
        "lane_recommendation_integrity_scoring": _lane_recommendation_integrity_scoring(
            records=records,
            recommendation_ready=recommendation_ready,
            candidate_count=len(candidates),
            eligible_count=eligible_count,
        ),
    }

    governed_lane_entry_recommendation: dict[str, Any] = {
        "schema_version": GOVERNED_LANE_ENTRY_RECOMMENDATION_SCHEMA_VERSION,
        "fix": GOVERNED_LANE_ENTRY_RECOMMENDATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_174,
        "execution_performed": EXECUTION_PERFORMED_FIX_174,
        "lane_admission_performed": LANE_ADMISSION_PERFORMED_FIX_174,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_174,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_174,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_174,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_174,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_174,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_174,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_174,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_174,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_174,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_174,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_174,
        "invariant": GOVERNED_LANE_ENTRY_RECOMMENDATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "lane_recommendation_record_count": len(records),
        "lane_entry_candidate_count": len(candidates),
        "eligible_lane_entry_count": eligible_count,
        "recommendation_tier": RECOMMENDATION_TIER if recommendation_ready else None,
        "recommendation_ready": recommendation_ready,
        "admission_ready_upstream": admission_ready_upstream,
        "review_ready_upstream": review_ready,
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_169_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_169),
            "fix_173_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_173),
        },
        "fix_174_certification_requirements": list(FIX_174_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "governed_lane_entry_recommendation_cognition": True,
        "lane_recommendation_not_admission_authority": True,
        "governed_lane_entry_recommendation_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GOVERNED_LANE_ENTRY_RECOMMENDATION_PRINCIPLES
        ],
        "sources": {
            "composes_work_package_readiness_lane_admission": readiness_result.ok,
            "composes_gate_routed_package_outcome_review": review_result.ok,
            "work_package_readiness_lane_admission_fix": "FIX 169",
            "gate_routed_package_outcome_review_fix": "FIX 173",
            "lane_recommendation_records": len(records),
        },
    }
    return GovernedLaneEntryRecommendationResult(
        ok=True,
        session_id=sid,
        governed_lane_entry_recommendation=governed_lane_entry_recommendation,
        detail="Governed lane entry recommendation assembled (composes FIX 169 + FIX 173 — recommendation ≠ admission).",
    )
