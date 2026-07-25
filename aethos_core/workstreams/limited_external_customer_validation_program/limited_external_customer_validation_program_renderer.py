# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_B1 — render limited external customer validation deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def render_limited_external_customer_validation_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    answers = payload.get("success_question_answers") or {}
    lines = [
        "# Limited External Customer Validation Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_B1')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Customer validation gathers evidence. Humans approve admissions and review outcomes. "
        "**Customer validation ≠ customer authority.**",
        "",
        "## Success questions",
        "",
    ]
    for question in payload.get("success_questions") or []:
        lines.append(f"- {question.replace('_', ' ').title()}: **{answers.get(question)}**")

    lines.extend(
        [
            "",
            "## Success criteria",
            "",
            f"- Onboarding evidence: **{success.get('onboarding_success_evidence')}**",
            f"- Provider connection evidence: **{success.get('provider_connection_evidence')}**",
            f"- Trust understanding evidence: **{success.get('trust_understanding_evidence')}**",
            f"- Workflow completion evidence: **{success.get('workflow_completion_evidence')}**",
            f"- Customer value evidence: **{success.get('customer_value_evidence')}**",
            f"- PMF pull evidence: **{success.get('pmf_pull_evidence')}**",
            f"- Program complete: **{success.get('program_complete')}**",
            "",
            "## Phase 1 — Candidate selection",
            "",
            "```json",
            _json_block(
                (payload.get("sections") or {}).get("phase_1_candidate_selection", [{}])[0].get(
                    "validation_candidate_registry"
                )
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


def render_customer_value_validation_report(payload: dict[str, Any]) -> str:
    report = (
        (payload.get("sections") or {})
        .get("phase_7_value_realization_validation", [{}])[0]
        .get("customer_value_validation_report")
        or {}
    )
    questions = report.get("questions") or {}
    lines = [
        "# Customer Value Validation Report",
        "",
        f"- Did users obtain value? **{questions.get('did_users_obtain_value')}**",
        f"- What value? **{questions.get('what_value')}**",
        f"- How quickly? **{questions.get('how_quickly')}**",
        "",
        "## Value scorecard",
        "",
        "```json",
        _json_block(report.get("value_scorecard") or {}),
        "```",
        "",
        "## Full report",
        "",
        "```json",
        _json_block(report),
        "```",
    ]
    return "\n".join(lines)


def render_first_customer_evidence_report(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    onboarding = (sections.get("phase_2_onboarding_validation") or [{}])[0].get(
        "onboarding_validation_report"
    ) or {}
    provider = (sections.get("phase_3_provider_connection_validation") or [{}])[0].get(
        "provider_validation_report"
    ) or {}
    workflow = (sections.get("phase_5_first_workflow_validation") or [{}])[0].get(
        "workflow_validation_report"
    ) or {}
    feedback = (sections.get("phase_6_customer_feedback_collection") or [{}])[0].get(
        "validation_feedback_report"
    ) or {}
    pmf = (sections.get("phase_8_product_market_signal_review") or [{}])[0].get("pmf_signal_report") or {}

    lines = [
        "# First Customer Evidence Report",
        "",
        "Early external-user evidence across onboarding, providers, workflow, feedback, and PMF signals.",
        "",
        "## Onboarding",
        "",
        f"- Completion rate: **{onboarding.get('completion_rate')}**",
        f"- Steps completed: **{len(onboarding.get('steps_completed') or [])}**",
        "",
        "## Providers",
        "",
        f"- GitHub success: **{provider.get('github_connection_success')}**",
        f"- Railway success: **{provider.get('railway_connection_success')}**",
        f"- Vercel success: **{provider.get('vercel_connection_success')}**",
        "",
        "## First workflow",
        "",
        f"- First workflow recorded: **{workflow.get('first_workflow_recorded')}**",
        f"- Completion rate: **{workflow.get('workflow_completion_rate')}**",
        "",
        "## Feedback",
        "",
        f"- Feedback count: **{feedback.get('feedback_count')}**",
        "",
        "## PMF signals",
        "",
        f"- Willingness to continue: **{pmf.get('willingness_to_continue')}**",
        f"- Willingness to recommend: **{pmf.get('willingness_to_recommend')}**",
        "",
        "## Combined evidence",
        "",
        "```json",
        _json_block(
            {
                "onboarding": onboarding,
                "provider": provider,
                "workflow": workflow,
                "feedback": feedback,
                "pmf": pmf,
            }
        ),
        "```",
    ]
    return "\n".join(lines)


def render_all_limited_external_customer_validation_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "LIMITED_EXTERNAL_CUSTOMER_VALIDATION_REPORT.md": render_limited_external_customer_validation_report(
            payload
        ),
        "CUSTOMER_VALUE_VALIDATION_REPORT.md": render_customer_value_validation_report(payload),
        "FIRST_CUSTOMER_EVIDENCE_REPORT.md": render_first_customer_evidence_report(payload),
    }
