# SPDX-License-Identifier: Apache-2.0
"""FIX 157 — Markdown renderer for institutional external relations."""

from __future__ import annotations

from typing import Any


def render_institutional_external_relations(external_relations: dict[str, Any]) -> str:
    sections = external_relations.get("sections") or {}

    lines = [
        "# Institutional External Relations + Constitutional Boundary (FIX 157 — external-relations cognition)",
        "",
        f"- session_id: `{external_relations.get('session_id', '')}`",
        f"- external relations records: **{external_relations.get('external_relations_record_count', 0)}**",
        f"- autonomous external negotiation: **{external_relations.get('autonomous_external_negotiation_enabled', False)}** _(always false)_",
        f"- sovereignty delegation: **{external_relations.get('sovereignty_delegation_enabled', False)}** _(always false)_",
        "",
        external_relations.get("invariant", ""),
        "",
        "_Constitutional external-relations cognition — recommendation-only, never autonomous diplomacy or sovereignty delegation._",
        "",
    ]

    for title, key in (
        ("External provider relationship models", "external_provider_relationship_models"),
        ("Constitutional boundary definitions", "constitutional_boundary_definitions"),
        ("External trust classifications", "external_trust_classifications"),
        ("Ecosystem dependency lineage", "ecosystem_dependency_lineage"),
        ("External governance interaction policies", "external_governance_interaction_policies"),
        ("Provider sovereignty boundaries", "provider_sovereignty_boundaries"),
        ("Constitutional interoperability analysis", "constitutional_interoperability_analysis"),
        ("Institutional dependency risk analysis", "institutional_dependency_risk_analysis"),
        ("External influence drift detection", "external_influence_drift_detection"),
        ("Cross-system trust continuity", "cross_system_trust_continuity"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("provider_id"):
                lines.append(f"- **{item.get('provider_id')}** ({item.get('lane')}): {item.get('relationship_model')}")
            elif item.get("boundary_id") and item.get("definition"):
                lines.append(f"- **{item.get('boundary_id')}**: {item.get('definition')}")
            elif item.get("classification_id"):
                lines.append(f"- `{item.get('classification_id')}`: {item.get('description')}")
            elif item.get("dependency_id"):
                lines.append(f"- dependency `{item.get('provider')}` depth={item.get('lineage_depth')}")
            elif item.get("policy_id"):
                lines.append(f"- **{item.get('policy_id')}**: {item.get('policy')}")
            elif item.get("provider") and item.get("institutional_sovereignty_preserved") is not None:
                lines.append(
                    f"- `{item.get('provider')}` sovereignty_preserved={item.get('institutional_sovereignty_preserved')}"
                )
            elif item.get("analysis_id") or item.get("risk_id"):
                lines.append(f"- **{item.get('analysis_id', item.get('risk_id'))}**: {item.get('detail')}")
            elif item.get("influence_id"):
                lines.append(f"- influence `{item.get('influence_id')}`: {item.get('detail')}")
            elif item.get("continuity_id"):
                lines.append(f"- **{item.get('continuity_id')}**: {item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All external relations recommendations are `executable: false` and require human institutional sovereignty._")
    return "\n".join(lines)
