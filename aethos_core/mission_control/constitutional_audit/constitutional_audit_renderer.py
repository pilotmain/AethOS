# SPDX-License-Identifier: Apache-2.0
"""FIX 160 — Markdown renderer for constitutional audit."""

from __future__ import annotations

from typing import Any


def render_constitutional_audit(constitutional_audit: dict[str, Any]) -> str:
    sections = constitutional_audit.get("sections") or {}

    lines = [
        "# Constitutional Audit + Public Accountability (FIX 160 — constitutional accountability cognition)",
        "",
        f"- session_id: `{constitutional_audit.get('session_id', '')}`",
        f"- audit records: **{constitutional_audit.get('audit_record_count', 0)}**",
        f"- autonomous disclosure: **{constitutional_audit.get('autonomous_disclosure_enabled', False)}** _(always false)_",
        f"- public communication authority: **{constitutional_audit.get('public_communication_authority_enabled', False)}** _(always false)_",
        "",
        constitutional_audit.get("invariant", ""),
        "",
        "_Constitutional accountability cognition — recommendation-only, never autonomous disclosure or governance enforcement._",
        "",
    ]

    for title, key in (
        ("Constitutional audit reports", "constitutional_audit_reports"),
        ("Traceable reasoning summaries", "traceable_reasoning_summaries"),
        ("Doctrine/ethics/existential linkage", "doctrine_ethics_existential_linkage"),
        ("Recommendation explanations", "recommendation_explanations"),
        ("Accountability records", "accountability_records"),
        ("Human-readable governance evidence bundles", "human_readable_governance_evidence_bundles"),
        ("Public-safe accountability summaries", "public_safe_accountability_summaries"),
        ("Internal vs external disclosure boundaries", "internal_vs_external_disclosure_boundaries"),
        ("Constitutional transparency scoring", "constitutional_transparency_scoring"),
        ("Audit trail integrity checks", "audit_trail_integrity_checks"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("layer_id"):
                lines.append(f"- **{item.get('layer_id')}** ({item.get('fix')}): {item.get('role')}")
            elif item.get("report_id") or item.get("bundle_id"):
                label = item.get("report_id") or item.get("bundle_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("explanation_id"):
                lines.append(f"- **{item.get('explanation_id')}**: {item.get('answer', item.get('detail'))}")
            elif item.get("boundary_id"):
                lines.append(f"- `{item.get('boundary_id')}`: {item.get('definition')}")
            elif item.get("score_id") or item.get("integrity_id"):
                label = item.get("score_id") or item.get("integrity_id")
                if item.get("transparency_score") is not None:
                    lines.append(
                        f"- **{label}**: score={item.get('transparency_score')} label={item.get('transparency_label')}"
                    )
                else:
                    lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("summary_id") or item.get("accountability_id") or item.get("summary_id"):
                label = item.get("summary_id") or item.get("accountability_id")
                lines.append(f"- **{label}**: {item.get('detail')}")
            elif item.get("linkage_id"):
                lines.append(f"- linkage `{item.get('linkage_id')}`: {item.get('detail')}")
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All audit outputs are `executable: false` — humans govern disclosure, approval, and enforcement._")
    return "\n".join(lines)
