# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — truth dashboard renderer."""

from __future__ import annotations

from typing import Any


def render_truth_consistency_markdown(*, payload: dict[str, Any], focus: str = "truth_dashboard") -> str:
    sections = payload.get("sections") or {}
    if focus != "truth_dashboard":
        section = sections.get(focus) or {}
        if isinstance(section, dict) and section.get("markdown"):
            return str(section["markdown"])
        return f"## {focus}\n\n(no rendered content)"

    dashboard = sections.get("truth_dashboard") or {}
    lines = [
        "## Truth dashboard",
        "",
        f"- Capability truth: **{'OK' if dashboard.get('capability_truth_ok') else 'REVIEW'}**",
        f"- Trust truth: **{'OK' if dashboard.get('trust_truth_ok') else 'REVIEW'}**",
        f"- Provider truth: **{'OK' if dashboard.get('provider_truth_ok') else 'REVIEW'}**",
        f"- Identity truth: **{'OK' if dashboard.get('identity_truth_ok') else 'REVIEW'}**",
        f"- Readiness truth: **{'OK' if dashboard.get('readiness_truth_ok') else 'REVIEW'}**",
        f"- Hallucination detected: **{'yes' if dashboard.get('hallucination_detected') else 'no'}**",
        f"- Truth drift detected: **{'yes' if dashboard.get('truth_drift_detected') else 'no'}**",
        "",
        "## Core principle",
        "",
        str(dashboard.get("core_principle") or "generated_response ≠ platform_truth"),
        "",
        "Public answers must align with certified platform evidence. Automatic truth rewrite is forbidden.",
    ]
    return "\n".join(lines)
