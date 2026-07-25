# SPDX-License-Identifier: Apache-2.0
"""FIX 155 — Markdown renderer for governance evolution."""

from __future__ import annotations

from typing import Any


def render_governance_evolution(evolution: dict[str, Any]) -> str:
    sections = evolution.get("sections") or {}
    scoring = sections.get("institutional_continuity_scoring") or {}

    lines = [
        "# Governance Evolution + Institutional Continuity (FIX 155 — institutional temporal cognition)",
        "",
        f"- session_id: `{evolution.get('session_id', '')}`",
        f"- evolution records: **{evolution.get('evolution_record_count', 0)}**",
        f"- institutional continuity score: **{scoring.get('continuity_score', '—')}** ({scoring.get('continuity_label', '')})",
        f"- autonomous governance evolution: **{evolution.get('autonomous_governance_evolution_enabled', False)}** _(always false)_",
        f"- automatic doctrine migration: **{evolution.get('automatic_doctrine_migration_enabled', False)}** _(always false)_",
        "",
        evolution.get("invariant", ""),
        "",
        "_Institutional temporal governance cognition — recommendation-only, never autonomous evolution._",
        "",
    ]

    for title, key in (
        ("Doctrine era tracking", "doctrine_era_tracking"),
        ("Governance generation lineage", "governance_generation_lineage"),
        ("Institutional transition analysis", "institutional_transition_analysis"),
        ("Freeze-era continuity", "freeze_era_continuity"),
        ("Governance maturity progression", "governance_maturity_progression"),
        ("Long-horizon drift analysis", "long_horizon_drift_analysis"),
        ("Constitutional epoch comparison", "constitutional_epoch_comparison"),
        ("Governance migration reasoning", "governance_migration_reasoning"),
        ("Historical governance narrative reconstruction", "historical_governance_narrative_reconstruction"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("epoch_id") or item.get("era_id"):
                label = item.get("epoch_id") or item.get("era_id")
                desc = item.get("description") or item.get("doctrine_version") or item.get("fix_range", "")
                lines.append(f"- **{label}**: {desc}")
            elif item.get("generation_id"):
                lines.append(f"- gen `{item.get('generation_id')}` (depth {item.get('lineage_depth')}): {item.get('description')}")
            elif item.get("transition_id"):
                lines.append(
                    f"- **{item.get('transition_id')}** {item.get('from_era')} → {item.get('to_era')} "
                    f"[{item.get('status')}]: {item.get('detail')}"
                )
            elif item.get("continuity_id"):
                lines.append(f"- {item.get('detail')} (fixes={item.get('shipped_fix_count')})")
            elif item.get("stage"):
                mark = "✓" if item.get("achieved") else "·"
                current = " _(current)_" if item.get("current") else ""
                lines.append(f"- {mark} {item.get('stage')}{current}")
            elif item.get("comparison_id"):
                lines.append(f"- {item.get('from_epoch')} → {item.get('to_epoch')}: {item.get('transition_note')}")
            elif item.get("reasoning_id"):
                lines.append(f"- **{item.get('reasoning_id')}**: {item.get('detail')}")
            elif item.get("reconstruction_id"):
                lines.append(f"- timeline ({item.get('epoch_count')} epochs): {item.get('detail')}")
            elif item.get("drift_id"):
                lines.append(f"- [{item.get('horizon')}] {item.get('signal', item.get('drift_id'))}: {item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            elif item.get("narrative"):
                lines.append(f"- **{item.get('epoch')}**: {item.get('narrative')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.extend([f"## Institutional continuity scoring", ""])
    lines.append(f"- score **{scoring.get('continuity_score')}** ({scoring.get('continuity_label')})")
    lines.append(f"- {scoring.get('scoring_note', '')}")
    lines.append("")
    lines.append("_All evolution recommendations are `executable: false` and require human institutional sovereignty._")
    return "\n".join(lines)
