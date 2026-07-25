# SPDX-License-Identifier: Apache-2.0
"""FIX 311 — public product experience renderer."""

from __future__ import annotations

from typing import Any


def render_public_product_experience(
    payload: dict[str, Any],
    *,
    focus: str = "public_product_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("public_product_dashboard") or [{}])[0]
    landing = (sections.get("public_landing_experience") or [{}])[0]

    lines = [
        "# Public Product Experience",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 311')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Public product experience ≠ platform authority. Explain and guide — never bypass governance.",
        "",
        f"Public product authority: **{payload.get('public_product_authority', False)}**",
        "",
    ]

    if focus in {"public_product_dashboard", "public_landing_experience"}:
        lines.extend(
            [
                "## What AethOS is",
                "",
                landing.get("headline", "Governed autonomous platform for software delivery and operations."),
                "",
                "## Why governance matters",
                "",
                *(f"- {item}" for item in landing.get("governance_points") or []),
                "",
            ]
        )

    if focus == "capability_explorer":
        explorer = (sections.get("capability_explorer") or [{}])[0]
        for bucket in ("proven", "experimental", "planned"):
            rows = explorer.get(bucket) or []
            if rows:
                lines.append(f"## {bucket.title()} capabilities")
                lines.append("")
                for row in rows[:8]:
                    lines.append(f"- **{row.get('label')}** ({row.get('status')})")
                lines.append("")

    if focus == "trust_explorer":
        explorer = (sections.get("trust_explorer") or [{}])[0]
        lines.extend(["## Trust baselines", ""])
        for baseline in explorer.get("baselines") or []:
            lines.append(
                f"- **{baseline.get('label')}** ({baseline.get('fix')}): "
                f"{baseline.get('evidence_summary')}"
            )
        lines.append("")

    if focus == "guided_product_tour":
        tour = (sections.get("guided_product_tour") or [{}])[0]
        for step in tour.get("steps") or []:
            lines.append(f"### {step.get('title')}")
            lines.append(step.get("detail", ""))
            lines.append("")

    if focus == "customer_journey_explorer":
        journey = (sections.get("customer_journey_explorer") or [{}])[0]
        for path in journey.get("paths") or []:
            lines.append(f"- **{path.get('title')}**: {path.get('detail')}")
        lines.append("")

    if focus == "public_readiness_explorer":
        readiness = (sections.get("public_readiness_explorer") or [{}])[0]
        lines.extend(
            [
                f"Overall launch status: **{readiness.get('overall_launch_status', '—')}**",
                "",
                "## Public limitations",
                "",
            ]
        )
        for item in readiness.get("public_limitations") or []:
            lines.append(f"- {item}")
        lines.append("")

    if focus == "public_education_center":
        education = (sections.get("public_education_center") or [{}])[0]
        for faq in education.get("faqs") or []:
            lines.append(f"**{faq.get('question')}**")
            lines.append(faq.get("answer", ""))
            lines.append("")

    if focus == "public_product_dashboard":
        coverage = dashboard.get("evidence_coverage") or {}
        lines.extend(
            [
                "## Unified public surface",
                "",
                f"Domains composed: **{coverage.get('domains_composed', 0)}** / **{coverage.get('domains_total', 10)}**",
                "",
                "## Getting started",
                "",
            ]
        )
        for item in dashboard.get("getting_started") or []:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "No provider mutation, governance bypass, or automatic onboarding. "
            "Use `public experience note:` and `public experience review approve:` for human review only.",
        ]
    )
    return "\n".join(lines)
