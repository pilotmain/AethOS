# SPDX-License-Identifier: Apache-2.0
"""FIX 303 — provider connection experience renderer."""

from __future__ import annotations

from typing import Any


def render_provider_connection_experience(
    payload: dict[str, Any],
    *,
    focus: str = "provider_connection_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("provider_connection_dashboard") or [{}])[0]
    github = (sections.get("github_connection_report") or [{}])[0]
    railway = (sections.get("railway_connection_report") or [{}])[0]
    vercel = (sections.get("vercel_connection_report") or [{}])[0]
    readiness = (sections.get("provider_connection_readiness_report") or [{}])[0]
    unlocks = (sections.get("provider_capability_unlock_matrix") or [{}])[0]
    trust = (sections.get("provider_trust_explanation") or [{}])[0]

    lines = [
        "# Provider Connection Experience",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 303')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Provider connection guidance ≠ provider mutation authority. Connect manually in Settings.",
        "",
        "## Provider connection dashboard",
        "",
        f"Connected providers: **{dashboard.get('connected_provider_count', 0)}** / **{len(dashboard.get('phase_1_providers') or [])}** (Phase 1).",
        "",
    ]

    if focus in {"provider_connection_dashboard", "provider_connection_readiness_report"}:
        lines.extend(["## Connection readiness", ""])
        for row in readiness.get("phase_1") or []:
            lines.append(
                f"- **{row.get('provider')}**: {row.get('readiness')} "
                f"(credentials={row.get('credentials_present')}, reachable={row.get('provider_reachable')})"
            )
        lines.extend(["", "**Phase 2 — PLANNED (no connection flow)**", ""])
        for row in readiness.get("phase_2_planned") or []:
            lines.append(f"- **{row.get('provider')}**: PLANNED — not available")

    if focus in {"provider_connection_dashboard", "provider_capability_unlock_matrix"}:
        lines.extend(["", "## Provider capability unlock matrix", ""])
        for row in unlocks.get("providers") or []:
            lines.append(f"**{row.get('provider')}**")
            for unlock in row.get("capability_unlocks") or []:
                lines.append(f"- {unlock}")
            lines.append("")

    if focus == "provider_connection_dashboard":
        lines.extend(["## GitHub connection report", ""])
        lines.append(f"- Readiness: **{github.get('connection_readiness', github.get('readiness', {}).get('readiness', '—'))}**")
        for unlock in github.get("capability_unlocks") or []:
            lines.append(f"- Unlocks: {unlock}")

        lines.extend(["", "## Railway connection report", ""])
        lines.append(f"- Readiness: **{railway.get('readiness', {}).get('readiness', '—')}**")
        for unlock in railway.get("capability_unlocks") or []:
            lines.append(f"- Unlocks: {unlock}")

        lines.extend(["", "## Vercel connection report", ""])
        lines.append(f"- Readiness: **{vercel.get('readiness', {}).get('readiness', '—')}**")
        for unlock in vercel.get("capability_unlocks") or []:
            lines.append(f"- Unlocks: {unlock}")

        lines.extend(["", "## Provider trust explanation", ""])
        for item in trust.get("why_permissions_are_needed") or []:
            lines.append(f"- {item}")
        for item in trust.get("what_aethos_cannot_access") or []:
            lines.append(f"- Cannot: {item}")

        for gap in dashboard.get("permission_gaps") or []:
            lines.extend(["", "## Permission gaps", ""])
            lines.append(f"- **{gap.get('provider')}**: {gap.get('gap')} — configure in {gap.get('setup_in')}")
            break

    lines.extend(
        [
            "",
            "Never paste secrets into chat. Use `provider connection note:` and "
            "`provider connection review approve:` for human review records only.",
        ]
    )
    return "\n".join(lines)
