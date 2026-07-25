# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_H1 / FIX 358 — render strategic direction deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_strategic_direction_report(payload: dict[str, Any]) -> str:
    metrics = payload.get("metrics") or {}
    baseline = _section(payload, "phase_1_strategic_baseline_registry", "strategic_baseline_registry") or {}
    lines = [
        "# Strategic Direction Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_H1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 358')}",
        "",
        "## Core principle",
        "",
        "Strategic direction intelligence evaluates options. **Strategic direction intelligence ≠ strategic authority.**",
        "",
        f"- Growth potential score: **{metrics.get('growth_potential_score')}**",
        f"- Strategic leverage score: **{metrics.get('strategic_leverage_score')}**",
        f"- Leading outcome category: **{metrics.get('leading_outcome_category')}**",
        f"- G4 readiness level: **{(baseline.get('g4_readiness_maturity') or {}).get('platform_maturity_level')}**",
        f"- Strategic authority: **{payload.get('strategic_authority')}**",
    ]
    return "\n".join(lines)


def render_next_growth_options_report(payload: dict[str, Any]) -> str:
    growth = _section(payload, "phase_2_growth_path_analysis", "growth_path_report") or {}
    product = _section(payload, "phase_3_product_expansion_analysis", "product_expansion_report") or {}
    lines = [
        "# Next Growth Options Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Highest opportunity path: **{growth.get('highest_opportunity_path')}**",
        f"- Growth paths evaluated: **{growth.get('growth_opportunities_evaluated')}**",
        f"- Product expansion areas: **{len(product.get('expansion_areas') or [])}**",
        f"- Strategy execution performed: **{growth.get('strategy_execution_performed')}**",
        f"- Roadmap mutation performed: **{product.get('roadmap_mutation_performed')}**",
    ]
    for path in growth.get("growth_paths") or []:
        lines.append(
            f"- {path.get('path_id')}: opportunity **{path.get('opportunity_score')}**"
        )
    return "\n".join(lines)


def render_strategic_tradeoff_analysis(payload: dict[str, Any]) -> str:
    tradeoffs = _section(payload, "phase_6_strategic_tradeoff_analysis", "strategic_tradeoff_report") or {}
    metrics = payload.get("metrics") or {}
    lines = [
        "# Strategic Tradeoff Analysis",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Execution risk score: **{metrics.get('execution_risk_score')}**",
        f"- Confidence score: **{metrics.get('confidence_score')}**",
        f"- Opportunity score: **{metrics.get('opportunity_score')}**",
        f"- Automatic prioritization performed: **{payload.get('automatic_prioritization')}**",
        "",
        "## Outcome tradeoffs",
        "",
    ]
    for item in tradeoffs.get("tradeoffs") or []:
        lines.append(
            f"- **{item.get('outcome_category')}**: impact **{item.get('impact')}**, "
            f"risk **{item.get('risk')}**, effort **{item.get('effort')}**, confidence **{item.get('confidence')}**"
        )
    return "\n".join(lines)


def render_all_strategic_direction_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "STRATEGIC_DIRECTION_REPORT.md": render_strategic_direction_report(payload),
        "NEXT_GROWTH_OPTIONS_REPORT.md": render_next_growth_options_report(payload),
        "STRATEGIC_TRADEOFF_ANALYSIS.md": render_strategic_tradeoff_analysis(payload),
    }


def render_strategic_direction_next_growth_decision_program(
    payload: dict[str, Any],
    *,
    focus: str = "strategic_direction_dashboard",
) -> str:
    metrics = payload.get("metrics") or {}
    lines = [
        "# Strategic Direction & Next-Growth Decision Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_H1')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 358')}",
        "",
        f"Growth potential: **{metrics.get('growth_potential_score')}** · "
        f"Leverage: **{metrics.get('strategic_leverage_score')}** · "
        f"Leading outcome: **{metrics.get('leading_outcome_category')}**",
        "",
        "## Operator commands",
        "",
        "- `strategic direction note: ...`",
        "- `strategic direction review approve: ...`",
        "- `show strategic direction dashboard`",
        "",
    ]
    return "\n".join(lines)
