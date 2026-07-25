# SPDX-License-Identifier: Apache-2.0
"""Summary and executive summary renderers."""

from __future__ import annotations

from typing import Any


def attention_label(row: dict[str, Any]) -> str:
    project = str(row.get("project") or "—")
    environment = str(row.get("environment") or "—")
    service = str(row.get("service") or "—")
    state = str(row.get("health") or row.get("status") or "unknown")
    return f"{project} / {environment} / {service} — {state}"


def render_summary_block(counts: dict[str, Any]) -> list[str]:
    return [
        "Summary:",
        f"- Total: **{counts.get('total', 0)}**",
        f"- Healthy/running: **{counts.get('healthy', 0)}**",
        f"- Failed: **{counts.get('failed', 0)}**",
        f"- Unknown: **{counts.get('unknown', 0)}**",
    ]


def render_needs_attention(failed_rows: list[dict[str, Any]], unknown_rows: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    if not failed_rows and not unknown_rows:
        return lines
    lines.append("")
    lines.append("Needs attention:")
    for row in failed_rows:
        lines.append(f"- {attention_label(row)}")
    for row in unknown_rows:
        lines.append(f"- {attention_label(row)}")
    return lines


def render_failed_service_list(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    lines = ["", "Failed services:"]
    for row in rows:
        lines.append(f"- {attention_label(row)}")
    return lines


def render_unknown_service_list(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    lines = ["", "Unknown services:"]
    for row in rows:
        lines.append(f"- {attention_label(row)}")
    return lines


def render_fix_priority(failed_rows: list[dict[str, Any]], unknown_rows: list[dict[str, Any]]) -> str:
    lines = ["Fix priority:"]
    if failed_rows:
        for idx, row in enumerate(failed_rows, start=1):
            lines.append(f"{idx}. **{attention_label(row)}** — investigate deployment/runtime failure first")
    if unknown_rows:
        start = len(failed_rows) + 1
        for idx, row in enumerate(unknown_rows, start=start):
            lines.append(f"{idx}. **{attention_label(row)}** — confirm health evidence / deployment state")
    if not failed_rows and not unknown_rows:
        lines.append("- No failed or unknown services in the last report. Nothing urgent to fix.")
    return "\n".join(lines)
