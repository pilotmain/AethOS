# SPDX-License-Identifier: Apache-2.0
"""Human-facing response formatting for operational tool results."""

from __future__ import annotations

from typing import Any


def format_log_block(
    *,
    provider: str,
    target_label: str,
    logs: list[dict[str, Any]],
    limit: int,
    health: str = "",
    deployment_state: str = "",
    sources: list[str] | None = None,
) -> str:
    lines = [
        f"**{provider.title()} logs for {target_label}** (top **{limit}**):",
        "",
    ]
    if health or deployment_state:
        lines.append(f"Health: **{health or 'unknown'}** · deployment: `{deployment_state or 'unknown'}`")
        lines.append("")
    if not logs:
        lines.append("_No log lines returned from the provider API._")
    else:
        lines.append(f"**Latest {min(limit, len(logs))} logs:**")
        lines.append("")
        for row in logs[:limit]:
            ts = str(row.get("timestamp") or "—")
            level = str(row.get("level") or "INFO")
            message = str(row.get("message") or "").strip()
            source = str(row.get("source") or "").strip()
            suffix = f" _({source})_" if source else ""
            lines.append(f"- `{ts}` **{level}** — {message}{suffix}")
    if sources:
        lines.extend(["", f"_Sources checked:_ {', '.join(sources)}"])
    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)


def format_inventory_block(*, provider: str, body: str) -> str:
    return f"{body.rstrip()}\n\nNo mutation has been performed."


def format_health_block(*, provider: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"**{provider.title()} service health:**", ""]
    for row in rows:
        path = f"{row.get('project') or '—'} / {row.get('environment') or '—'} / {row.get('service') or '—'}"
        lines.append(
            f"- **{path}** — health: **{row.get('health') or 'unknown'}** · "
            f"deployment: `{row.get('deployment_state') or 'unknown'}`"
        )
    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)
