# SPDX-License-Identifier: Apache-2.0
"""FIX 334 / EXECUTION_TRACK_1 — render workspace creation deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_workspace_creation_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    lines = [
        "# Workspace Creation Report",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 334')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Repository preparation is allowed under governance controls. "
        "**Workspace creation ≠ deployment authority.** Trust remains separate.",
        "",
        "## Success criteria",
        "",
        f"- Workspace created: **{success.get('workspace_created')}**",
        f"- Repository structure prepared: **{success.get('repository_structure_prepared')}**",
        f"- Delivery metadata initialized: **{success.get('delivery_metadata_initialized')}**",
        f"- Readiness validated: **{success.get('readiness_validated')}**",
        f"- Evidence produced: **{success.get('evidence_produced')}**",
        f"- Track complete: **{success.get('track_complete')}**",
        "",
        "## Phase 1 — Workspace registry",
        "",
        "```json",
        _json_block(_section(payload, "phase_1_workspace_registry", "workspace_registry")),
        "```",
        "",
        "## Phase 6 — Workspace dashboard",
        "",
        "```json",
        _json_block(_section(payload, "phase_6_workspace_dashboard", "workspace_creation_dashboard")),
        "```",
        "",
        "## Non-goals",
        "",
    ]
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_repository_bootstrap_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_2_repository_bootstrap", "repository_bootstrap_report") or {}
    templates = _section(payload, "phase_3_project_template_registry", "project_template_registry") or {}
    lines = [
        "# Repository Bootstrap Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Bootstrap status",
        "",
        f"- Workspace decision approve: **{report.get('workspace_decision_approve')}**",
        f"- Bootstrap executed: **{report.get('bootstrap_executed')}**",
        f"- Git push performed: **{report.get('git_push_performed')}**",
        f"- Deployment performed: **{report.get('deployment_performed')}**",
        f"- Code generation performed: **{report.get('code_generation_performed')}**",
        "",
        "## Supported templates",
        "",
        "```json",
        _json_block(templates),
        "```",
        "",
        "## Execution receipts",
        "",
        "```json",
        _json_block(report.get("execution_receipts") or []),
        "```",
    ]
    return "\n".join(lines)


def render_workspace_verification_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_4_workspace_verification", "workspace_verification_report") or {}
    bundle = _section(payload, "phase_5_bootstrap_evidence", "workspace_creation_evidence_bundle") or {}
    lines = [
        "# Workspace Verification Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Verification",
        "",
        f"- Verified: **{report.get('verified')}**",
        f"- Structure valid: **{report.get('structure_valid')}**",
        f"- Template valid: **{report.get('template_valid')}**",
        f"- Repository healthy: **{report.get('repository_healthy')}**",
        f"- Governance metadata valid: **{report.get('governance_metadata_valid')}**",
        "",
        "## Missing artifacts",
        "",
        f"- Missing folders: `{report.get('missing_folders') or []}`",
        f"- Missing files: `{report.get('missing_files') or []}`",
        "",
        "## Evidence bundle",
        "",
        "```json",
        _json_block(bundle),
        "```",
    ]
    return "\n".join(lines)


def render_all_governed_workspace_creation_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "WORKSPACE_CREATION_REPORT.md": render_workspace_creation_report(payload),
        "REPOSITORY_BOOTSTRAP_REPORT.md": render_repository_bootstrap_report(payload),
        "WORKSPACE_VERIFICATION_REPORT.md": render_workspace_verification_report(payload),
    }


def render_governed_workspace_creation_repository_bootstrap(
    payload: dict[str, Any],
    *,
    focus: str = "workspace_creation_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("phase_6_workspace_dashboard") or [{}])[0].get(
        "workspace_creation_dashboard", {}
    )
    lines = [
        "# Governed Workspace Creation & Repository Bootstrap",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 334')}",
        "",
        "Workspace creation prepares governed delivery environments. Deployment authority remains separate.",
        "",
        f"Workspace status: **{dashboard.get('workspace_status', '—')}**",
        f"Repository status: **{dashboard.get('repository_status', '—')}**",
        f"Template status: **{dashboard.get('template_status', '—')}**",
        f"Verification status: **{dashboard.get('verification_status', '—')}**",
        f"Handoff ready: **{dashboard.get('handoff_ready', False)}**",
        "",
    ]

    if focus == "repository_bootstrap_report":
        report = (sections.get("phase_2_repository_bootstrap") or [{}])[0].get(
            "repository_bootstrap_report", {}
        )
        lines.extend(
            [
                "## Repository bootstrap",
                "",
                f"Decision approve: **{report.get('workspace_decision_approve')}**",
                f"Bootstrap executed: **{report.get('bootstrap_executed')}**",
                f"Supported templates: `{', '.join(report.get('supported_templates') or [])}`",
                "",
            ]
        )
    elif focus == "workspace_creation_dashboard":
        registry = (sections.get("phase_1_workspace_registry") or [{}])[0].get("workspace_registry", {})
        lines.extend(
            [
                "## Workspace registry",
                "",
                f"Registered workspaces: **{registry.get('entry_count', 0)}**",
                "",
            ]
        )
        for entry in (registry.get("entries") or [])[:5]:
            lines.append(
                f"- **{entry.get('workspace_name')}** ({entry.get('template_id')}): "
                f"`{entry.get('local_workspace_path')}`"
            )
        lines.append("")

    templates = (sections.get("phase_3_project_template_registry") or [{}])[0].get(
        "project_template_registry", {}
    )
    lines.extend(["## Approved templates", ""])
    for row in templates.get("templates") or []:
        lines.append(f"- **{row.get('template_id')}** — {row.get('display_name')} ({row.get('stack')})")
    lines.append("")
    return "\n".join(lines)
