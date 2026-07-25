# SPDX-License-Identifier: Apache-2.0
"""FIX 250 — Markdown renderer for governed application generation."""

from __future__ import annotations

from typing import Any


def render_governed_application_generation(payload: dict[str, Any]) -> str:
    sections = payload.get("sections") or {}
    product = (sections.get("product_understanding_package") or [{}])[0]
    architecture = (sections.get("architecture_package") or [{}])[0]
    blueprint = (sections.get("repository_blueprint") or [{}])[0]
    backlog = (sections.get("delivery_backlog") or [{}])[0]
    readiness = (sections.get("generation_readiness_report") or [{}])[0]
    handoff = (sections.get("delivery_pipeline_handoff") or [{}])[0] if sections.get(
        "delivery_pipeline_handoff"
    ) else {}

    lines = [
        "# Governed Application Generation (FIX 250 — application_generation ≠ autonomous_authority)",
        "",
        f"- product: **{payload.get('product_name')}**",
        f"- application generation authority: **{payload.get('application_generation_authority', False)}** _(always false)_",
        f"- repository creation authority: **{payload.get('repository_creation_authority', False)}** _(always false)_",
        f"- current stage: **{payload.get('current_stage')}**",
        f"- human decision: **{payload.get('human_generation_decision') or 'pending'}**",
        "",
        payload.get("invariant", ""),
        "",
        "## Product Understanding",
        "",
        f"- PRD captured: **{product.get('present')}**",
        "",
        "## Architecture Package",
        "",
        f"- system: {architecture.get('system_architecture')}",
        f"- deployment: {architecture.get('deployment_architecture')}",
        "",
        "## Repository Blueprint",
        "",
        f"- branch strategy: **{blueprint.get('branch_strategy')}**",
        f"- modules: {', '.join(blueprint.get('modules') or [])}",
        "",
        "## Delivery Backlog",
        "",
        f"- epics: {', '.join(backlog.get('epics') or [])}",
        "",
        "## Generation Readiness",
        "",
        f"- readiness score: **{readiness.get('readiness_score', 0)}**",
        f"- ready for handoff: **{readiness.get('ready_for_delivery_pipeline_handoff')}**",
    ]

    blockers = readiness.get("outstanding_blockers") or []
    if blockers:
        lines.append(f"- blockers: {', '.join(blockers)}")

    if handoff:
        lines.extend(
            [
                "",
                "## Delivery Pipeline Handoff",
                "",
                f"- handoff id: `{handoff.get('handoff_id')}`",
                f"- entry: **{handoff.get('existing_pipeline_entry')}**",
                f"- executable: **{handoff.get('handoff_executable', False)}**",
            ]
        )

    lines.extend(
        [
            "",
            "_Planning only — feeds existing Plan → Patch → Verify → PR pipeline when approved._",
        ]
    )
    return "\n".join(lines)
