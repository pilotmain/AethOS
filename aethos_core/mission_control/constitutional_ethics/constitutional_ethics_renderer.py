# SPDX-License-Identifier: Apache-2.0
"""FIX 159 — Markdown renderer for constitutional ethics."""

from __future__ import annotations

from typing import Any


def render_constitutional_ethics(constitutional_ethics: dict[str, Any]) -> str:
    sections = constitutional_ethics.get("sections") or {}

    lines = [
        "# Constitutional Ethics + Institutional Moral Reasoning (FIX 159 — constitutional ethical cognition)",
        "",
        f"- session_id: `{constitutional_ethics.get('session_id', '')}`",
        f"- ethics records: **{constitutional_ethics.get('ethics_record_count', 0)}**",
        f"- autonomous moral authority: **{constitutional_ethics.get('autonomous_moral_authority_enabled', False)}** _(always false)_",
        f"- value enforcement authority: **{constitutional_ethics.get('value_enforcement_authority_enabled', False)}** _(always false)_",
        "",
        constitutional_ethics.get("invariant", ""),
        "",
        "_Constitutional ethical cognition — recommendation-only, never autonomous moral authority or value enforcement._",
        "",
    ]

    for title, key in (
        ("Constitutional ethics records", "constitutional_ethics_records"),
        ("Value-conflict reasoning", "value_conflict_reasoning"),
        ("Institutional moral tradeoff analysis", "institutional_moral_tradeoff_analysis"),
        ("Mission-vs-risk ethical tension analysis", "mission_vs_risk_ethical_tension_analysis"),
        ("Constitutional ethics continuity", "constitutional_ethics_continuity"),
        ("Long-horizon value preservation", "long_horizon_value_preservation"),
        ("Ethical ambiguity surfacing", "ethical_ambiguity_surfacing"),
        ("Institutional moral precedent analysis", "institutional_moral_precedent_analysis"),
        ("Constitutional value drift detection", "constitutional_value_drift_detection"),
        ("Ethical coherence scoring", "ethical_coherence_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("value_id"):
                lines.append(f"- **{item.get('value_id')}**: {item.get('statement')}")
            elif item.get("conflict_id"):
                lines.append(f"- **{item.get('conflict_id')}** ({item.get('severity')}): {item.get('description')}")
            elif item.get("tradeoff_id"):
                lines.append(f"- tradeoff `{item.get('tradeoff_id')}`: {item.get('detail')}")
            elif item.get("tension_id"):
                lines.append(f"- **{item.get('tension_id')}** ({item.get('tension_level')}): {item.get('detail')}")
            elif item.get("continuity_id") or item.get("preservation_id"):
                label = item.get("continuity_id") or item.get("preservation_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("ambiguity_id"):
                lines.append(f"- ambiguity `{item.get('ambiguity_id')}`: {item.get('detail')}")
            elif item.get("precedent_id"):
                lines.append(f"- **{item.get('precedent_id')}**: {item.get('precedent', item.get('content'))}")
            elif item.get("drift_id"):
                lines.append(f"- drift `{item.get('drift_id')}`: {item.get('detail')}")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('coherence_score')} label={item.get('coherence_label')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All ethics recommendations are `executable: false` and require human moral sovereignty._")
    return "\n".join(lines)
