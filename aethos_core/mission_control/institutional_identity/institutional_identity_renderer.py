# SPDX-License-Identifier: Apache-2.0
"""FIX 156 — Markdown renderer for institutional identity."""

from __future__ import annotations

from typing import Any


def render_institutional_identity(identity: dict[str, Any]) -> str:
    sections = identity.get("sections") or {}

    lines = [
        "# Institutional Identity + Constitutional Intent (FIX 156 — institutional identity cognition)",
        "",
        f"- session_id: `{identity.get('session_id', '')}`",
        f"- identity records: **{identity.get('identity_record_count', 0)}**",
        f"- autonomous institutional redirection: **{identity.get('autonomous_institutional_redirection_enabled', False)}** _(always false)_",
        f"- automatic constitutional rewriting: **{identity.get('automatic_constitutional_rewriting_enabled', False)}** _(always false)_",
        f"- governance sovereignty delegated: **{identity.get('governance_sovereignty_delegated', False)}** _(always false)_",
        "",
        identity.get("invariant", ""),
        "",
        "_Institutional identity cognition — recommendation-only, never autonomous redirection or mission authorship._",
        "",
    ]

    for title, key in (
        ("Institutional mission identity records", "institutional_mission_identity_records"),
        ("Constitutional intent lineage", "constitutional_intent_lineage"),
        ("Operational philosophy continuity", "operational_philosophy_continuity"),
        ("Governance purpose preservation", "governance_purpose_preservation"),
        ("Institutional value drift detection", "institutional_value_drift_detection"),
        ("Constitutional mission alignment", "constitutional_mission_alignment"),
        ("Organizational identity continuity", "organizational_identity_continuity"),
        ("Doctrine-purpose consistency", "doctrine_purpose_consistency"),
        ("Constitutional intent reconstruction", "constitutional_intent_reconstruction"),
        ("Institutional narrative continuity", "institutional_narrative_continuity"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("identity_id") and item.get("statement"):
                lines.append(f"- **{item.get('identity_id')}**: {item.get('statement')}")
            elif item.get("intent_id"):
                lines.append(f"- intent `{item.get('intent_id')}` (depth {item.get('lineage_depth')}): {item.get('statement')}")
            elif item.get("philosophy_id"):
                lines.append(f"- philosophy `{item.get('philosophy_id')}`: {item.get('statement')}")
            elif item.get("purpose_id"):
                lines.append(f"- purpose `{item.get('purpose_id')}` preserved={item.get('preserved')}: {item.get('purpose')}")
            elif item.get("drift_id"):
                lines.append(f"- drift `{item.get('drift_id')}`: {item.get('detail')}")
            elif item.get("alignment_id"):
                lines.append(f"- **{item.get('alignment_id')}** stage={item.get('current_maturity_stage')}: {item.get('detail')}")
            elif item.get("continuity_id"):
                lines.append(f"- **{item.get('continuity_id')}**: {item.get('detail')}")
            elif item.get("consistency_id"):
                lines.append(f"- consistency={item.get('consistent')}: {item.get('detail')}")
            elif item.get("reconstruction_id"):
                lines.append(f"- **{item.get('reconstruction_id')}**: {item.get('detail')}")
            elif item.get("narrative_continuity_id"):
                lines.append(f"- **{item.get('narrative_continuity_id')}**: {item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All identity recommendations are `executable: false` and require human governance sovereignty._")
    return "\n".join(lines)
