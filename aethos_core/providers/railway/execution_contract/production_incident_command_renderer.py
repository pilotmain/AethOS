# SPDX-License-Identifier: Apache-2.0
"""FIX 123 — production incident command renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.production_incident_command import (
    IncidentContextBundle,
    build_incident_context_bundle,
)
from aethos_core.providers.railway.execution_contract.production_incident_command_contract import (
    ALLOWED_INCIDENT_DECISIONS,
    AUTONOMOUS_INCIDENT_MUTATION_PERMITTED,
    AUTONOMOUS_INCIDENT_ROLLBACK_PERMITTED,
    INCIDENT_COMMANDER_ACCEPTANCE_PHRASE,
)


def _verification_label(bundle: IncidentContextBundle) -> str:
    if bundle.verification_passed is True:
        return "passed"
    if bundle.verification_passed is False:
        return "failed"
    return "unknown"


def render_incident_summary(incident: dict[str, Any]) -> str:
    target = incident.get("target") or {}
    ctx = incident.get("attached_context") or {}
    lines = [
        "# Railway Production Incident",
        "",
        f"- incident_id: `{incident.get('incident_id', '')}`",
        f"- execution_id: `{incident.get('execution_id', '')}`",
        f"- status: **{incident.get('status', '')}**",
        f"- severity: **{incident.get('severity', '')}**",
        f"- commander: **{incident.get('commander') or 'unassigned'}**",
        f"- rollback_recommendation: **{incident.get('rollback_recommendation') or 'none'}**",
        f"- mutation_performed: **{incident.get('mutation_performed', False)}**",
        "",
        "## Target",
        f"- project: **{target.get('project', '')}**",
        f"- environment: **{target.get('environment', '')}**",
        f"- service: **{target.get('service', '')}**",
        "",
        "## Attached context",
        f"- verification: **{ctx.get('verification_status', 'unknown')}**",
        f"- rollout_stage: **{ctx.get('rollout_stage', '')}**",
        f"- incident_mode: **{ctx.get('incident_mode_active', False)}**",
        f"- escalation_ticket: **{ctx.get('escalation_ticket_id') or '—'}**",
    ]
    return "\n".join(lines)


def render_incident_timeline(incident: dict[str, Any]) -> str:
    lines = [
        "# Railway Production Incident Timeline",
        "",
        f"incident_id: `{incident.get('incident_id', '')}`",
        "",
    ]
    events = incident.get("events") or []
    if not events:
        lines.append("_No events recorded._")
        return "\n".join(lines)
    for ev in events:
        lines.extend(
            [
                f"## {ev.get('action', '')}",
                f"- timestamp: {ev.get('timestamp', '')}",
                f"- actor: {ev.get('actor', '')}",
                f"- mutation_performed: **{ev.get('mutation_performed', False)}**",
                f"- detail: {ev.get('detail', '')}",
                "",
            ]
        )
    return "\n".join(lines)


def render_incident_briefing(incident: dict[str, Any], *, bundle: IncidentContextBundle | None = None) -> str:
    bundle = bundle or build_incident_context_bundle(
        execution_id=str(incident.get("execution_id") or ""),
    )
    target = incident.get("target") or {}
    verification_label = _verification_label(bundle)
    lines = [
        "# Railway Production Incident Briefing",
        "",
        "## Incident",
        f"- id: **{incident.get('incident_id', '')}**",
        f"- status: **{incident.get('status', '')}**",
        f"- severity: **{incident.get('severity', '')}**",
        "",
        "## Target",
        f"- project: **{target.get('project', '')}**",
        f"- environment: **{target.get('environment', '')}**",
        f"- service: **{target.get('service', '')}**",
        "",
        "## Evidence",
        f"- production verification: **{verification_label}**",
        f"- rollback recommendation: **{bundle.rollback_recommendation}**",
        f"- rollout stage: **{bundle.rollout_stage}**",
        f"- incident mode: **{'enabled' if bundle.incident_mode_active else 'disabled'}**",
        f"- canary/shadow policy: **{bundle.canary_shadow_summary}**",
        "",
        "## Required human actions",
        "1. Assign incident commander",
        "2. Review verification evidence",
        "3. Decide whether to rehearse rollback",
        "4. Record decision",
        "5. Communicate status",
        "",
        "No production mutation has been performed.",
    ]
    return "\n".join(lines)


def render_incident_operator_checklist(incident: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Railway Production Incident Operator Checklist",
            "",
            f"- [ ] Assign commander (`assign railway incident commander` + phrase)",
            f"- [ ] Review briefing (`show railway incident briefing`)",
            f"- [ ] Review rollback recommendation",
            f"- [ ] Record decision (`record railway incident decision ...`)",
            f"- [ ] Authorize rollback **rehearsal only** (FIX 120 — no live rollback)",
            f"- [ ] Draft customer update (`show railway incident customer update draft`)",
            f"- [ ] Close incident when resolved (`close railway production incident`)",
            "",
            f"Incident status: **{incident.get('status', '')}**",
            f"Autonomous rollback permitted: **{AUTONOMOUS_INCIDENT_ROLLBACK_PERMITTED}**",
        ]
    )


def render_customer_update_draft(incident: dict[str, Any], *, bundle: IncidentContextBundle) -> str:
    """Safe external-facing draft — no secrets, stack traces, or speculation."""
    target = incident.get("target") or {}
    service = str(target.get("service") or "the service")
    _ = bundle
    return "\n".join(
        [
            "# Railway Production Incident — Customer Update Draft",
            "",
            "## Draft (review before sending)",
            "",
            f"We are investigating a deployment-related issue affecting {service}. "
            "Our team has initiated incident procedures and is reviewing health and deployment signals. "
            "We will provide an update once mitigation steps are confirmed.",
            "",
            "## Safety constraints applied",
            "- No internal secrets included",
            "- No raw stack traces included",
            "- No unverified customer impact claims",
            "- No autonomous production changes performed by AethOS",
            "",
            f"Incident reference (internal): `{incident.get('incident_id', '')}`",
        ]
    )


def render_incident_decisions(incident: dict[str, Any]) -> str:
    lines = ["# Railway Production Incident Decisions", ""]
    decisions = incident.get("decisions") or []
    if not decisions:
        lines.append("_No decisions recorded._")
    else:
        for row in decisions:
            lines.append(
                f"- `{row.get('decision', '')}` by {row.get('actor', '')} "
                f"at {row.get('recorded_at', '')}"
            )
    lines.extend(["", "## Allowed decisions"])
    for d in sorted(ALLOWED_INCIDENT_DECISIONS):
        lines.append(f"- `{d}`")
    return "\n".join(lines)


def render_commander_status(incident: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Railway Incident Commander Status",
            "",
            f"- incident_id: `{incident.get('incident_id', '')}`",
            f"- commander: **{incident.get('commander') or 'unassigned'}**",
            f"- status: **{incident.get('status', '')}**",
            "",
            "## Required phrase",
            INCIDENT_COMMANDER_ACCEPTANCE_PHRASE,
            "",
            f"- autonomous_mutation_permitted: **{AUTONOMOUS_INCIDENT_MUTATION_PERMITTED}**",
        ]
    )


def render_rollback_recommendation(incident: dict[str, Any], *, bundle: IncidentContextBundle) -> str:
    return "\n".join(
        [
            "# Railway Production Incident Rollback Recommendation",
            "",
            f"- recommendation: **{bundle.rollback_recommendation}**",
            f"- incident_status: **{incident.get('status', '')}**",
            f"- escalation_ticket: **{bundle.escalation_ticket_id or '—'}**",
            "",
            "Rollback rehearsal is **manual-only** (FIX 120). Live production rollback is never permitted.",
        ]
    )
