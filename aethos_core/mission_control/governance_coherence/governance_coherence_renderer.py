# SPDX-License-Identifier: Apache-2.0
"""FIX 153 — Markdown renderer for governance coherence."""

from __future__ import annotations

from typing import Any


def render_governance_coherence(coherence: dict[str, Any]) -> str:
    sections = coherence.get("sections") or {}
    integrity = sections.get("institutional_integrity_scoring") or {}

    lines = [
        "# Governance Coherence + Constitutional Integrity (FIX 153 — institutional coherence intelligence)",
        "",
        f"- session_id: `{coherence.get('session_id', '')}`",
        f"- coherence records: **{coherence.get('coherence_record_count', 0)}**",
        f"- institutional integrity score: **{integrity.get('integrity_score', '—')}** ({integrity.get('integrity_label', '')})",
        f"- autonomous governance correction: **{coherence.get('autonomous_governance_correction_enabled', False)}** _(always false)_",
        f"- self-healing governance: **{coherence.get('self_healing_governance_enabled', False)}** _(always false)_",
        "",
        coherence.get("invariant", ""),
        "",
        "_Institutional constitutional coherence intelligence — recommendation-only, never enforcement._",
        "",
    ]

    for title, key in (
        ("Doctrine/topology consistency analysis", "doctrine_topology_consistency_analysis"),
        ("Precedent drift detection", "precedent_drift_detection"),
        ("Governance contradiction surfacing", "governance_contradiction_surfacing"),
        ("Policy fragmentation analysis", "policy_fragmentation_analysis"),
        ("Governance principle alignment checks", "governance_principle_alignment_checks"),
        ("Cross-session doctrine coherence", "cross_session_doctrine_coherence"),
        ("Conflicting precedent clustering", "conflicting_precedent_clustering"),
        ("Trust-boundary consistency analysis", "trust_boundary_consistency_analysis"),
        ("Governance stability indicators", "governance_stability_indicators"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if key == "institutional_integrity_scoring":
            lines.append(f"- score **{integrity.get('integrity_score')}** ({integrity.get('integrity_label')})")
            lines.append(f"- {integrity.get('scoring_note', '')}")
            lines.append("")
            continue
        if not items:
            lines.append("_None detected._")
        for item in items:
            if item.get("principle_id"):
                lines.append(f"- **{item.get('principle_id')}** [{item.get('status')}]: aligned={item.get('aligned')}")
            elif item.get("integrity_score") is not None and item.get("indicator_id"):
                lines.append(
                    f"- **{item.get('indicator_id')}** stability={item.get('stability_label')} "
                    f"(integrity={item.get('integrity_score')}, contradictions={item.get('active_contradiction_count')})"
                )
            elif item.get("cluster_id"):
                lines.append(f"- cluster `{item.get('topic')}` ({item.get('precedent_count')} precedents): {item.get('detail')}")
            elif item.get("drift_id") or item.get("signal"):
                lines.append(f"- **{item.get('signal', item.get('drift_id'))}**: {item.get('detail')}")
            elif item.get("contradiction"):
                lines.append(f"- **{item.get('contradiction')}** ({item.get('severity', '')}): {item.get('detail')}")
            elif item.get("fragmentation_level"):
                lines.append(f"- fragmentation **{item.get('fragmentation_level')}**: {item.get('detail')}")
            elif item.get("status") and item.get("detail"):
                lines.append(f"- [{item.get('status')}] {item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All coherence recommendations are `executable: false` and require human governance sovereignty._")
    return "\n".join(lines)
