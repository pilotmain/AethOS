# SPDX-License-Identifier: Apache-2.0
"""FIX 161 — Markdown renderer for constitutional legitimacy."""

from __future__ import annotations

from typing import Any


def render_constitutional_legitimacy(constitutional_legitimacy: dict[str, Any]) -> str:
    sections = constitutional_legitimacy.get("sections") or {}

    lines = [
        "# Constitutional Legitimacy + Institutional Trust (FIX 161 — constitutional legitimacy cognition)",
        "",
        f"- session_id: `{constitutional_legitimacy.get('session_id', '')}`",
        f"- legitimacy records: **{constitutional_legitimacy.get('legitimacy_record_count', 0)}**",
        f"- autonomous legitimacy enforcement: **{constitutional_legitimacy.get('autonomous_legitimacy_enforcement_enabled', False)}** _(always false)_",
        f"- public trust manipulation: **{constitutional_legitimacy.get('public_trust_manipulation_enabled', False)}** _(always false)_",
        "",
        constitutional_legitimacy.get("invariant", ""),
        "",
        "_Constitutional legitimacy cognition — recommendation-only, never autonomous legitimacy enforcement or trust manipulation._",
        "",
    ]

    for title, key in (
        ("Institutional trust continuity analysis", "institutional_trust_continuity_analysis"),
        ("Governance legitimacy indicators", "governance_legitimacy_indicators"),
        ("Stakeholder confidence reasoning", "stakeholder_confidence_reasoning"),
        ("Constitutional credibility drift detection", "constitutional_credibility_drift_detection"),
        ("Governance trust fragmentation analysis", "governance_trust_fragmentation_analysis"),
        ("Institutional confidence scoring", "institutional_confidence_scoring"),
        ("Legitimacy continuity tracking", "legitimacy_continuity_tracking"),
        ("Constitutional participation health", "constitutional_participation_health"),
        ("Governance transparency trust analysis", "governance_transparency_trust_analysis"),
        ("Institutional credibility reconstruction", "institutional_credibility_reconstruction"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("indicator_id"):
                lines.append(f"- **{item.get('indicator_id')}** ({item.get('strength')}): {item.get('description')}")
            elif item.get("dimension_id"):
                lines.append(f"- `{item.get('dimension_id')}`: {item.get('description')}")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('confidence_score')} label={item.get('confidence_label')}"
                )
            elif item.get("drift_id"):
                lines.append(f"- drift `{item.get('drift_id')}`: {item.get('detail')}")
            elif item.get("fragmentation_id") or item.get("health_id") or item.get("analysis_id"):
                label = item.get("fragmentation_id") or item.get("health_id") or item.get("analysis_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("continuity_id") or item.get("tracking_id") or item.get("reconstruction_id"):
                label = item.get("continuity_id") or item.get("tracking_id") or item.get("reconstruction_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All legitimacy recommendations are `executable: false` — humans govern trust, credibility, and authority._")
    return "\n".join(lines)
