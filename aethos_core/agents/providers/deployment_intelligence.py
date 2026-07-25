# SPDX-License-Identifier: Apache-2.0
"""Deployment intelligence — operational telemetry and timelines."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from aethos_core.operations.intents import extract_target_hints


def build_deployment_intelligence(user_request: str) -> dict[str, Any]:
    """Unified deployment intelligence — provider telemetry + timeline."""
    lower = (user_request or "").lower()
    if "vercel" in lower and "railway" not in lower:
        return _vercel_intelligence(user_request)
    if ("github" in lower or "workflow" in lower) and "railway" not in lower and "deployment" not in lower:
        return _github_intelligence(user_request)
    return _railway_intelligence(user_request)


def format_deployment_intelligence_report(intel: dict[str, Any]) -> str:
    lines = [
        "# Deployment Intelligence",
        "",
        f"**Provider:** {intel.get('provider', 'unknown')}",
        f"**Credential state:** {intel.get('credential_state', 'unknown')}",
        f"**Source API:** {intel.get('source_api', '—')}",
        "",
    ]
    latest = intel.get("latest_deployment") or {}
    previous = intel.get("previous_deployment") or {}
    if latest:
        lines.extend(
            [
                "## Latest deployment",
                f"- ID: `{latest.get('id') or '—'}`",
                f"- State: **{latest.get('state') or 'unknown'}**",
                f"- Started: {latest.get('started_label') or '—'}",
                f"- Duration: {latest.get('duration_label') or '—'}",
                f"- Logs available: {'yes' if latest.get('logs_available') or intel.get('logs_available') else 'no'}",
                "",
            ]
        )
    if previous:
        lines.extend(
            [
                "## Previous deployment",
                f"- ID: `{previous.get('id') or '—'}`",
                f"- State: **{previous.get('state') or 'unknown'}**",
                f"- Failure window: {previous.get('started_label') or '—'}",
                "",
            ]
        )
    if intel.get("restart_count"):
        lines.append(f"**Restart history:** {intel.get('restart_count')} restart signal(s) in recent window")
        lines.append("")
    corr = intel.get("correlated_signals") or []
    if corr:
        lines.append("## Correlated signals")
        for c in corr:
            lines.append(f"- {c}")
        lines.append("")
    conf = intel.get("confidence") or {}
    if conf.get("level"):
        lines.append(f"**Confidence:** {conf['level']} — {', '.join(conf.get('reasons') or []) or 'provider telemetry'}")
    elif intel.get("telemetry_quality"):
        lines.append(f"**Telemetry quality:** {intel['telemetry_quality']}")
    return "\n".join(lines)


def _railway_intelligence(user_request: str) -> dict[str, Any]:
    from aethos_core.agents.providers.railway_reasoning import run_railway_diagnostics
    from aethos_core.providers.railway.api_client import find_service_by_name, list_service_deployments
    from aethos_core.providers.railway.auth import RailwayAuthAdapter

    auth = RailwayAuthAdapter().resolve_best_auth_method(operation="read_projects")
    if not auth.get("credential_id"):
        return {
            "ok": False,
            "provider": "railway",
            "credential_state": "unavailable",
            "source_api": "railway_graphql",
            "telemetry_quality": "none",
            "report": format_deployment_intelligence_report(
                {
                    "provider": "railway",
                    "credential_state": "unavailable",
                    "source_api": "railway_graphql",
                }
            ),
        }

    diag = run_railway_diagnostics(user_request)
    service_name = diag.get("service_name")
    deployments: list[dict[str, Any]] = []
    service_id = None
    token = RailwayAuthAdapter().get_api_token(str(auth["credential_id"]))
    if token and service_name:
        svc = find_service_by_name(token, service_name)
        if svc:
            service_id = svc.get("service_id")
            deployments = list_service_deployments(token, service_id=str(service_id), limit=10)

    timeline = _build_timeline(deployments, logs_available=bool(diag.get("logs_available")))
    latest = timeline[0] if timeline else {}
    previous_failed = next((d for d in timeline[1:] if _is_failed(d)), timeline[1] if len(timeline) > 1 else {})

    restart_count = sum(1 for d in timeline if _is_failed(d))
    quality = "high" if diag.get("logs_available") and latest.get("id") else "medium" if latest.get("id") else "low"
    correlated: list[str] = []
    failed = (diag.get("correlation") or {}).get("failed_deployment") or {}
    if failed.get("commit"):
        correlated.append(f"Git commit `{failed.get('commit')}` aligns with deployment window.")
    if diag.get("failed_deployment_found") and not diag.get("logs_available"):
        correlated.append("Workflow/build failure likely — deployment logs unavailable for confirmation.")

    confidence = {
        "level": "medium" if quality in ("high", "medium") else "low",
        "reasons": ["provider telemetry"] + (["deployment logs"] if diag.get("logs_available") else []),
    }

    intel = {
        "ok": True,
        "provider": "railway",
        "credential_state": "available",
        "source_api": "railway_graphql",
        "service_name": service_name,
        "service_id": service_id,
        "deployments": timeline,
        "latest_deployment": latest,
        "previous_deployment": previous_failed if isinstance(previous_failed, dict) else {},
        "failed_deployment_found": bool(diag.get("failed_deployment_found")),
        "restart_count": restart_count,
        "logs_available": bool(diag.get("logs_available")),
        "telemetry_quality": quality,
        "correlated_signals": correlated,
        "confidence": confidence,
        "correlation": diag.get("correlation"),
        "log_excerpt": diag.get("log_excerpt"),
        "deployment_id": diag.get("deployment_id"),
        "deployment_state": diag.get("deployment_state"),
    }
    intel["report"] = format_deployment_intelligence_report(intel)
    intel.update({k: v for k, v in diag.items() if k not in intel})
    return intel


def _vercel_intelligence(user_request: str) -> dict[str, Any]:
    from aethos_core.agents.providers.vercel_reasoning import run_vercel_diagnostics

    diag = run_vercel_diagnostics(user_request)
    intel = {
        "ok": diag.get("ok", False),
        "provider": "vercel",
        "credential_state": "unavailable" if diag.get("credential_required") else "available",
        "source_api": "vercel_api",
        "telemetry_quality": "low" if diag.get("credential_required") else "medium",
        "target": diag.get("target"),
        "latest_deployment": {"state": diag.get("state"), "id": diag.get("deployment_id")},
    }
    intel["report"] = diag.get("report") or format_deployment_intelligence_report(intel)
    return intel


def _github_intelligence(user_request: str) -> dict[str, Any]:
    from aethos_core.agents.providers.github_reasoning import run_github_diagnostics

    diag = run_github_diagnostics(user_request)
    intel = {
        "ok": diag.get("ok", False),
        "provider": "github",
        "credential_state": "unavailable" if diag.get("credential_required") else "available",
        "source_api": "github_api",
        "telemetry_quality": "low" if diag.get("credential_required") else "medium",
        "repo_hint": diag.get("repo_hint"),
        "latest_deployment": {"state": diag.get("workflow_state"), "id": diag.get("workflow_run_id")},
    }
    intel["report"] = diag.get("report") or format_deployment_intelligence_report(intel)
    return intel


def _build_timeline(deployments: list[dict[str, Any]], *, logs_available: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dep in deployments:
        created = dep.get("created_at")
        rows.append(
            {
                "id": dep.get("id"),
                "state": dep.get("state"),
                "branch": dep.get("branch"),
                "commit": dep.get("commit"),
                "commit_message": dep.get("commit_message"),
                "created_at": created,
                "started_label": _format_ts(created),
                "duration_label": "—",
                "logs_available": logs_available,
                "error_message": dep.get("error_message"),
            }
        )
    return rows


def _is_failed(dep: dict[str, Any]) -> bool:
    return str(dep.get("state") or "").lower() in ("failed", "crashed", "error")


def _format_ts(raw: Any) -> str:
    if not raw:
        return "—"
    try:
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw / 1000 if raw > 1e12 else raw, tz=timezone.utc).strftime("%I:%M %p UTC")
        text = str(raw).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        return dt.strftime("%I:%M %p UTC")
    except (ValueError, TypeError, OSError):
        return str(raw)[:24]


def resolve_service_name(text: str) -> str | None:
    hints = extract_target_hints(text)
    for h in hints:
        if h and not re.search(r"\b(railway|deployment|failed|latest|analyze|why)\b", h, re.I):
            return h
    return hints[0] if hints else None
