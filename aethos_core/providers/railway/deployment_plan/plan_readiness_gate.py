# SPDX-License-Identifier: Apache-2.0
"""Mutation readiness gate for Railway new-service deployment plans."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.deployment_plan.repo_inspection import is_health_probe_command

_UNKNOWN_VALUES = frozenset({"", "unknown", "unknown / inferred"})

_FIELD_LABELS = {
    "runtime": "Runtime",
    "start_command": "Start command",
    "build_command": "Build command",
    "project": "Railway project",
    "environment": "Railway environment",
    "service_name": "Service name",
    "health_verification": "Health verification strategy",
}


def _is_known_field(value: object) -> bool:
    text = str(value or "").strip().lower()
    return text not in _UNKNOWN_VALUES


def assess_mutation_readiness_gate(plan: dict[str, Any]) -> dict[str, Any]:
    """mutation_ready is true only when governed create prerequisites are satisfied."""
    missing: list[str] = []

    if not _is_known_field(plan.get("runtime")):
        missing.append("runtime")
    if not _is_known_field(plan.get("build_command")):
        missing.append("build_command")
    start = str(plan.get("start_command") or "")
    if not _is_known_field(start) or is_health_probe_command(start):
        missing.append("start_command")
    if not str(plan.get("project") or "").strip():
        missing.append("project")
    if not str(plan.get("environment") or "").strip():
        missing.append("environment")
    if not str(plan.get("service_name") or "").strip():
        missing.append("service_name")
    if not _is_known_field(plan.get("health_check_path")):
        missing.append("health_verification")

    mutation_ready = not missing
    return {
        "mutation_ready": mutation_ready,
        "missing": missing,
        "missing_labels": [_FIELD_LABELS.get(key, key) for key in missing],
    }


def format_readiness_gate_lines(plan: dict[str, Any]) -> list[str]:
    gate = assess_mutation_readiness_gate(plan)
    lines = [
        "Readiness gate:",
        f"- mutation_ready: {'true' if gate['mutation_ready'] else 'false'}",
        "- missing:",
    ]
    missing = list(gate.get("missing") or [])
    if missing:
        for key in missing:
            lines.append(f"  - {key}")
    else:
        lines.append("  - (none)")
    return lines
