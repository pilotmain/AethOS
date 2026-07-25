# SPDX-License-Identifier: Apache-2.0
"""Railway runtime failure diagnosis — log pattern classification."""

from __future__ import annotations

import re
from typing import Any

_RULES: list[tuple[str, str, re.Pattern[str], str, str]] = [
    (
        "missing_env_var",
        "Missing environment variable",
        re.compile(r"(?i)(missing|required|undefined).*(env|environment|variable)|DATABASE_URL|API_KEY|SECRET"),
        "redeploy",
        "Configure the missing environment variable and redeploy the service.",
    ),
    (
        "port_bind_failure",
        "Port bind failure",
        re.compile(r"(?i)(EADDRINUSE|address already in use|bind.*port|listen EACCES)"),
        "restart",
        "Review service port configuration and restart after resolving the bind conflict.",
    ),
    (
        "dependency_connection_failure",
        "Dependency connection failure",
        re.compile(r"(?i)(ECONNREFUSED|connection refused|could not connect|database.*unreachable|redis.*unreachable)"),
        "redeploy",
        "Verify dependency credentials/endpoints and redeploy once connectivity is restored.",
    ),
    (
        "build_failure",
        "Build failure",
        re.compile(r"(?i)(build failed|npm ERR!|pnpm ERR!|Module not found|compile error)"),
        "deploy",
        "Fix the build error in source and deploy latest code.",
    ),
    (
        "health_check_failure",
        "Health check failure",
        re.compile(r"(?i)(health check failed|unhealthy|readiness probe failed|liveness probe failed)"),
        "restart",
        "Inspect runtime logs and restart or redeploy after resolving the health check failure.",
    ),
    (
        "crash_loop",
        "Crash loop",
        re.compile(r"(?i)(crash|exited with code|SIGTERM|SIGKILL|process exited|container restart)"),
        "restart",
        "Service is crash-looping. Inspect logs, apply fix, then restart or redeploy.",
    ),
    (
        "memory_limit",
        "Memory limit exceeded",
        re.compile(r"(?i)(out of memory|OOM|memory limit|heap out of memory)"),
        "redeploy",
        "Increase memory limits or reduce memory usage, then redeploy.",
    ),
    (
        "start_command_error",
        "Start command error",
        re.compile(r"(?i)(command not found|ENOENT.*start|cannot find module|failed to start)"),
        "deploy",
        "Fix the start command or package entrypoint, then deploy latest code.",
    ),
]


def diagnose_railway_runtime(*, logs: list[dict[str, Any]], health_summary: str = "") -> dict[str, Any]:
    corpus = " ".join(
        [
            health_summary,
            *[str(row.get("message") or row.get("msg") or "") for row in logs if isinstance(row, dict)],
        ]
    )
    for category, label, pattern, suggested_op, fix in _RULES:
        if pattern.search(corpus):
            signals = [m.group(0)[:120] for m in pattern.finditer(corpus)][:3]
            return {
                "ok": True,
                "category": category,
                "summary": label,
                "likely_cause": fix,
                "log_signals": signals,
                "suggested_operation": suggested_op,
                "requires_approval": True,
            }
    if logs:
        return {
            "ok": True,
            "category": "unknown_runtime_error",
            "summary": "Runtime error detected in logs",
            "likely_cause": "Inspect deployment logs and prepare a governed fix plan before mutation.",
            "log_signals": [str(logs[-1].get("message") or "")[:160]],
            "suggested_operation": "redeploy",
            "requires_approval": True,
        }
    return {
        "ok": False,
        "category": "insufficient_evidence",
        "summary": "Not enough log evidence to diagnose runtime failure.",
        "likely_cause": "Collect Railway deployment logs before proposing a fix.",
        "log_signals": [],
        "suggested_operation": None,
        "requires_approval": True,
    }


def propose_railway_fix(*, diagnosis: dict[str, Any], target_name: str) -> dict[str, Any]:
    if not diagnosis.get("ok"):
        return {
            "ok": False,
            "summary": f"No governed fix plan for `{target_name}` — diagnosis evidence is insufficient.",
            "proposed_operation": None,
            "proposed_changes": [],
            "requires_approval": True,
            "preflight_required": True,
        }
    category = str(diagnosis.get("category") or "unknown")
    op = str(diagnosis.get("suggested_operation") or "redeploy")
    changes = [str(diagnosis.get("likely_cause") or "Apply provider-visible fix and verify.")]
    if category == "missing_env_var":
        changes.insert(0, "Set the missing environment variable in Railway project settings.")
    return {
        "ok": True,
        "summary": f"Governed fix plan for `{target_name}`: {diagnosis.get('summary')}.",
        "proposed_operation": op,
        "proposed_changes": changes,
        "requires_approval": True,
        "preflight_required": True,
    }
