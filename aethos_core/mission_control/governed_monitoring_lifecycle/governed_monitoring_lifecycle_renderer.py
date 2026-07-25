# SPDX-License-Identifier: Apache-2.0
"""FIX 220 — Markdown renderer for governed monitoring lifecycle."""

from __future__ import annotations

from typing import Any


def render_governed_monitoring_lifecycle(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    health = (sections.get("monitoring_health_assessment") or [{}])[0]
    incident = (sections.get("incident_detection") or [{}])[0]
    recommendation = (sections.get("monitoring_recommendation") or [{}])[0]
    escalation = (sections.get("incident_escalation_artifact") or [{}])[0] if sections.get(
        "incident_escalation_artifact"
    ) else {}

    lines = [
        "# Governed Monitoring Lifecycle (FIX 220 — monitoring_authority ≠ operational_authority)",
        "",
        f"- monitoring authority: **{payload.get('monitoring_authority', False)}** _(always false)_",
        f"- autonomous remediation: **{payload.get('autonomous_remediation_enabled', False)}** _(always false)_",
        f"- incident classification: **{payload.get('incident_classification')}**",
        f"- current stage: **{payload.get('current_stage')}**",
        f"- human decision: **{payload.get('human_operational_decision') or 'pending'}**",
        "",
        payload.get("invariant", ""),
        "",
        "## Monitoring Health",
        "",
        f"- health score: **{health.get('health_score', 0)}**",
        f"- deployment success observed: **{health.get('deployment_success')}**",
        f"- workflow observed: **{health.get('workflow_completion_observed')}**",
    ]

    blockers = health.get("outstanding_blockers") or []
    if blockers:
        lines.append(f"- blockers: {', '.join(blockers)}")

    lines.extend(
        [
            "",
            "## Incident Detection",
            "",
            f"**{incident.get('classification', 'UNKNOWN')}** — {incident.get('rationale', '')}",
            "",
            "## Monitoring Recommendation",
            "",
            f"**{recommendation.get('recommendation', 'REVIEW_REQUIRED')}** — {recommendation.get('rationale', '')}",
            "",
            "_Recommendation only — not operational authority._",
        ]
    )

    if escalation:
        lines.extend(
            [
                "",
                "## Incident Escalation",
                "",
                f"- escalation id: `{escalation.get('escalation_id')}`",
                f"- executable: **{escalation.get('escalation_executable', False)}**",
            ]
        )

    timeline = sections.get("operational_timeline") or []
    if timeline:
        lines.extend(["", "## Operational Timeline", ""])
        for event in timeline[-6:]:
            lines.append(f"- {event.get('stage')}: {event.get('kind') or event.get('label') or event.get('event_id')}")

    return "\n".join(lines)
