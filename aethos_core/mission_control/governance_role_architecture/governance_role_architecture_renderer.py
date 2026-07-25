# SPDX-License-Identifier: Apache-2.0
"""FIX 150 — Markdown renderer for governance role architecture."""

from __future__ import annotations

from typing import Any


def render_governance_role_architecture(architecture: dict[str, Any]) -> str:
    sections = architecture.get("sections") or {}
    quorum = sections.get("quorum_role_composition_rules") or {}

    lines = [
        "# Governance Role Architecture + Trust Boundaries (FIX 150 — institutional topology)",
        "",
        f"- session_id: `{architecture.get('session_id', '')}`",
        f"- plan_id: `{architecture.get('plan_id') or '—'}`",
        f"- trust zones: {architecture.get('trust_zones', [])}",
        f"- delegated execution authority: **{architecture.get('delegated_execution_authority_enabled', False)}** _(always false)_",
        f"- autonomous role elevation: **{architecture.get('autonomous_role_elevation_enabled', False)}** _(always false)_",
        "",
        architecture.get("invariant", ""),
        "",
        "_Institutional governance topology — roles and trust boundaries, not execution authority._",
        "",
        "## Quorum role composition (advisory)",
        "",
        f"- required roles: {quorum.get('required_roles', [])}",
        f"- advisory quorum: **{quorum.get('advisory_quorum_size', '—')}**",
        f"- current acknowledgments: {quorum.get('current_acknowledgments', 0)}",
        f"- automatic quorum approval: **{quorum.get('automatic_quorum_approval', False)}**",
        "",
    ]

    for title, key in (
        ("Governance role taxonomy", "governance_role_taxonomy"),
        ("Trust boundary modeling", "trust_boundary_modeling"),
        ("Role capability matrix", "role_capability_matrix"),
        ("Escalation path definitions", "escalation_path_definitions"),
        ("Separation-of-duty policies", "separation_of_duty_policies"),
        ("Review authority scopes", "review_authority_scopes"),
        ("Governance delegation boundaries", "governance_delegation_boundaries"),
        ("Operator trust zones", "operator_trust_zones"),
        ("Institutional responsibility maps", "institutional_responsibility_maps"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_No signals in this section._")
        for item in items:
            if item.get("role") and item.get("can"):
                lines.append(f"- **{item.get('role')}** — can: {item.get('can')}; cannot: {item.get('cannot')}")
            elif item.get("from_zone"):
                lines.append(
                    f"- `{item.get('from_zone')}` → `{item.get('to_zone')}`: {item.get('boundary')} "
                    f"(human required={item.get('crossing_requires_human_authority')})"
                )
            elif item.get("from_role"):
                lines.append(f"- {item.get('from_role')} → {item.get('to_role')} ({item.get('kind', '')})")
            elif item.get("policy"):
                lines.append(f"- {item.get('policy')} _(enforced={item.get('enforced')})_")
            elif item.get("delegation_type"):
                lines.append(
                    f"- **{item.get('delegation_type')}**: allowed={item.get('allowed')} — {item.get('detail', '')}"
                )
            elif item.get("operator") or item.get("trust_zone"):
                lines.append(
                    f"- operator `{item.get('operator') or '—'}` — zone `{item.get('trust_zone')}` "
                    f"(max authority: {item.get('max_authority', '—')})"
                )
            elif item.get("responsible_party"):
                lines.append(f"- **{item.get('responsible_party')}**: {item.get('responsibility', '')}")
            elif item.get("scope"):
                lines.append(
                    f"- **{item.get('role')}** — scope `{item.get('scope')}` ({item.get('authority_type')})"
                )
            else:
                role = item.get("role")
                count = item.get("observed_count")
                if role is not None:
                    lines.append(f"- `{role}` — observed: {count} operator(s)")
                else:
                    lines.append(f"- {item}")
        lines.append("")

    lines.append("_Topology is read-only — no role elevation, auto-approval, or policy mutation._")
    return "\n".join(lines)
