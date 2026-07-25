# SPDX-License-Identifier: Apache-2.0
"""FIX 163 — Markdown renderer for constitutional synthesis."""

from __future__ import annotations

from typing import Any


def render_constitutional_synthesis(constitutional_synthesis: dict[str, Any]) -> str:
    sections = constitutional_synthesis.get("sections") or {}

    lines = [
        "# Constitutional Synthesis + Institutional Wisdom (FIX 163 — synthesis cognition)",
        "",
        f"- session_id: `{constitutional_synthesis.get('session_id', '')}`",
        f"- synthesis records: **{constitutional_synthesis.get('synthesis_record_count', 0)}**",
        f"- constitutional layer count: **{constitutional_synthesis.get('sources', {}).get('constitutional_layer_count', 0)}**",
        f"- autonomous constitutional decisions: **{constitutional_synthesis.get('autonomous_constitutional_decisions_enabled', False)}** _(always false)_",
        f"- doctrine enforcement: **{constitutional_synthesis.get('doctrine_enforcement_enabled', False)}** _(always false)_",
        "",
        constitutional_synthesis.get("invariant", ""),
        "",
        "_Constitutional synthesis cognition — recommendation-only, never autonomous decisions or constitutional authority._",
        "",
    ]

    for title, key in (
        ("Constitutional tension analysis", "constitutional_tension_analysis"),
        ("Constitutional tradeoff maps", "constitutional_tradeoff_maps"),
        ("Cross-dimensional synthesis", "cross_dimensional_synthesis"),
        ("Institutional wisdom signals", "institutional_wisdom_signals"),
        ("Inter-dimensional disagreement analysis", "inter_dimensional_disagreement_analysis"),
        ("Recurring constitutional tension tracking", "recurring_constitutional_tension_tracking"),
        ("Recurring institutional strength signals", "recurring_institutional_strength_signals"),
        ("Constitutional layer interaction map", "constitutional_layer_interaction_map"),
        ("Synthesis coherence scoring", "synthesis_coherence_scoring"),
        ("Institutional wisdom continuity", "institutional_wisdom_continuity"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("tension_id"):
                lines.append(f"- **{item.get('tension_id')}** ({item.get('dimension_a')} vs {item.get('dimension_b')}): {item.get('description')}")
            elif item.get("tradeoff_id"):
                lines.append(f"- tradeoff `{item.get('tradeoff_id')}`: {item.get('detail')}")
            elif item.get("layer_id") and item.get("fix"):
                lines.append(f"- `{item.get('layer_id')}` ({item.get('fix')})")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('coherence_score')} label={item.get('coherence_label')}"
                )
            elif item.get("synthesis_id") or item.get("wisdom_id") or item.get("strength_id"):
                label = item.get("synthesis_id") or item.get("wisdom_id") or item.get("strength_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("tracking_id") or item.get("continuity_id") or item.get("disagreement_id"):
                label = item.get("tracking_id") or item.get("continuity_id") or item.get("disagreement_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All synthesis outputs are `executable: false` — humans govern constitutional tradeoffs and authority._")
    return "\n".join(lines)
