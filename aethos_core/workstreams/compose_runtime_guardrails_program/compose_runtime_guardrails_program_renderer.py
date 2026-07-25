# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E4 / FIX 346 — render compose runtime guardrails deliverables."""

from __future__ import annotations

from typing import Any


def _section(payload: dict[str, Any], phase: str, key: str) -> Any:
    return (payload.get("sections") or {}).get(phase, [{}])[0].get(key)


def render_compose_runtime_guardrails_report(payload: dict[str, Any]) -> str:
    success = payload.get("success_criteria") or {}
    guard = _section(payload, "phase_3_heavy_compose_guard", "heavy_compose_guard_report") or {}
    lines = [
        "# Compose Runtime Guardrails Report",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_E4')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 346')}",
        "",
        "## Core principle",
        "",
        "Guardrails prevent accidental expensive execution without reducing evidence. "
        "**Runtime guardrails ≠ evidence reduction.**",
        "",
        f"- Active mode: **{payload.get('active_runtime_mode', 'operator')}**",
        f"- Guarded modules: **{', '.join(guard.get('guarded_modules') or [])}**",
        f"- Test safety enforced: **{success.get('test_runtime_safety_enforced')}**",
        f"- Interactive operator default: **{success.get('interactive_defaults_operator_mode')}**",
        f"- Evidence reduction performed: **{success.get('evidence_reduction_performed')}**",
    ]
    return "\n".join(lines)


def render_benchmark_mode_separation_report(payload: dict[str, Any]) -> str:
    registry = _section(payload, "phase_6_benchmark_command_separation", "benchmark_command_registry") or {}
    lines = [
        "# Benchmark Mode Separation Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        "Explicit benchmark entrypoints separated from operator flows:",
        "",
    ]
    for row in registry.get("commands") or []:
        lines.append(f"- `{row.get('command')}` → mode `{row.get('runtime_mode')}`")
    return "\n".join(lines)


def render_test_runtime_safety_report(payload: dict[str, Any]) -> str:
    report = _section(payload, "phase_4_test_runtime_safety", "test_runtime_safety_report") or {}
    lines = [
        "# Test Runtime Safety Report",
        "",
        f"**Session:** {payload.get('session_id', '')}",
        "",
        f"- Default test mode: **{report.get('default_test_mode')}**",
        f"- Tests default lightweight: **{report.get('tests_default_lightweight')}**",
        f"- Critical compose blocked in test mode: **{report.get('critical_compose_blocked_in_test_mode')}**",
        f"- Explicit benchmark required: **{report.get('explicit_benchmark_required_for_full_compose')}**",
    ]
    return "\n".join(lines)


def render_all_compose_runtime_guardrails_deliverables(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "COMPOSE_RUNTIME_GUARDRAILS_REPORT.md": render_compose_runtime_guardrails_report(payload),
        "BENCHMARK_MODE_SEPARATION_REPORT.md": render_benchmark_mode_separation_report(payload),
        "TEST_RUNTIME_SAFETY_REPORT.md": render_test_runtime_safety_report(payload),
    }


def render_compose_runtime_guardrails_program(
    payload: dict[str, Any],
    *,
    focus: str = "runtime_safety_dashboard",
) -> str:
    dashboard = _section(payload, "phase_8_runtime_safety_dashboard", "runtime_safety_dashboard") or {}
    lines = [
        "# Compose Runtime Guardrails Program",
        "",
        f"**Workstream:** {payload.get('workstream_id', 'WORKSTREAM_E4')}",
        f"**FIX:** {payload.get('fix_id', 'FIX 346')}",
        "",
        f"Active mode: **{dashboard.get('active_mode', payload.get('active_runtime_mode'))}**",
        "",
        "## Operator commands",
        "",
        "- `runtime guardrail note: ...`",
        "- `run compose benchmark`",
        "- `run full evidence benchmark`",
        "- `run critical compose benchmark`",
        "- `runtime guardrail review approve: ...`",
        "- `show runtime safety dashboard`",
        "",
    ]
    return "\n".join(lines)
