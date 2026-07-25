# SPDX-License-Identifier: Apache-2.0
"""FIX 335 / EXECUTION_TRACK_2 — render code generation deliverables."""

from __future__ import annotations

import json
from typing import Any


def _json_block(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_code_generation_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    lines = [
        "# Code Generation Report",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 335')}",
        f"**Exported:** {payload.get('exported_at', '')}",
        "",
        "## Core principle",
        "",
        "Generated code is advisory until human review. **Code generation ≠ repository authority.**",
        "",
        "## Success criteria",
        "",
        f"- Files generated: **{success.get('files_generated')}**",
        f"- Tests generated: **{success.get('tests_generated')}**",
        f"- Documentation generated: **{success.get('documentation_generated')}**",
        f"- Changeset assembled: **{success.get('changeset_assembled')}**",
        f"- Readiness validated: **{success.get('readiness_validated')}**",
        f"- Track complete: **{success.get('track_complete')}**",
        "",
        "## Phase 1 — Requirement intake",
        "",
        "```json",
        _json_block(_section(payload, "phase_1_requirement_intake", "generation_request_registry")),
        "```",
        "",
        "## Phase 9 — Dashboard",
        "",
        "```json",
        _json_block(_section(payload, "phase_9_dashboard", "code_generation_dashboard")),
        "```",
        "",
        "## Non-goals",
        "",
    ]
    for item in payload.get("non_goals") or []:
        lines.append(f"- {item.replace('_', ' ')}")
    return "\n".join(lines)


def render_changeset_review_package(payload: dict[str, Any]) -> str:
    package = _section(payload, "phase_6_changeset_assembly", "changeset_review_package") or {}
    registry = _section(payload, "phase_6_changeset_assembly", "changeset_registry") or {}
    lines = [
        "# Changeset Review Package",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Review package",
        "",
        f"- Changeset ID: **{package.get('changeset_id', '—')}**",
        f"- Review status: **{package.get('review_status', 'PENDING')}**",
        f"- Git commit performed: **{package.get('git_commit_performed')}**",
        f"- Git push performed: **{package.get('git_push_performed')}**",
        f"- PR creation performed: **{package.get('pr_creation_performed')}**",
        "",
        "## New files",
        "",
        "```json",
        _json_block(package.get("new_files") or []),
        "```",
        "",
        "## Modified files",
        "",
        "```json",
        _json_block(package.get("modified_files") or []),
        "```",
        "",
        "## Generated tests",
        "",
        "```json",
        _json_block(package.get("generated_tests") or []),
        "```",
        "",
        "## Changeset registry",
        "",
        "```json",
        _json_block(registry),
        "```",
    ]
    return "\n".join(lines)


def render_generation_verification_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_7_verification", "generation_verification_report") or {}
    bundle = _section(payload, "phase_8_evidence", "generation_evidence_bundle") or {}
    lines = [
        "# Generation Verification Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "## Verification",
        "",
        f"- Verified: **{report.get('verified')}**",
        f"- Compilation ready: **{report.get('compilation_ready')}**",
        f"- Dependency consistent: **{report.get('dependency_consistent')}**",
        f"- Template compliant: **{report.get('template_compliant')}**",
        f"- Generation complete: **{report.get('generation_complete')}**",
        "",
        "## Missing files",
        "",
        f"`{report.get('missing_files') or []}`",
        "",
        "## Evidence bundle",
        "",
        "```json",
        _json_block(bundle),
        "```",
    ]
    return "\n".join(lines)


def render_all_governed_code_generation_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "CODE_GENERATION_REPORT.md": render_code_generation_report(payload),
        "CHANGESET_REVIEW_PACKAGE.md": render_changeset_review_package(payload),
        "GENERATION_VERIFICATION_REPORT.md": render_generation_verification_report(payload),
    }


def render_governed_code_generation_changeset_creation(
    payload: dict[str, Any],
    *,
    focus: str = "code_generation_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("phase_9_dashboard") or [{}])[0].get("code_generation_dashboard", {})
    lines = [
        "# Governed Code Generation & Changeset Creation",
        "",
        f"**Execution track:** {payload.get('execution_track_id', 'EXECUTION_TRACK_2')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 335')}",
        "",
        "Code generation produces reviewable changes inside approved workspaces. "
        "No commits, pushes, or PR creation.",
        "",
        f"Request status: **{dashboard.get('request_status', '—')}**",
        f"Generated files: **{dashboard.get('generated_file_status', '—')}**",
        f"Verification: **{dashboard.get('verification_status', '—')}**",
        f"Review status: **{dashboard.get('review_status', '—')}**",
        f"Handoff ready: **{dashboard.get('handoff_ready', False)}**",
        "",
    ]

    if focus == "changeset_review_package":
        package = (sections.get("phase_6_changeset_assembly") or [{}])[0].get("changeset_review_package", {})
        lines.extend(
            [
                "## Changeset review package",
                "",
                f"New files: **{len(package.get('new_files') or [])}**",
                f"Modified files: **{len(package.get('modified_files') or [])}**",
                f"Generated tests: **{len(package.get('generated_tests') or [])}**",
                "",
            ]
        )
        for path in (package.get("new_files") or [])[:8]:
            lines.append(f"- `{path}`")
        lines.append("")
    else:
        registry = (sections.get("phase_1_requirement_intake") or [{}])[0].get(
            "generation_request_registry", {}
        )
        lines.extend(
            [
                "## Generation requests",
                "",
                f"Recorded requests: **{registry.get('request_count', 0)}**",
                "",
            ]
        )

    stacks = (sections.get("phase_3_code_generation") or [{}])[0].get("generated_artifact_report", {})
    lines.extend(["## Supported stacks", ""])
    for stack in stacks.get("supported_stacks") or []:
        lines.append(f"- `{stack}`")
    lines.append("")
    return "\n".join(lines)
