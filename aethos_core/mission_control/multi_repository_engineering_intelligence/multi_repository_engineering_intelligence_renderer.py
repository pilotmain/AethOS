# SPDX-License-Identifier: Apache-2.0
"""FIX 260 — multi-repository engineering intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_multi_repository_engineering_intelligence(payload: dict[str, Any]) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("portfolio_engineering_dashboard") or [{}])[0]
    summary = dict(dashboard.get("portfolio_summary") or {})
    health_rows = list(dashboard.get("repository_health_rows") or sections.get("engineering_health_scores") or [])
    deps = list(sections.get("cross_repository_dependency_map") or [])
    program = list(sections.get("program_delivery_visibility") or [])

    lines = [
        "# Multi-Repository Engineering Intelligence",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 260')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "## Portfolio summary",
        "",
        f"- Portfolio health score: **{summary.get('portfolio_engineering_health_score', '—')}** "
        f"({summary.get('portfolio_health_tier', '—')})",
        f"- Conditionally trusted: {summary.get('conditionally_trusted_count', 0)}",
        f"- Unproven: {summary.get('unproven_count', 0)}",
        "",
        "## Repository health",
        "",
        "| Repository | Trust | Health score | Tier | Throughput |",
        "| --- | --- | --- | --- | --- |",
    ]

    for row in health_rows:
        lines.append(
            f"| {row.get('display_name', row.get('repository'))} | "
            f"{row.get('trust_state', '—')} | "
            f"{row.get('engineering_health_score', '—')} | "
            f"{row.get('engineering_health_tier', '—')} | "
            f"{row.get('throughput_score', '—')} |"
        )

    lines.extend(["", "## Cross-repository dependencies (advisory)", ""])
    for link in deps[:12]:
        src = link.get("source_repository") or "—"
        tgt = link.get("target_repository") or "—"
        lines.append(f"- **{src}** → **{tgt}** ({link.get('relationship', 'advisory')})")

    lines.extend(["", "## Program delivery visibility", ""])
    for row in program:
        lines.append(
            f"- **{row.get('display_name', row.get('repository'))}** — "
            f"{row.get('program_visibility', 'unproven')} · "
            f"live evidence: {', '.join(row.get('live_evidence_stages') or []) or 'none'}"
        )

    lines.extend(
        [
            "",
            "## Authority",
            "",
            "Portfolio intelligence is advisory only. "
            "Cross-repository authority, program delivery authority, merge, deploy, and provider mutation remain **false**.",
        ]
    )
    return "\n".join(lines)
