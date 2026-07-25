# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A1 — render PilotOS operational proof deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def render_pilotos_operational_proof_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    readiness = (
        (payload.get("sections") or {})
        .get("phase_1_repository_readiness", [{}])[0]
        .get("pilotos_readiness_report")
        or {}
    )
    lines = [
        "# PilotOS UI Operational Proof Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_A1')}",
        f"**Repository:** {payload.get('repository', 'pilotmain/pilot-os-ui')}",
        f"**Arc state:** {payload.get('arc_state', 'UNPROVEN')}",
        f"**Trust status:** {payload.get('trust_status', 'none')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Objective",
        "",
        "Generate real-world PilotOS UI operational evidence using existing FIX 188/192/181 paths — no new intelligence modules.",
        "",
        "## Success criteria",
        "",
        f"- Pilot 1 completed: **{success.get('pilot_1_completed')}**",
        f"- Pilot 2 completed: **{success.get('pilot_2_completed')}**",
        f"- Pilot 3 completed: **{success.get('pilot_3_completed')}**",
        f"- Trust freeze completed: **{success.get('trust_freeze_completed')}**",
        f"- Trust decision recorded: **{success.get('trust_decision_recorded')}**",
        f"- Cross-repository validation updated: **{success.get('cross_repository_validation_updated')}**",
        f"- Executive dashboard real evidence: **{success.get('executive_dashboard_real_evidence')}**",
        f"- Program complete: **{success.get('program_complete')}**",
        "",
        "## Phase 1 — Repository readiness",
        "",
        f"- FIX 187 expansion approved: **{readiness.get('fix_187_expansion_approved')}**",
        f"- FIX 182 readiness OK: **{readiness.get('fix_182_readiness_ok')}**",
        f"- Eligible to start pilot 1: **{readiness.get('eligible_to_start_pilot_1')}**",
        "",
        "### Readiness report",
        "",
        "```json",
        _json_block(readiness),
        "```",
        "",
        "## Execution commands",
        "",
        "1. Approve FIX 187 expansion for `pilotmain/pilot-os-ui`",
        "2. `pilot arc issue: pilotmain/pilot-os-ui#1`",
        "3. `run pilotos pilot 1` → `run pilotos pilot 2` → `run pilotos pilot 3`",
        "4. `show pilotos trust report freeze`",
        "5. `pilotos trust freeze: ...`",
        "6. `pilotos trust decision approve: ...`",
        "",
        "Or use:",
        "",
        "```bash",
        "python scripts/generate_pilotos_operational_proof_reports.py --run-pilot 1",
        "python scripts/generate_pilotos_operational_proof_reports.py --report",
        "```",
        "",
        "## Non-goals",
        "",
    ]
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_pilotos_evidence_density_report(payload: dict[str, Any]) -> str:
    density = (
        (payload.get("sections") or {})
        .get("phase_7_evidence_density_review", [{}])[0]
        .get("pilotos_evidence_density_report")
        or {}
    )
    pilot_sections = []
    for phase_key, bundle_key in (
        ("phase_2_pilot_1_execution", "pilotos_pilot1_evidence_bundle"),
        ("phase_3_pilot_2_execution", "pilotos_pilot2_evidence_bundle"),
        ("phase_4_pilot_3_execution", "pilotos_pilot3_evidence_bundle"),
    ):
        bundle = (payload.get("sections") or {}).get(phase_key, [{}])[0].get(bundle_key) or {}
        pilot_sections.append(bundle)

    lines = [
        "# PilotOS UI Evidence Density Report",
        "",
        f"**Level:** {density.get('evidence_density_level', 'INSUFFICIENT')}",
        f"**Score:** {density.get('evidence_density_score', 0)}",
        "",
        "## Assessment questions",
        "",
        f"- Meaningful operational proof? **{density.get('meaningful_operational_proof')}**",
        f"- External reviewer would trust? **{density.get('external_reviewer_would_trust')}**",
        "",
        "## Metrics",
        "",
        f"- Audits present: **{density.get('audits_present')}** / 3",
        f"- Pilots complete: **{density.get('pilots_complete')}** / 3",
        f"- Receipt count: **{density.get('receipt_count')}**",
        f"- Pending timeline answers: **{density.get('pending_timeline_answers')}**",
        "",
        "## Pilot evidence bundles",
        "",
    ]
    for bundle in pilot_sections:
        lines.extend(
            [
                f"### Pilot {bundle.get('pilot_number')}",
                "",
                f"- Session: `{bundle.get('session_id')}`",
                f"- Audit present: **{bundle.get('audit_present')}**",
                f"- Outcome: **{bundle.get('pilot_outcome', 'none')}**",
                f"- Receipts: **{len(bundle.get('receipt_paths') or [])}**",
                "",
            ]
        )
    lines.extend(["## Full density report", "", "```json", _json_block(density), "```"])
    return "\n".join(lines)


def render_pilotos_trust_validation_report(payload: dict[str, Any]) -> str:
    freeze = (payload.get("sections") or {}).get("phase_5_trust_freeze", [{}])[0]
    decision = (payload.get("sections") or {}).get("phase_6_trust_review", [{}])[0].get(
        "pilotos_trust_decision_record"
    ) or {}
    exec_report = (
        (payload.get("sections") or {})
        .get("phase_8_executive_dashboard_validation", [{}])[0]
        .get("pilotos_executive_visibility_report")
        or {}
    )

    lines = [
        "# PilotOS UI Trust Validation Report",
        "",
        f"**Trust status:** {payload.get('trust_status', 'none')}",
        f"**Arc state:** {payload.get('arc_state', 'UNPROVEN')}",
        "",
        "## FIX 192 trust freeze",
        "",
        "```json",
        _json_block(freeze.get("pilotos_trust_freeze_artifact") or {}),
        "```",
        "",
        "## Trust boundary snapshot",
        "",
        "```json",
        _json_block(freeze.get("trust_boundary_snapshot") or {}),
        "```",
        "",
        "## Trust recommendation snapshot",
        "",
        "```json",
        _json_block(freeze.get("trust_recommendation_snapshot") or {}),
        "```",
        "",
        "## Trust decision record",
        "",
        f"- Decision recorded: **{decision.get('trust_decision_recorded')}**",
        f"- Human approve: **{decision.get('human_trust_decision_approve')}**",
        "",
        "```json",
        _json_block(decision),
        "```",
        "",
        "## Cross-repository validation",
        "",
        "```json",
        _json_block(exec_report.get("pilotos_trust_state_in_cross_repo") or {}),
        "```",
        "",
        "## Executive module visibility",
        "",
    ]
    for fix_label, assessment in (exec_report.get("module_assessments") or {}).items():
        if isinstance(assessment, dict):
            lines.append(
                f"- **{fix_label}**: compose_available={assessment.get('compose_available')} "
                f"placeholder_risk={assessment.get('placeholder_risk')}"
            )
    return "\n".join(lines)


def render_all_pilotos_operational_proof_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "PILOTOS_OPERATIONAL_PROOF_REPORT.md": render_pilotos_operational_proof_report(payload),
        "PILOTOS_EVIDENCE_DENSITY_REPORT.md": render_pilotos_evidence_density_report(payload),
        "PILOTOS_TRUST_VALIDATION_REPORT.md": render_pilotos_trust_validation_report(payload),
    }
