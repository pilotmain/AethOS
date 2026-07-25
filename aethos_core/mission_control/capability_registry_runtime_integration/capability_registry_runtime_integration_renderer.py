# SPDX-License-Identifier: Apache-2.0
"""FIX 296 — capability registry runtime integration renderer."""

from __future__ import annotations

from typing import Any


def render_capability_registry_runtime_integration(payload: dict[str, Any]) -> str:
    sections = dict(payload.get("sections") or {})
    summary = (sections.get("capability_summary") or [{}])[0]
    domains = (sections.get("platform_capability_domains") or [{}])[0].get("domains") or {}
    proven = (sections.get("proven_capabilities") or [{}])[0]
    operational = (sections.get("operational_capabilities") or [{}])[0]
    experimental = (sections.get("experimental_capabilities") or [{}])[0]
    planned = (sections.get("planned_blocked_capabilities") or [{}])[0]
    provider_matrix = (sections.get("provider_capability_matrix") or [{}])[0]
    trust_matrix = (sections.get("repository_trust_matrix") or [{}])[0]
    authority = (sections.get("authority_boundaries") or [{}])[0]

    lines = [
        "# AethOS Capability Self-Awareness",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 296')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "## Capability summary",
        "",
        f"AethOS currently registers **{summary.get('capability_count', 0)}** platform capabilities "
        f"at maturity tier **{summary.get('overall_maturity_tier', '—')}**, composed from live FIX certifications, "
        "trust baselines, operator surfaces, pilot evidence, provider readiness, and runtime flags.",
        "",
        "## Platform capability domains",
        "",
    ]

    domain_titles = {
        "governance": "Governance",
        "software_delivery": "Governed software delivery",
        "operations": "Operations",
        "repository_intelligence": "Repository intelligence",
        "product_intelligence": "Product intelligence",
        "lifecycle_and_business_intelligence": "Lifecycle and business intelligence",
        "multi_tenant_platform_readiness": "Multi-tenant platform readiness",
        "provider_readiness": "Provider readiness",
        "limitations": "Limitations",
    }
    for key, title in domain_titles.items():
        items = domains.get(key) or []
        if not items:
            continue
        lines.append(f"**{title}**")
        for item in items[:6]:
            lines.append(f"- {item}")
        lines.append("")

    lines.extend(["## Proven capabilities", ""])
    for item in proven.get("items") or []:
        lines.append(f"- {item}")
    for repo in proven.get("trusted_repositories") or []:
        lines.append(f"- Trusted repository: {repo}")

    lines.extend(["", "## Operational capabilities", ""])
    for item in operational.get("items") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Experimental / expanding capabilities", ""])
    for item in experimental.get("items") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Planned / blocked capabilities", ""])
    for item in planned.get("items") or []:
        lines.append(f"- {item}")

    lines.extend(["", "## Provider capability matrix", ""])
    for row in provider_matrix.get("providers") or []:
        lines.append(f"- **{row.get('provider')}**: {row.get('status')} ({row.get('readiness')})")

    lines.extend(["", "## Repository trust matrix", ""])
    for row in trust_matrix.get("repositories") or []:
        lines.append(
            f"- **{row.get('display_name') or row.get('repository')}**: {row.get('trust_state', '—')}"
        )

    lines.extend(["", "## Authority boundaries", ""])
    for boundary in authority.get("boundaries") or []:
        lines.append(f"- {boundary}")

    lines.extend(
        [
            "",
            "Capability answering uses live evidence from FIX 295. Provider readiness is one section, not the whole answer.",
        ]
    )
    return "\n".join(lines)
