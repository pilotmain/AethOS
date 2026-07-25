# SPDX-License-Identifier: Apache-2.0
"""FIX 149 — Markdown renderer for governance collaboration workspace."""

from __future__ import annotations

from typing import Any


def _render_collab_records(items: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    if not items:
        lines.append("_None recorded._")
        return lines
    for item in items:
        if item.get("reviewer_name") and item.get("content"):
            role = item.get("reviewer_role") or "—"
            lines.append(f"- **{item.get('reviewer_name')}** ({role}): {item.get('content')}")
        elif item.get("reviewer_name"):
            lines.append(f"- **{item.get('reviewer_name')}** — role: {item.get('reviewer_role', '—')}")
        elif item.get("owner"):
            lines.append(f"- owner **{item.get('owner')}**: {item.get('content', '')}")
        elif item.get("signal"):
            lines.append(f"- {item.get('signal')}: {item.get('detail', '')}")
        elif item.get("reviewer_role") and item.get("participation_count") is not None:
            lines.append(
                f"- role `{item.get('reviewer_role')}` — {item.get('participation_count')} participation(s)"
            )
        else:
            lines.append(f"- {item}")
    return lines


def render_governance_collaboration(collaboration: dict[str, Any]) -> str:
    sections = collaboration.get("sections") or {}
    quorum = sections.get("quorum_aware_discussion") or {}
    graph = sections.get("decision_participation_graph") or {}

    lines = [
        "# Multi-Operator Governance Collaboration (FIX 149 — institutional continuity)",
        "",
        f"- session_id: `{collaboration.get('session_id', '')}`",
        f"- plan_id: `{collaboration.get('plan_id') or '—'}`",
        f"- collaboration records: **{collaboration.get('collaboration_record_count', 0)}**",
        f"- delegated execution authority: **{collaboration.get('delegated_execution_authority_enabled', False)}** _(always false)_",
        f"- automatic quorum approval: **{collaboration.get('automatic_quorum_approval_enabled', False)}** _(always false)_",
        "",
        collaboration.get("invariant", ""),
        "",
        "_Institutional collaborative governance — multi-operator continuity without autonomous decisions._",
        "",
        "## Quorum-aware discussion (advisory)",
        "",
        f"- advisory quorum: **{quorum.get('advisory_quorum_size', '—')}**",
        f"- unique reviewers acknowledged: **{quorum.get('unique_reviewers_acknowledged', 0)}**",
        f"- quorum advisory met: **{quorum.get('quorum_advisory_met', False)}** _(does not auto-approve)_",
        "",
        "## Decision participation graph",
        "",
        f"- nodes: **{graph.get('node_count', 0)}** · edges: **{graph.get('edge_count', 0)}**",
        "",
    ]

    for title, key in (
        ("Named reviewers", "named_reviewers"),
        ("Role-aware deliberation", "role_aware_deliberation"),
        ("Review ownership", "review_ownership"),
        ("Delegated review requests", "delegated_review_requests"),
        ("Reviewer assignments", "reviewer_assignments"),
        ("Reviewer acknowledgments", "reviewer_acknowledgments"),
        ("Governance handoff tracking", "governance_handoff_tracking"),
        ("Unresolved concern escalation", "unresolved_concern_escalation"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        lines.extend(_render_collab_records(items if isinstance(items, list) else []))
        lines.append("")

    lines.append(
        "_Collaboration records persist institutional continuity only — no merge, deploy, or quorum approval automation._"
    )
    return "\n".join(lines)
