# SPDX-License-Identifier: Apache-2.0
"""FIX 322 — product-market fit intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_product_market_fit_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "product_market_fit_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "value_signal_registry":
        registry = (sections.get("value_signal_registry") or [{}])[0]
        lines = ["## Value signal registry", ""]
        for signal in registry.get("signals") or []:
            lines.append(f"- **{signal.get('category')}** ({signal.get('source')}): {signal.get('detail')}")
        return "\n".join(lines)

    if focus == "problem_solution_fit_report":
        report = (sections.get("problem_solution_fit_report") or [{}])[0]
        lines = ["## Problem-solution fit", "", "### Customer problems", ""]
        for item in report.get("customer_problems") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Product capabilities", ""])
        for item in report.get("product_capabilities") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "customer_value_realization_report":
        report = (sections.get("customer_value_realization_report") or [{}])[0]
        lines = ["## Customer value realization", "", "### Realized value", ""]
        for item in report.get("realized_value") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Unrealized value", ""])
        for item in report.get("unrealized_value") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Perceived value", ""])
        for item in report.get("perceived_value") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "capability_demand_report":
        report = (sections.get("capability_demand_report") or [{}])[0]
        lines = ["## Capability demand", "", "### Requested", ""]
        for item in report.get("requested_capabilities") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Adopted", ""])
        for item in report.get("adopted_capabilities") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Ignored", ""])
        for item in report.get("ignored_capabilities") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "retention_value_report":
        report = (sections.get("retention_value_report") or [{}])[0]
        lines = ["## Retention value", "", "### Capabilities driving retention", ""]
        for item in report.get("capabilities_driving_retention") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Journeys driving retention", ""])
        for item in report.get("journeys_driving_retention") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "expansion_value_report":
        report = (sections.get("expansion_value_report") or [{}])[0]
        lines = ["## Expansion value", "", "### Capabilities driving expansion", ""]
        for item in report.get("capabilities_driving_expansion") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Plan expansion paths", ""])
        for item in report.get("plan_expansion_paths") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "pmf_opportunity_registry":
        registry = (sections.get("pmf_opportunity_registry") or [{}])[0]
        lines = ["## PMF opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('category')})")
        lines.append("", "Recommendations only — no automatic product strategy.")
        return "\n".join(lines)

    if focus == "pmf_scorecard":
        scorecard = (sections.get("pmf_scorecard") or [{}])[0]
        lines = [
            "## Product-market fit scorecard",
            "",
            f"- Overall: **{scorecard.get('overall_level', 'UNKNOWN')}** ({scorecard.get('overall_score', 0)})",
            "",
        ]
        for dim, score in (scorecard.get("dimensions") or {}).items():
            level = (scorecard.get("dimension_levels") or {}).get(dim, "UNKNOWN")
            lines.append(f"- **{dim.title()}**: {level} ({score})")
        return "\n".join(lines)

    dashboard = (sections.get("product_market_fit_dashboard") or [{}])[0]
    lines = [
        "## Product-market fit dashboard",
        "",
        f"- Value signals: **{dashboard.get('value_signal_count', 0)}**",
        f"- Customer problems tracked: **{dashboard.get('customer_problem_count', 0)}**",
        f"- Realized / unrealized value: **{dashboard.get('realized_value_signals', 0)}** / **{dashboard.get('unrealized_value_signals', 0)}**",
        f"- Capabilities requested / adopted / ignored: **{dashboard.get('requested_capability_count', 0)}** / **{dashboard.get('adopted_capability_count', 0)}** / **{dashboard.get('ignored_capability_count', 0)}**",
        f"- PMF level: **{dashboard.get('pmf_overall_level', 'UNKNOWN')}** ({dashboard.get('pmf_overall_score', 0)})",
        f"- PMF opportunities: **{dashboard.get('pmf_opportunity_count', 0)}**",
        "",
        "## Privacy",
        "",
        "Product-market fit intelligence ≠ product strategy authority. Tenant isolation preserved.",
    ]
    return "\n".join(lines)
