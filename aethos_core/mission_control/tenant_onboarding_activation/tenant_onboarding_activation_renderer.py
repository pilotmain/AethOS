# SPDX-License-Identifier: Apache-2.0
"""FIX 301 — tenant onboarding and activation renderer."""

from __future__ import annotations

from typing import Any


def render_tenant_onboarding_activation(payload: dict[str, Any]) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("tenant_onboarding_dashboard") or [{}])[0]
    progress = (sections.get("onboarding_progress_registry") or [{}])[0]
    organization = (sections.get("organization_setup_review") or [{}])[0]
    workspace = (sections.get("workspace_setup_review") or [{}])[0]
    project = (sections.get("project_registration_review") or [{}])[0]
    provider = (sections.get("provider_connection_checklist") or [{}])[0]
    capability = (sections.get("capability_discovery_report") or [{}])[0]
    trust = (sections.get("trust_explanation_report") or [{}])[0]
    activation = (sections.get("first_mission_control_activation_packet") or [{}])[0]

    lines = [
        "# Tenant Onboarding & Activation",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 301')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Onboarding guidance ≠ platform authority. Review artifacts only — no automatic provisioning.",
        "",
        "## Tenant onboarding dashboard",
        "",
        f"Progress: **{progress.get('completed_step_count', 0)}** / **{progress.get('total_step_count', 0)}** steps.",
        f"Organizations modeled: **{dashboard.get('organization_count', 0)}**.",
        "",
        "## Onboarding progress",
        "",
    ]

    for step in progress.get("steps") or []:
        lines.append(f"- **{step.get('label')}**: {step.get('status')}")

    lines.extend(["", "## Step 1 — Organization setup", ""])
    lines.append(f"Status: **{organization.get('status', 'pending')}**")
    for field in organization.get("collects") or []:
        lines.append(f"- Collect: {field}")

    lines.extend(["", "## Step 2 — Workspace setup", ""])
    lines.append(f"Status: **{workspace.get('status', 'pending')}**")
    for field in workspace.get("collects") or []:
        lines.append(f"- Collect: {field}")

    lines.extend(["", "## Step 3 — Project registration", ""])
    lines.append(f"Status: **{project.get('status', 'pending')}**")
    for field in project.get("collects") or []:
        lines.append(f"- Collect: {field}")

    lines.extend(["", "## Step 4 — Provider connection", ""])
    for target in provider.get("targets") or []:
        lines.append(
            f"- **{target.get('provider')}**: {target.get('status')} ({target.get('readiness')}) — manual setup only"
        )
    lines.append("- Never paste secrets into chat.")

    lines.extend(["", "## Step 5 — Capability discovery", ""])
    for item in capability.get("what_can_you_do") or []:
        lines.append(f"- Can do: {item}")
    for item in capability.get("what_cannot_you_do") or []:
        lines.append(f"- Cannot do: {item}")

    lines.extend(["", "## Step 6 — Trust explanation", ""])
    for item in trust.get("human_approval_model") or []:
        lines.append(f"- {item}")
    for repo in trust.get("repository_trust") or []:
        name = repo.get("display_name") or repo.get("repository")
        lines.append(f"- Repository trust: **{name}** — {repo.get('trust_state', '—')}")

    lines.extend(["", "## Step 7 — First Mission Control session", ""])
    lines.append(f"Status: **{activation.get('status', 'blocked')}**")
    for action in activation.get("guided_actions") or []:
        lines.append(f"- {action}")

    lines.extend(["", "## Authority boundaries", ""])
    for boundary in capability.get("authority_boundaries") or []:
        lines.append(f"- {boundary}")

    lines.extend(
        [
            "",
            "Record review notes with `organization setup:`, `workspace setup:`, `project registration:`, "
            "and `provider connection note:`. Human decisions use `onboarding decision approve:` (or hold/reject/defer).",
        ]
    )
    return "\n".join(lines)
