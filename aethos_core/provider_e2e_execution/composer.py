# SPDX-License-Identifier: Apache-2.0
"""Compose provider E2E execution replies — no secret values."""

from __future__ import annotations

from typing import Any


def compose_missing_config_report(
    *,
    provider: str,
    blockers: list[str],
    required: list[str],
    next_steps: list[str],
) -> str:
    lines = [
        f"**{provider.title()} E2E — missing configuration**",
        "",
        "I started a governed readiness pass. Execution has **not** started — configure the items below first.",
        "",
        "**Blockers:**",
    ]
    for item in blockers or ["Unknown blocker — check Mission Control → Advanced settings → Credentials."]:
        lines.append(f"- {item}")
    if required:
        lines.extend(["", "**Required:**"])
        for item in required:
            lines.append(f"- {item}")
    lines.extend(["", "**Valid next steps:**"])
    for step in next_steps:
        lines.append(f"- {step}")
    lines.append("")
    lines.append("No provider mutation has been performed.")
    return "\n".join(lines)


def compose_e2e_orchestration_preflight_reply(
    *,
    provider: str,
    job_id: str,
    target_label: str,
    steps: list[str],
    readiness_summary: str,
    approval_path: str = "Mission Control → Jobs",
) -> str:
    lines = [
        f"**{provider.title()} E2E orchestration preflight created**",
        "",
        readiness_summary.strip(),
        "",
        f"**Target:** {target_label}",
        "",
        "**Planned governed steps (approval required before each mutation):**",
    ]
    for idx, step in enumerate(steps, start=1):
        lines.append(f"{idx}. {step}")
    lines.extend(
        [
            "",
            f"Review orchestration job `{job_id}` in **{approval_path}**.",
            "No env var values are shown here. No mutation has been executed yet.",
        ]
    )
    return "\n".join(lines)


def redact_checks_snapshot(checks: dict[str, Any]) -> dict[str, Any]:
    """Drop sensitive fields from checks before storing on a job."""
    safe = dict(checks)
    for key in ("railway_api_token", "token", "credential"):
        safe.pop(key, None)
    return safe
