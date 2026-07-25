# SPDX-License-Identifier: Apache-2.0
"""FIX 162 — Markdown renderer for constitutional pluralism."""

from __future__ import annotations

from typing import Any


def render_constitutional_pluralism(constitutional_pluralism: dict[str, Any]) -> str:
    sections = constitutional_pluralism.get("sections") or {}

    lines = [
        "# Constitutional Pluralism + Governance Perspective (FIX 162 — constitutional pluralism cognition)",
        "",
        f"- session_id: `{constitutional_pluralism.get('session_id', '')}`",
        f"- pluralism records: **{constitutional_pluralism.get('pluralism_record_count', 0)}**",
        f"- authoritative worldview selection: **{constitutional_pluralism.get('authoritative_worldview_selection_enabled', False)}** _(always false)_",
        f"- autonomous constitutional arbitration: **{constitutional_pluralism.get('autonomous_constitutional_arbitration_enabled', False)}** _(always false)_",
        "",
        constitutional_pluralism.get("invariant", ""),
        "",
        "_Constitutional pluralism cognition — recommendation-only, never authoritative worldview selection or ideological alignment._",
        "",
    ]

    for title, key in (
        ("Governance perspective mapping", "governance_perspective_mapping"),
        ("Constitutional worldview coexistence analysis", "constitutional_worldview_coexistence_analysis"),
        ("Institutional philosophy comparison", "institutional_philosophy_comparison"),
        ("Stakeholder perspective continuity", "stakeholder_perspective_continuity"),
        ("Constitutional pluralism tracking", "constitutional_pluralism_tracking"),
        ("Competing legitimacy interpretation analysis", "competing_legitimacy_interpretation_analysis"),
        ("Governance culture drift detection", "governance_culture_drift_detection"),
        ("Institutional perspective lineage", "institutional_perspective_lineage"),
        ("Constitutional disagreement mapping", "constitutional_disagreement_mapping"),
        ("Pluralistic coherence scoring", "pluralistic_coherence_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("perspective_id"):
                lines.append(f"- **{item.get('perspective_id')}** ({item.get('orientation')}): {item.get('description')}")
            elif item.get("philosophy_id"):
                lines.append(f"- `{item.get('philosophy_id')}`: {item.get('statement')}")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('coherence_score')} label={item.get('coherence_label')}"
                )
            elif item.get("coexistence_id") or item.get("interpretation_id") or item.get("lineage_id"):
                label = item.get("coexistence_id") or item.get("interpretation_id") or item.get("lineage_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("drift_id") or item.get("disagreement_id"):
                lines.append(f"- `{item.get('drift_id', item.get('disagreement_id'))}`: {item.get('detail')}")
            elif item.get("continuity_id") or item.get("tracking_id"):
                label = item.get("continuity_id") or item.get("tracking_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All pluralism recommendations are `executable: false` — humans govern perspective resolution and constitutional arbitration._")
    return "\n".join(lines)
