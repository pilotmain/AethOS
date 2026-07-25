# SPDX-License-Identifier: Apache-2.0
"""FIX 158 — Markdown renderer for institutional existential risk."""

from __future__ import annotations

from typing import Any


def render_institutional_existential_risk(existential_risk: dict[str, Any]) -> str:
    sections = existential_risk.get("sections") or {}

    lines = [
        "# Institutional Existential Risk + Continuity Preservation (FIX 158 — existential continuity cognition)",
        "",
        f"- session_id: `{existential_risk.get('session_id', '')}`",
        f"- existential risk records: **{existential_risk.get('existential_risk_record_count', 0)}**",
        f"- autonomous self-preservation: **{existential_risk.get('autonomous_self_preservation_enabled', False)}** _(always false)_",
        f"- constitutional override authority: **{existential_risk.get('constitutional_override_authority_enabled', False)}** _(always false)_",
        "",
        existential_risk.get("invariant", ""),
        "",
        "_Institutional existential continuity cognition — recommendation-only, never autonomous self-preservation or constitutional override._",
        "",
    ]

    for title, key in (
        ("Constitutional continuity risk analysis", "constitutional_continuity_risk_analysis"),
        ("Institutional dependency concentration analysis", "institutional_dependency_concentration_analysis"),
        ("Governance collapse scenario modeling", "governance_collapse_scenario_modeling"),
        ("Mission identity erosion detection", "mission_identity_erosion_detection"),
        ("Sovereignty degradation analysis", "sovereignty_degradation_analysis"),
        ("Long-horizon institutional fragility indicators", "long_horizon_institutional_fragility_indicators"),
        ("Continuity preservation recommendations", "continuity_preservation_recommendations"),
        ("Civilization-scale dependency mapping", "civilization_scale_dependency_mapping"),
        ("Constitutional extinction-path analysis", "constitutional_extinction_path_analysis"),
        ("Institutional preservation scoring", "institutional_preservation_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("scenario_id"):
                lines.append(f"- **{item.get('scenario_id')}** ({item.get('severity')}): {item.get('description')}")
            elif item.get("path_id"):
                lines.append(f"- extinction path `{item.get('path_id')}`: {item.get('description')}")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('preservation_score')} label={item.get('preservation_label')}"
                )
            elif item.get("recommendation_id"):
                lines.append(f"- **{item.get('recommendation_id')}**: {item.get('recommendation')}")
            elif item.get("indicator_id"):
                lines.append(f"- `{item.get('indicator_id')}`: {item.get('description')}")
            elif item.get("risk_id") or item.get("concentration_id") or item.get("degradation_id"):
                label = item.get("risk_id") or item.get("concentration_id") or item.get("degradation_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("erosion_id"):
                lines.append(f"- erosion `{item.get('erosion_id')}`: {item.get('detail')}")
            elif item.get("mapping_id"):
                lines.append(f"- **{item.get('mapping_id')}**: {item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All existential risk recommendations are `executable: false` and require human institutional sovereignty._")
    return "\n".join(lines)
