# SPDX-License-Identifier: Apache-2.0
"""FIX 152 — Markdown renderer for governance policy interpretation."""

from __future__ import annotations

from typing import Any


def render_governance_policy_interpretation(interpretation: dict[str, Any]) -> str:
    sections = interpretation.get("sections") or {}

    lines = [
        "# Governance Policy Interpretation + Precedent Application (FIX 152 — institutional constitutional reasoning)",
        "",
        f"- session_id: `{interpretation.get('session_id', '')}`",
        f"- interpretation records: **{interpretation.get('interpretation_record_count', 0)}**",
        f"- automatic doctrine enforcement: **{interpretation.get('automatic_doctrine_enforcement_enabled', False)}** _(always false)_",
        f"- autonomous governance rulings: **{interpretation.get('autonomous_governance_rulings_enabled', False)}** _(always false)_",
        "",
        interpretation.get("invariant", ""),
        "",
        "_Institutional constitutional reasoning — interpretation assistance only, never enforcement._",
        "",
    ]

    consistency = sections.get("constitutional_consistency_checks") or []
    if consistency:
        lines.extend(["## Constitutional consistency checks", ""])
        for check in consistency:
            lines.append(f"- **{check.get('check_id', '—')}** [{check.get('status', '')}]: {check.get('detail', '')}")
        lines.append("")

    for title, key in (
        ("Doctrine interpretation records", "doctrine_interpretation_records"),
        ("Precedent application references", "precedent_application_references"),
        ("Conflict interpretation guidance", "conflict_interpretation_guidance"),
        ("Governance rationale mapping", "governance_rationale_mapping"),
        ("Doctrine-to-review linkage", "doctrine_to_review_linkage"),
        ("Precedent confidence scoring", "precedent_confidence_scoring"),
        ("Competing interpretation comparison", "competing_interpretation_comparison"),
        ("Governance ambiguity surfacing", "governance_ambiguity_surfacing"),
        ("Historical interpretation continuity", "historical_interpretation_continuity"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("principle_id") and item.get("interpretation"):
                lines.append(f"- **{item.get('principle_id')}**: {item.get('interpretation')}")
            elif item.get("precedent_content"):
                lines.append(f"- precedent `{item.get('precedent_record_id', '—')}`: {item.get('precedent_content')}")
            elif item.get("guidance"):
                lines.append(f"- **{item.get('guidance_id', '—')}**: {item.get('guidance')}")
            elif item.get("rationale"):
                lines.append(f"- {item.get('rationale_kind', 'rationale')}: {item.get('rationale')}")
            elif item.get("linkage_note"):
                lines.append(
                    f"- readiness `{item.get('readiness_recommendation', '—')}` ↔ doctrine `{item.get('doctrine_version', '—')}`: {item.get('linkage_note')}"
                )
            elif item.get("confidence_score") is not None:
                lines.append(
                    f"- `{item.get('precedent_id', '—')}` confidence **{item.get('confidence_score')}** ({item.get('confidence_label', '')})"
                )
            elif item.get("interpretation_count"):
                lines.append(
                    f"- **{item.get('interpretation_count')} competing views** — {item.get('detail', '')}"
                )
            elif item.get("ambiguous_terms"):
                lines.append(f"- ambiguity in `{item.get('source_record_id', '—')}`: {', '.join(item.get('ambiguous_terms', []))}")
            elif item.get("timeline"):
                lines.append(f"- timeline ({item.get('record_count', 0)} records): {len(item.get('timeline', []))} recent entries")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All interpretations are `executable: false` and require human governance ratification._")
    return "\n".join(lines)
