# SPDX-License-Identifier: Apache-2.0
"""Render cross-repository operational proof review deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def render_cross_repository_operational_proof_review(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    trust = (sections.get("review_area_8_trust_generalization") or [{}])[0].get(
        "trust_generalization_assessment"
    ) or {}
    recommendation = (sections.get("review_area_10_strategic_recommendation") or [{}])[0].get(
        "cross_repository_strategic_recommendation"
    ) or {}
    success = payload.get("success_criteria") or {}

    lines = [
        "# Cross-Repository Operational Proof Review",
        "",
        f"**Review ID:** {payload.get('review_id', 'CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Cross-repository operational review evaluates evidence. Humans determine conclusions. "
        "This review is **not** trust authority.",
        "",
        "## FIX 191 question",
        "",
        f"**Does governed delivery generalize across repositories?**",
        "",
        f"- Assessment level: **{trust.get('level', 'NOT_PROVEN')}**",
        f"- Evidence-backed answer available: **{trust.get('evidence_backed_answer')}**",
        f"- Governed delivery generalizes: **{trust.get('governed_delivery_generalizes')}**",
        "",
        f"{trust.get('summary', '')}",
        "",
        "## Success criteria",
        "",
        f"- FIX 191 question answered with evidence: **{success.get('fix_191_question_answered_with_evidence')}**",
        f"- Four-repository review complete: **{success.get('four_repository_review_complete')}**",
        f"- Review complete (all repos PROVEN): **{success.get('program_complete')}**",
        "",
        "## Review areas",
        "",
    ]
    for area in payload.get("review_areas") or []:
        lines.append(f"- {area}")

    lines.extend(
        [
            "",
            "## Strategic recommendation (summary)",
            "",
            f"- Primary: **{recommendation.get('primary_recommendation')}**",
            f"- Secondary: **{recommendation.get('secondary_recommendation')}**",
            "",
            f"{recommendation.get('rationale', '')}",
            "",
            "## Repository trust baselines",
            "",
            "```json",
            _json_block(
                (sections.get("review_area_1_repository_trust_baselines") or [{}])[0].get(
                    "repository_trust_baseline_review"
                )
            ),
            "```",
            "",
            "## Pilot completion",
            "",
            "```json",
            _json_block(
                (sections.get("review_area_2_pilot_completion") or [{}])[0].get("pilot_completion_review")
            ),
            "```",
            "",
            "## Non-goals",
            "",
        ]
    )
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_trust_generalization_assessment(payload: dict[str, Any]) -> str:
    assessment = (
        (payload.get("sections") or {})
        .get("review_area_8_trust_generalization", [{}])[0]
        .get("trust_generalization_assessment")
        or {}
    )
    consistency = (
        (payload.get("sections") or {})
        .get("review_area_6_cross_repository_consistency", [{}])[0]
        .get("cross_repository_consistency_review")
        or {}
    )
    gaps = (
        (payload.get("sections") or {})
        .get("review_area_9_remaining_gaps", [{}])[0]
        .get("remaining_gap_assessment")
        or {}
    )

    lines = [
        "# Trust Generalization Assessment",
        "",
        f"**Level:** {assessment.get('level', 'NOT_PROVEN')}",
        "",
        "## Summary",
        "",
        assessment.get("summary", ""),
        "",
        "## Metrics",
        "",
        f"- Repositories operational proof complete: **{assessment.get('repositories_operational_proof_complete')}** / 4",
        f"- Repositories all pilots complete: **{assessment.get('repositories_all_pilots_complete')}** / 4",
        f"- Repositories conditionally trusted: **{assessment.get('repositories_conditionally_trusted')}** / 4",
        f"- Repositories with trust freeze: **{assessment.get('repositories_with_trust_freeze')}** / 4",
        "",
        "## Consistency questions",
        "",
        f"- Same trust progression? **{(consistency.get('questions') or {}).get('same_trust_progression')}**",
        f"- Substantially different treatment required? **{(consistency.get('questions') or {}).get('substantially_different_treatment_required')}**",
        "",
        "## Remaining gaps",
        "",
        f"- Missing evidence items: **{gaps.get('gap_count', 0)}**",
        f"- Weak evidence items: **{gaps.get('weak_count', 0)}**",
        "",
        "## Full assessment",
        "",
        "```json",
        _json_block(assessment),
        "```",
    ]
    return "\n".join(lines)


def render_post_proof_strategic_recommendation(payload: dict[str, Any]) -> str:
    recommendation = (
        (payload.get("sections") or {})
        .get("review_area_10_strategic_recommendation", [{}])[0]
        .get("cross_repository_strategic_recommendation")
        or {}
    )
    assessment = (
        (payload.get("sections") or {})
        .get("review_area_8_trust_generalization", [{}])[0]
        .get("trust_generalization_assessment")
        or {}
    )

    lines = [
        "# POST Proof Strategic Recommendation",
        "",
        f"**Trust generalization level:** {assessment.get('level', 'NOT_PROVEN')}",
        "",
        "## Primary recommendation",
        "",
        f"**{recommendation.get('primary_recommendation')}**",
        "",
        recommendation.get("rationale", ""),
        "",
        "## Secondary recommendation",
        "",
        f"**{recommendation.get('secondary_recommendation') or 'None'}**",
        "",
        "## Options evaluated",
        "",
        "### Option A — Expand operational proof further",
        "",
        "Continue WORKSTREAM_A1–A3 execution; close per-repository trust freeze and audit gaps.",
        "",
        "### Option B — Expand provider coverage",
        "",
        "Implement phase-2 cloud providers after operational proof baseline is stable.",
        "",
        "### Option C — Begin limited external customer validation",
        "",
        "Engage external reviewers or pilot customers when four-repository proof is PROVEN.",
        "",
        "### Option D — Revisit architecture",
        "",
        "Only if evidence reveals non-composeable gaps — not assumed from sparse dashboards.",
        "",
        "## Human decision",
        "",
        f"Human decision required: **{recommendation.get('human_decision_required')}**",
        "",
        "```json",
        _json_block(recommendation),
        "```",
    ]
    return "\n".join(lines)


def render_all_cross_repository_operational_proof_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW.md": render_cross_repository_operational_proof_review(payload),
        "TRUST_GENERALIZATION_ASSESSMENT.md": render_trust_generalization_assessment(payload),
        "POST_PROOF_STRATEGIC_RECOMMENDATION.md": render_post_proof_strategic_recommendation(payload),
    }
