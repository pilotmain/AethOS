# SPDX-License-Identifier: Apache-2.0
"""FIX 138 — Markdown renderer for governed rerun plan (chat)."""

from __future__ import annotations

from typing import Any


def render_governed_rerun_plan(plan: dict[str, Any]) -> str:
    elig = plan.get("eligibility") or {}
    replay_plan = plan.get("replay_derived_plan") or {}
    lines = [
        "# Governed Rerun Plan (FIX 138 — planning only)",
        "",
        f"- session_id: `{plan.get('session_id', '')}`",
        f"- plan_id: `{plan.get('plan_id') or 'none'}`",
        f"- correlation_id: `{plan.get('correlation_id', '')}`",
        f"- eligible (planning): **{elig.get('eligible_for_planning', False)}**",
        f"- eligible (execution): **{elig.get('eligible_for_execution', False)}** _(always false in FIX 138)_",
        "",
        elig.get("summary", ""),
        "",
        "## Replay-derived target",
        "",
        f"- step_index: **{replay_plan.get('target_step_index', '—')}**",
        f"- action: `{replay_plan.get('target_action', '')}`",
        f"- would_replay_from gate: `{replay_plan.get('would_replay_from', '')}`",
        f"- link_key: `{replay_plan.get('target_link_key', '')}`",
        "",
        "## Blast radius",
        "",
    ]
    br = plan.get("blast_radius") or {}
    lines.append(f"- risk_tier: **{br.get('risk_tier', '—')}**")
    for key, val in (br.get("blast_radius") or {}).items():
        lines.append(f"- {key}: {val}")
    lines.extend(["", "## Dependencies", ""])
    for dep in plan.get("dependencies") or []:
        lines.append(f"- `{dep.get('kind', '')}` — {dep.get('detail') or dep.get('stage', '')}")

    stale = plan.get("stale_state") or {}
    lines.extend(["", "## Stale-state detection", "", f"- stale: **{stale.get('is_stale', False)}**"])
    for sig in stale.get("signals") or []:
        lines.append(f"  - {sig.get('signal')}: {sig.get('detail')}")

    lines.extend(["", "## Rollback posture", ""])
    rb = plan.get("rollback_posture") or {}
    for key in ("workspace_rollback", "autonomous_rollback", "snapshot_required"):
        lines.append(f"- {key}: {rb.get(key, '—')}")

    lines.extend(["", "## Required approvals (if recovery needed)", ""])
    for row in plan.get("required_approvals") or []:
        lines.append(
            f"- `{row.get('gate_id')}` severity={row.get('severity')} "
            f"ui_eligible={row.get('ui_eligible')} mode={row.get('execution_mode')}"
        )

    lines.extend(["", "## Rerun blockers", ""])
    for b in plan.get("rerun_blockers") or []:
        lines.append(f"- **{b.get('code', '')}**: {b.get('detail', '')}")

    preview = plan.get("mutation_preview") or {}
    lines.extend(
        [
            "",
            "## Mutation preview (hypothetical)",
            "",
            f"- execution_enabled: **{preview.get('execution_enabled', False)}**",
            f"- stages if rerun executed later: {', '.join(preview.get('hypothetical_stages_if_rerun_executed_later') or []) or 'none'}",
            "",
            "## Exact phrases (not executable in FIX 138)",
            "",
        ]
    )
    for phrase in plan.get("exact_rerun_phrases") or []:
        lines.append(f"- [{phrase.get('kind', '')}] `{phrase.get('phrase', '')}` — _{phrase.get('note', '')}_")

    lines.extend(
        [
            "",
            "_No rerun was executed. This is a planning artifact only._",
            f"`{plan.get('invariant', '')}`",
        ]
    )
    return "\n".join(lines)
