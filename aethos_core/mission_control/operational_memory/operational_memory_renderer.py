# SPDX-License-Identifier: Apache-2.0
"""FIX 139 — Markdown renderer for operational memory graph."""

from __future__ import annotations

from typing import Any


def render_operational_memory_graph(graph: dict[str, Any]) -> str:
    g = graph.get("graph") or {}
    stats = g.get("stats") or {}
    lines = [
        "# Operational Memory Graph (FIX 139 — read-only)",
        "",
        f"- session_id: `{graph.get('session_id', '')}`",
        f"- plan_id: `{graph.get('plan_id') or 'none'}`",
        f"- correlation_id: `{graph.get('correlation_id', '')}`",
        f"- autonomous adaptation: **{graph.get('autonomous_adaptation_enabled', False)}** _(always false in FIX 139)_",
        "",
        graph.get("invariant", ""),
        "",
        "## Graph stats",
        "",
        f"- nodes: **{stats.get('node_count', 0)}** | edges: **{stats.get('edge_count', 0)}**",
    ]
    for kind, count in sorted((stats.get("nodes_by_kind") or {}).items()):
        lines.append(f"  - `{kind}`: {count}")

    lines.extend(["", "## Mission lineage", ""])
    for row in graph.get("mission_lineage") or []:
        lines.append(f"- **{row.get('stage')}** `{row.get('id')}` ({row.get('kind')})")

    lines.extend(["", "## Correlated executions", ""])
    correlated = graph.get("correlated_executions") or []
    if not correlated:
        lines.append("_No multi-execution correlation groups in current scope._")
    for row in correlated:
        lines.append(
            f"- `{row.get('operation', '')}` — {row.get('count', row.get('lifecycle_entries', 1))} "
            f"({row.get('correlation_basis', '')})"
        )

    lines.extend(["", "## Repeated failures", ""])
    for row in graph.get("repeated_failures") or []:
        lines.append(f"- `{row.get('signature', '')}` × **{row.get('occurrences', 0)}**")

    lines.extend(["", "## Historical blast radius", ""])
    br = graph.get("historical_blast_radius") or {}
    lines.append(f"- source: `{br.get('source', '')}`")
    if br.get("risk_tier"):
        lines.append(f"- risk_tier: **{br.get('risk_tier')}**")
    if br.get("blocker_count") is not None:
        lines.append(f"- blockers: **{br.get('blocker_count')}**")

    lines.extend(["", "## Recurring blockers", ""])
    for row in graph.get("recurring_blockers") or []:
        lines.append(f"- `{row.get('blocker', '')}` × **{row.get('occurrences', 0)}**")

    lines.extend(["", "## Cross-domain links", ""])
    for row in graph.get("cross_domain_links") or []:
        if row.get("kind") == "synthetic_correlation":
            lines.append(f"- {row.get('detail', '')}")
        else:
            lines.append(
                f"- `{row.get('kind')}` {row.get('source', '')} → {row.get('target', '')}"
                + (f" ({row.get('domain')})" if row.get("domain") else "")
            )

    lines.extend(["", "## Learning signals (observation only)", ""])
    for sig in graph.get("learning_signals") or []:
        lines.append(f"- **{sig.get('signal', '')}**: {sig.get('detail', '')}")

    sources = graph.get("sources") or {}
    lines.extend(
        [
            "",
            "## Sources composed",
            "",
            f"- evidence bundle: {sources.get('evidence_bundle', False)}",
            f"- job replay: {sources.get('job_replay', False)}",
            f"- rerun plan: {sources.get('rerun_plan', False)}",
            "",
            "_FIX 139 is read-only operational memory — no mutations, reruns, or autonomous adaptation._",
        ]
    )
    return "\n".join(lines)
