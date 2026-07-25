# SPDX-License-Identifier: Apache-2.0
"""Render Railway service creation execution simulation artifacts."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.service_creation_simulator.simulator_normalization import (
    normalize_simulation_snapshot,
)
from aethos_core.providers.railway.service_creation_simulator.simulator_result import _BLOCKER_CODES


def _dry_run_label(row: dict[str, Any]) -> str:
    check = str(row.get("check") or "")
    status = str(row.get("status") or "unknown")
    labels = {
        "railway_project_environment": "Project/environment resolution",
        "service_name_availability": "Service name availability",
        "github_source_binding": "GitHub source binding",
        "railway_credential_readiness": "Railway credential readiness",
        "required_env_var_readiness": "Required env var readiness",
        "build_start_health_readiness": "Build/start/health readiness",
        "rollback_readiness": "Rollback readiness",
        "execution_api_surface": "Execution API surface",
    }
    name = labels.get(check, check)
    if check == "required_env_var_readiness":
        names_st = row.get("env_var_names_status") or status
        values_st = row.get("env_var_values_status") or status
        lines = [
            f"- Required env var names: {names_st}",
            f"- Required env var values: {values_st}",
        ]
        if values_st == "pass_with_defaults":
            defaults = row.get("using_defaults_preview") or []
            if defaults:
                lines.append("- Using defaults:")
                for item in defaults[:6]:
                    lines.append(f"  - `{item}`")
        optional = row.get("optional_missing_preview") or []
        if optional:
            lines.append("- Optional config missing:")
            for item in optional[:6]:
                lines.append(f"  - `{item}`")
        return "\n".join(lines)
    return f"- {name}: {status}"


def render_simulation_artifact(simulation: dict[str, Any], *, session_id: str = "default") -> str:
    simulation, _repaired = normalize_simulation_snapshot(dict(simulation))
    checks = list(simulation.get("checks") or [])
    blocking = list(simulation.get("blocking_reasons") or [])
    messages = list(simulation.get("blocking_reason_messages") or [])
    if not messages and blocking:
        messages = [_BLOCKER_CODES.get(code, code) for code in blocking]

    lines = [
        "# Railway Service Creation Execution Simulation",
        "",
        "Target:",
        f"- Project: {simulation.get('project') or '—'}",
        f"- Environment: {simulation.get('environment') or '—'}",
        f"- Service: {simulation.get('service_name') or '—'}",
        f"- Source: {simulation.get('repo') or '—'}",
        f"- Branch: {simulation.get('branch') or 'main'}",
        "",
        "Dry-run checks:",
    ]
    for row in checks:
        label = _dry_run_label(row)
        if "\n" in label:
            lines.extend(label.split("\n"))
        else:
            lines.append(label)
        check_name = str(row.get("check") or "")
        details = str(row.get("details") or "").strip()
        if check_name == "railway_project_environment":
            src = str(row.get("resolution_source") or "").strip()
            if src:
                lines.append(f"  - source: {src}")
        if check_name == "railway_credential_readiness":
            src = str(row.get("credential_source") or row.get("checked_source") or "").strip()
            if src:
                label = "source" if row.get("status") == "pass" else "checked source"
                lines.append(f"  - {label}: {src}")
        if details and check_name == "service_name_availability" and row.get("status") == "pass":
            lines.append(f"  - {details}")
        elif details and check_name == "service_name_availability" and row.get("status") == "fail":
            lines.append(f"  - {details}")
            alts = row.get("suggested_alternatives") or []
            if alts:
                lines.append("  - Suggested alternatives:")
                for alt in alts:
                    lines.append(f"    - `{alt}`")

    probe_rows = [row for row in checks if isinstance(row.get("inventory_probe"), dict)]
    if probe_rows:
        lines.append("")
        lines.append("Diagnostics:")
        for row in probe_rows:
            probe = dict(row.get("inventory_probe") or {})
            reason = str(probe.get("reason") or "unavailable")
            detail = str(probe.get("detail") or "").strip()
            lines.append(f"- Inventory probe: {probe.get('status', 'degraded')}")
            lines.append(f"  - reason: {reason}")
            if detail:
                lines.append(f"  - detail: {detail}")

    api_row = next((r for r in checks if r.get("check") == "execution_api_surface"), None)
    if api_row and isinstance(api_row.get("surfaces"), dict):
        lines.append("")
        lines.append("Execution API surface:")
        for key, state in api_row["surfaces"].items():
            if key == "cli_note":
                continue
            label = key.replace("_", " ")
            lines.append(f"- {label}: {state}")

    lines.extend(
        [
            "",
            "Execution readiness:",
            f"- ready_to_execute: {'true' if simulation.get('ready_to_execute') else 'false'}",
            "",
        ]
    )
    if messages:
        lines.append("Blocking reasons:")
        for msg in messages:
            lines.append(f"- {msg}")
        lines.append("")

    lines.extend(
        [
            "No service has been created.",
            "No mutation has been performed.",
            "Service creation execution: not enabled yet in this runtime.",
        ]
    )
    body = "\n".join(lines)
    from aethos_core.providers.railway.env_value_readiness.env_value_readiness import (
        append_env_value_readiness_section,
    )

    plan_for_env = {
        "repo": simulation.get("repo") or "",
        "project": simulation.get("project") or "",
        "environment": simulation.get("environment") or "",
        "service_name": simulation.get("service_name") or "",
        "required_env_var_names": list(simulation.get("required_env_var_names") or []),
    }
    return append_env_value_readiness_section(
        body,
        plan=plan_for_env,
        session_id=str(simulation.get("session_id") or session_id),
    )


def render_precondition_blocker(blockers: list[str]) -> str:
    lines = [
        "Cannot simulate Railway service creation yet.",
        "",
        "Missing:",
    ]
    for item in blockers:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Next steps:",
            "1. `confirm railway deployment plan`",
            "2. `create railway service creation preflight`",
            "3. `simulate railway service creation`",
            "",
            "No service has been created.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def render_blocking_followup(simulation: dict[str, Any]) -> str:
    simulation, _repaired = normalize_simulation_snapshot(dict(simulation))
    messages = list(simulation.get("blocking_reason_messages") or [])
    codes = list(simulation.get("blocking_reasons") or [])
    if not messages:
        messages = [_BLOCKER_CODES.get(c, c) for c in codes]
    lines = [
        "# Railway Service Creation — Execution Blocked",
        "",
        f"ready_to_execute: {'true' if simulation.get('ready_to_execute') else 'false'}",
        "",
        "Blocking reasons:",
    ]
    for msg in messages:
        lines.append(f"- {msg}")
    lines.extend(
        [
            "",
            "What would execute (when wired):",
            f"- Create service `{simulation.get('service_name')}` in `{simulation.get('project')}` / `{simulation.get('environment')}`",
            f"- Connect `{simulation.get('repo')}` @ `{simulation.get('branch')}`",
            "- Apply build/start from deployment plan",
            "- Require env var values via secure credential path",
            "",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def render_passed_followup(simulation: dict[str, Any]) -> str:
    passed = [r for r in (simulation.get("checks") or []) if r.get("status") == "pass"]
    lines = ["# Railway Service Creation Simulation — Passed Checks", ""]
    if not passed:
        lines.append("(No checks passed in the saved simulation.)")
    else:
        for row in passed:
            lines.append(_dry_run_label(row))
            detail = str(row.get("details") or "").strip()
            if detail:
                lines.append(f"  - {detail}")
    lines.append("")
    lines.append("No mutation has been performed.")
    return "\n".join(lines)


def render_failed_followup(simulation: dict[str, Any]) -> str:
    failed = [
        r
        for r in (simulation.get("checks") or [])
        if r.get("status") in {"fail", "blocked", "unknown"}
    ]
    lines = ["# Railway Service Creation Simulation — Failed / Blocked Checks", ""]
    if not failed:
        lines.append("(No failed checks in the saved simulation.)")
    else:
        for row in failed:
            lines.append(_dry_run_label(row))
            detail = str(row.get("details") or "").strip()
            if detail:
                lines.append(f"  - {detail}")
            alts = row.get("suggested_alternatives") or []
            for alt in alts:
                lines.append(f"  - suggested: `{alt}`")
    lines.append("")
    lines.append("No mutation has been performed.")
    return "\n".join(lines)
