# SPDX-License-Identifier: Apache-2.0
"""FIX 302 — identity and access hardening renderer."""

from __future__ import annotations

from typing import Any


def render_identity_access_hardening(payload: dict[str, Any], *, focus: str = "authorization_dashboard") -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("authorization_dashboard") or [{}])[0]
    identity = (sections.get("identity_resolution_report") or [{}])[0]
    permission = (sections.get("permission_evaluation_report") or [{}])[0]
    boundary = (sections.get("tenant_boundary_audit") or [{}])[0]
    mission_control = (sections.get("mission_control_authorization_report") or [{}])[0]
    governance = (sections.get("governance_action_report") or [{}])[0]
    least_priv = (sections.get("least_privilege_report") or [{}])[0]
    session_trust = (sections.get("session_trust_report") or [{}])[0]

    lines = [
        "# Identity & Access Hardening",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 302')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Authorization enforcement ≠ authority escalation. Permissions are verified, never self-granted.",
        "",
        "## Authorization dashboard",
        "",
        f"User **{identity.get('user_id', '—')}** · Role **{identity.get('role', '—')}** "
        f"({identity.get('tenant_role_label', '—')}) · Org **{identity.get('organization_id', '—')}**",
        "",
    ]

    if focus in {"authorization_dashboard", "permission_evaluation"}:
        lines.extend(["## Permission evaluation", ""])
        for row in permission.get("evaluations") or []:
            status = "allowed" if row.get("allowed") else "denied"
            lines.append(f"- **{row.get('permission')}**: {status}")
            if row.get("reason"):
                lines.append(f"  - {row.get('reason')}")

    if focus in {"authorization_dashboard", "tenant_boundary_audit"}:
        lines.extend(["", "## Tenant boundary audit", ""])
        for row in boundary.get("audits") or []:
            access = "allowed" if row.get("access_allowed") else "blocked"
            trust = "allowed" if row.get("trust_read_allowed") else "blocked"
            lines.append(
                f"- **{row.get('target_organization_name')}** ({row.get('target_organization_id')}): "
                f"access {access}, trust read {trust}"
            )

    if focus in {"authorization_dashboard", "least_privilege_report"}:
        lines.extend(["", "## Least privilege analysis", ""])
        lines.append(f"Granted platform permissions: {', '.join(least_priv.get('granted_platform_permissions') or [])}")
        for key in ("unused_permissions", "excessive_permissions", "overlapping_permissions", "privilege_drift"):
            items = least_priv.get(key) or []
            if items:
                lines.append(f"**{key.replace('_', ' ').title()}**")
                for item in items:
                    lines.append(f"- {item}")

    if focus == "authorization_dashboard":
        lines.extend(["", "## Mission Control authorization", ""])
        for row in mission_control.get("protected_surfaces") or []:
            status = "protected" if row.get("allowed") else "denied"
            lines.append(
                f"- **{row.get('surface')}** requires `{row.get('required_permission')}` — {status}"
            )

        lines.extend(["", "## Governance action controls", ""])
        for row in governance.get("actions") or []:
            status = "allowed" if row.get("allowed") else "denied"
            lines.append(
                f"- **{row.get('action')}** requires `{row.get('required_permission')}` — {status}"
            )

        lines.extend(["", "## Session trust", ""])
        lines.append(f"- Session valid: **{session_trust.get('session_valid')}**")
        lines.append(f"- Membership valid: **{session_trust.get('membership_valid')}**")
        lines.append(f"- Authorization bypass enabled: **{dashboard.get('authorization_bypass_enabled')}**")

    lines.extend(
        [
            "",
            "Record review notes with `authorization note:` and decisions with "
            "`authorization review approve:` (or hold/reject/defer).",
        ]
    )
    return "\n".join(lines)
