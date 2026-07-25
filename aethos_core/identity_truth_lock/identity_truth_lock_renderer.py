# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — identity truth lock markdown renderer."""

from __future__ import annotations

from typing import Any


def render_identity_truth_lock_markdown(*, payload: dict[str, Any], focus: str = "identity_dashboard") -> str:
    sections = payload.get("sections") or {}
    if focus == "identity_dashboard":
        dashboard = sections.get("identity_dashboard") or {}
        validation = sections.get("identity_truth_validation_report") or {}
        lines = [
            "## Identity dashboard",
            "",
            f"- Platform: **{dashboard.get('platform', 'AethOS')}**",
            f"- Creator: **{dashboard.get('creator', '—')}**",
            f"- Owner: **{dashboard.get('owner', '—')}**",
            f"- Provider (session): **{dashboard.get('provider', '—')}**",
            f"- Runtime model: **{dashboard.get('runtime_model', '—')}**",
            f"- Trust status: **{'OK' if dashboard.get('trust_status') else 'REVIEW'}**",
            "",
            "## Identity validation",
            "",
            f"Overall: **{'pass' if validation.get('overall_ok') else 'review'}**",
            "",
            "## Runtime identity lock",
            "",
            "- Identity responses bypass provider-generated self-identity.",
            "- Identity comes from the platform registry.",
        ]
        return "\n".join(lines)

    package = sections.get(focus) or {}
    if isinstance(package, dict) and package.get("markdown"):
        return str(package["markdown"])
    return f"## {focus}\n\n(no rendered content)"
