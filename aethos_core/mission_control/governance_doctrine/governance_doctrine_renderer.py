# SPDX-License-Identifier: Apache-2.0
"""FIX 151 — Markdown renderer for governance doctrine."""

from __future__ import annotations

from typing import Any


def render_governance_doctrine(doctrine: dict[str, Any]) -> str:
    sections = doctrine.get("sections") or {}
    versioning = sections.get("doctrine_versioning") or {}

    lines = [
        "# Governance Doctrine + Policy Charter (FIX 151 — institutional constitutionality)",
        "",
        f"- session_id: `{doctrine.get('session_id', '')}`",
        f"- current doctrine version: `{versioning.get('current_version', '—')}`",
        f"- amendment proposals: **{doctrine.get('amendment_proposal_count', 0)}**",
        f"- automatic policy mutation: **{doctrine.get('automatic_policy_mutation_enabled', False)}** _(always false)_",
        f"- autonomous doctrine evolution: **{doctrine.get('autonomous_doctrine_evolution_enabled', False)}** _(always false)_",
        "",
        doctrine.get("invariant", ""),
        "",
        "_Institutional governance constitutionality — proposals only, never self-modifying._",
        "",
    ]

    conflicts = sections.get("doctrine_conflict_detection") or []
    if conflicts:
        lines.extend(["## Doctrine conflict detection", ""])
        for c in conflicts:
            lines.append(f"- **{c.get('conflict', '—')}** ({c.get('severity', '')}): {c.get('detail', '')}")
        lines.append("")

    for title, key in (
        ("Governance charter records", "governance_charter_records"),
        ("Governance principle registry", "governance_principle_registry"),
        ("Institutional rule lineage", "institutional_rule_lineage"),
        ("Policy amendment proposals", "policy_amendment_proposals"),
        ("Governance precedent tracking", "governance_precedent_tracking"),
        ("Policy rationale history", "policy_rationale_history"),
        ("Policy freeze snapshots", "policy_freeze_snapshots"),
        ("Constitutional governance references", "constitutional_governance_references"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("principle_id"):
                lines.append(f"- **{item.get('principle_id')}**: {item.get('statement')}")
            elif item.get("fix") and item.get("reference"):
                lines.append(f"- `{item.get('fix')}` — {item.get('reference')}")
            elif item.get("charter_id") or item.get("title"):
                lines.append(f"- **{item.get('title', item.get('charter_id'))}**: {item.get('content', '')}")
            elif item.get("rule"):
                lines.append(f"- rule `{item.get('rule_id', '—')}`: {item.get('rule')}")
            elif item.get("content") and item.get("kind") == "policy_amendment_proposal":
                lines.append(
                    f"- **[proposed]** {item.get('content')} _(executable={item.get('executable', False)})_"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("policy"):
                lines.append(f"- {item.get('policy')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_All amendment proposals are `executable: false` and require human ratification._")
    return "\n".join(lines)
