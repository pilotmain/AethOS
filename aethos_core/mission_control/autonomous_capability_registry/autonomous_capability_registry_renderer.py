# SPDX-License-Identifier: Apache-2.0
"""FIX 295 — autonomous capability registry renderer."""

from __future__ import annotations

from typing import Any


def render_autonomous_capability_registry(
    payload: dict[str, Any],
    *,
    focus: str = "dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("capability_dashboard") or [{}])[0]
    maturity = (sections.get("capability_maturity_dashboard") or [{}])[0]
    self_awareness = (sections.get("self_awareness_report") or [{}])[0]
    drift = (sections.get("capability_drift_report") or [{}])[0]
    registry = (sections.get("capability_registry") or [{}])[0]

    lines = [
        "# Autonomous Capability Registry & Self-Awareness",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 295')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        f"- Certified FIX modules: **{payload.get('certified_fix_count', 0)}**",
        f"- Registered capabilities: **{registry.get('capability_count', 0)}**",
        f"- Overall maturity: **{maturity.get('capability_maturity_tier', '—')}**",
        f"- Capability drift items: **{drift.get('drift_count', 0)}**",
        f"- Human capability review approved: **{payload.get('human_capability_review_approve', False)}**",
        "",
    ]

    if focus in {"self_awareness", "dashboard"}:
        lines.extend(["## Self-awareness", ""])
        for label, key in (
            ("What I can do", "what_can_you_do"),
            ("What I cannot do", "what_cant_you_do"),
            ("What is proven", "what_is_proven"),
            ("What is experimental", "what_is_experimental"),
            ("What is trusted", "what_is_trusted"),
            ("What is planned", "what_is_planned"),
        ):
            items = self_awareness.get(key) or []
            lines.append(f"**{label}**")
            for item in items[:5]:
                lines.append(f"- {item}")
            lines.append("")

    if focus in {"registry", "dashboard"}:
        lines.extend(["## Top capabilities", ""])
        for cap in (registry.get("capabilities") or [])[:8]:
            lines.append(
                f"- **{cap.get('name')}** [{cap.get('domain')}] — {cap.get('status')} "
                f"(maturity {cap.get('maturity_score', '—')})"
            )
        lines.append("")

    if focus == "maturity":
        lines.extend(
            [
                "## Capability maturity",
                "",
                f"- Capability maturity score: **{maturity.get('capability_maturity_score', '—')}**",
                f"- Evidence confidence score: **{maturity.get('evidence_confidence_score', '—')}**",
                f"- Trust confidence score: **{maturity.get('trust_confidence_score', '—')}**",
                f"- Operational readiness score: **{maturity.get('operational_readiness_score', '—')}**",
                "",
            ]
        )

    if focus == "drift":
        lines.extend(["## Capability drift", ""])
        for item in drift.get("drift_items") or []:
            lines.append(f"- **{item.get('drift_type')}**: {item.get('subject')} — {item.get('detail')}")
        lines.append("")

    provider_matrix = (sections.get("provider_capability_matrix") or [{}])[0]
    trust_matrix = (sections.get("repository_trust_matrix") or [{}])[0]
    lines.extend(["## Provider readiness", ""])
    for row in provider_matrix.get("providers") or []:
        lines.append(f"- **{row.get('provider')}**: {row.get('status')} ({row.get('readiness')})")

    lines.extend(["", "## Repository trust", ""])
    for row in trust_matrix.get("repositories") or []:
        lines.append(
            f"- **{row.get('display_name') or row.get('repository')}**: {row.get('trust_state', '—')}"
        )

    lines.extend(
        [
            "",
            "## Human capability review",
            "",
            "Record with:",
            "- `capability review approve: …`",
            "- `capability review hold/reject/defer: …`",
            "",
            "## Authority",
            "",
            "Capability awareness tracks platform evidence only. "
            "Self-authority granting, automatic promotion, and trust mutation remain **false**.",
        ]
    )
    return "\n".join(lines)
