# SPDX-License-Identifier: Apache-2.0
"""FIX 308 — payment integration readiness renderer."""

from __future__ import annotations

from typing import Any


def render_payment_integration_readiness(
    payload: dict[str, Any],
    *,
    focus: str = "payment_readiness_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("payment_readiness_dashboard") or [{}])[0]
    providers = (sections.get("payment_provider_registry") or [{}])[0]
    lifecycle = (sections.get("subscription_lifecycle_registry") or [{}])[0]
    events = (sections.get("billing_event_registry") or [{}])[0]
    analytics = (sections.get("commercial_analytics_dashboard") or [{}])[0]
    upgrades = (sections.get("upgrade_path_registry") or [{}])[0]
    monetization = (sections.get("usage_monetization_registry") or [{}])[0]
    governance = (sections.get("commercial_governance_report") or [{}])[0]

    lines = [
        "# Payment Integration Readiness",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 308')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Payment readiness ≠ payment processing. No charging, card storage, or provider API mutation.",
        "",
        "## Payment readiness dashboard",
        "",
        f"Provider readiness: **{dashboard.get('provider_readiness', '—')}**",
        f"Subscription readiness: **{dashboard.get('subscription_readiness', '—')}**",
        f"Invoice readiness: **{dashboard.get('invoice_readiness', '—')}**",
        f"Usage readiness: **{dashboard.get('usage_readiness', '—')}**",
        f"Payment processing: **{payload.get('payment_processing_enabled', False)}**",
        "",
    ]

    if focus in {"payment_readiness_dashboard", "payment_provider_registry"}:
        lines.extend(["## Payment provider registry", ""])
        for row in providers.get("providers") or []:
            lines.append(
                f"- **{row.get('provider')}**: {row.get('integration_status')} "
                f"(configured={row.get('configured')})"
            )
        lines.append("")

    if focus in {"payment_readiness_dashboard", "subscription_lifecycle_registry"}:
        lines.extend(
            [
                "## Subscription lifecycle",
                "",
                f"Current state: **{lifecycle.get('current_state', '—')}**",
            ]
        )
        for row in lifecycle.get("states") or []:
            if row.get("current_for_tenant"):
                lines.append(f"- Current: **{row.get('state')}**")
        lines.append("")

    if focus in {"payment_readiness_dashboard", "billing_event_registry"}:
        lines.extend(["## Billing events", ""])
        for row in events.get("events") or []:
            lines.append(f"- **{row.get('event_type')}**: modeled={row.get('modeled')} processed={row.get('processed')}")
        lines.append("")

    if focus in {"payment_readiness_dashboard", "commercial_analytics_dashboard"}:
        lines.extend(
            [
                "## Commercial analytics",
                "",
                f"Plan distribution: **{analytics.get('plan_distribution', {})}**",
                f"Trial adoption: **{analytics.get('trial_adoption', False)}**",
                "",
            ]
        )

    if focus in {"payment_readiness_dashboard", "upgrade_path_registry"}:
        lines.extend(["## Upgrade paths", ""])
        for row in upgrades.get("eligible_paths") or []:
            lines.append(f"- {row.get('from_plan')} → {row.get('to_plan')} (advisory only)")
        lines.append("")

    if focus == "payment_readiness_dashboard":
        lines.extend(["## Usage monetization", ""])
        for row in (monetization.get("categories") or [])[:5]:
            lines.append(f"- **{row.get('category')}**: {row.get('current_usage')} / {row.get('plan_limit', 'unlimited')}")

        lines.extend(["", "## Commercial governance", ""])
        for gap in governance.get("commercial_risks") or []:
            lines.append(f"- {gap.get('gap')} ({gap.get('severity')})")

    lines.extend(
        [
            "",
            "No payment collection or credit card storage. Use `payment readiness note:` and "
            "`payment readiness review approve:` for human review records only.",
        ]
    )
    return "\n".join(lines)
