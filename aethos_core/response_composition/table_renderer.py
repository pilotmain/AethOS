# SPDX-License-Identifier: Apache-2.0
"""Markdown table renderer for operational payloads."""

from __future__ import annotations

from typing import Any


def render_service_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "(no services)"
    lines = [
        "| Service | Project | Environment | Status | Health |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('service', '—')} | {row.get('project', '—')} | {row.get('environment', '—')} "
            f"| {row.get('status', '—')} | {row.get('health', '—')} |"
        )
    return "\n".join(lines)
