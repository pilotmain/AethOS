# SPDX-License-Identifier: Apache-2.0
"""FIX 305 — billing & entitlements foundation renderer."""

from __future__ import annotations

from typing import Any


def render_billing_entitlements_foundation(
    payload: dict[str, Any],
    *,
    focus: str = "billing_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("billing_dashboard") or [{}])[0]
    subscription = (sections.get("subscription_registry") or [{}])[0]
    entitlements = (sections.get("entitlement_registry") or [{}])[0]
    usage_limits = (sections.get("usage_limit_report") or [{}])[0]
    capability_matrix = (sections.get("capability_entitlement_matrix") or [{}])[0]
    readiness = (sections.get("billing_readiness_report") or [{}])[0]

    lines = [
        "# Billing & Entitlements Foundation",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 305')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Entitlements ≠ authority. Billing controls access — not governance.",
        "",
        "## Billing dashboard",
        "",
        f"Plan: **{dashboard.get('plan', 'FREE')}** (org plan: {dashboard.get('org_plan_raw', '—')})",
        f"Payment processing: **{payload.get('payment_processing_enabled', False)}**",
        "",
    ]

    if focus in {"billing_dashboard", "subscription_registry"}:
        lines.extend(
            [
                "## Subscription status",
                "",
                f"- Organization: **{subscription.get('organization_name', '—')}**",
                f"- Commercial plan: **{subscription.get('commercial_plan', 'FREE')}**",
                f"- Status: **{subscription.get('status', 'active')}**",
                f"- Trial: **{subscription.get('trial_status', 'none')}**",
                "",
            ]
        )

    if focus in {"billing_dashboard", "entitlement_registry"}:
        lines.extend(["## Entitlements", ""])
        for feature in entitlements.get("features") or []:
            lines.append(f"- {feature}")
        blocked = entitlements.get("enterprise_only_blocked") or []
        if blocked:
            lines.extend(["", "**Enterprise-only (not entitled):**", ""])
            for item in blocked:
                lines.append(f"- {item}")

    if focus in {"billing_dashboard", "usage_limit_report"}:
        lines.extend(["", "## Usage limits", ""])
        consumption = usage_limits.get("consumption") or {}
        for row in consumption.get("limits") or []:
            maximum = row.get("maximum")
            max_label = "unlimited" if maximum is None else str(maximum)
            lines.append(
                f"- **{row.get('metric')}**: {row.get('current')} / {max_label} "
                f"({'within limit' if row.get('within_limit') else 'over limit'})"
            )

    if focus == "billing_dashboard":
        lines.extend(["", "## Capability entitlement matrix", ""])
        for row in capability_matrix.get("plans") or []:
            lines.append(f"**{row.get('plan')}**")
            for cap in row.get("capabilities") or []:
                lines.append(f"- {cap}")
            lines.append("")

        lines.extend(["## Billing readiness", ""])
        lines.append(f"- Subscription status: **{readiness.get('subscription_status', 'active')}**")
        lines.append(f"- Payment processing enabled: **{readiness.get('payment_processing_enabled', False)}**")

        upgrades = dashboard.get("upgrade_opportunities") or []
        if upgrades:
            lines.extend(["", "## Upgrade opportunities (advisory only)", ""])
            for opp in upgrades:
                lines.append(f"- {opp.get('from_plan')} → {opp.get('to_plan')}")

    lines.extend(
        [
            "",
            "No payment collection or automatic plan mutation. Use `billing note:` and "
            "`billing review approve:` for human review records only.",
        ]
    )
    return "\n".join(lines)
