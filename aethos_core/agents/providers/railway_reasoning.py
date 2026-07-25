# SPDX-License-Identifier: Apache-2.0
"""Railway provider diagnostics — real deployment + log substrate."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.agents.providers.deployment_correlation import correlate_deployments
from aethos_core.operations.intents import extract_target_hints
from aethos_core.providers.railway.auth import RailwayAuthAdapter
from aethos_core.providers.railway.api_client import find_service_by_name, list_service_deployments
from aethos_core.providers.railway.operations.logs_api import fetch_service_logs, format_logs_output


def run_railway_diagnostics(user_request: str) -> dict[str, Any]:
    """Fetch Railway deployments and logs when credentials are available."""
    auth = RailwayAuthAdapter().resolve_best_auth_method(operation="read_projects")
    if not auth.get("credential_id"):
        return {
            "ok": False,
            "provider": "railway",
            "credential_required": True,
            "credential_state": "unavailable",
            "detail": auth.get("detail") or "Railway API token required.",
            "report": _credential_required_report(),
        }

    token = RailwayAuthAdapter().get_api_token(str(auth["credential_id"]))
    if not token:
        return {
            "ok": False,
            "provider": "railway",
            "credential_required": True,
            "detail": "Railway token not decryptable — reconnect in Mission Control.",
            "report": _credential_required_report(),
        }

    service_name = _resolve_service_name(user_request)
    if not service_name:
        return {
            "ok": False,
            "provider": "railway",
            "detail": "Could not resolve Railway service name from request.",
            "report": "Specify a Railway service name or register target in Mission Control inventory.",
        }

    logs_payload = fetch_service_logs(token, service_name=service_name)
    svc = find_service_by_name(token, service_name)
    deployments: list[dict[str, Any]] = []
    if svc:
        deployments = list_service_deployments(token, service_id=str(svc["service_id"]), limit=10)

    failed = _select_failed(deployments)
    healthy = _select_healthy(deployments, exclude_id=str(failed.get("id") or "") if failed else "")
    correlation = correlate_deployments(failed=failed, healthy=healthy, deployments=deployments)

    log_text = str(logs_payload.get("log_text") or "")
    report = _format_railway_report(service_name, logs_payload, correlation, log_text, failed=failed)

    return {
        "ok": logs_payload.get("ok", False),
        "provider": "railway",
        "service_name": service_name,
        "credential_state": "available",
        "source_api": "railway_provider_api",
        "deployment_id": logs_payload.get("deployment_id"),
        "deployment_state": logs_payload.get("deployment_state"),
        "failed_deployment_found": bool(failed),
        "logs_available": bool(log_text.strip()),
        "correlation": correlation,
        "log_excerpt": log_text[-2000:],
        "log_text": log_text,
        "events": logs_payload.get("events") or [],
        "report": report,
        "evidence_chain": [
            f"deployment:{correlation.get('failed_deployment', {}).get('id') or 'unknown'}",
            f"healthy:{correlation.get('last_healthy_deployment', {}).get('id') or 'unknown'}",
        ],
    }


def _credential_required_report() -> str:
    return (
        "# Railway diagnostics (credential required)\n\n"
        "Connect Railway in **Mission Control → Advanced settings → Credentials** to fetch real deployment timelines and logs.\n"
        "No synthetic deployment IDs are fabricated when credentials are missing."
    )


def _resolve_service_name(text: str) -> str | None:
    hints = extract_target_hints(text)
    for h in hints:
        if h and not re.search(r"\b(railway|deployment|failed|latest|analyze|why)\b", h, re.I):
            return h
    m = re.search(r"\bservice\s+([a-z0-9_-]+)", text, re.I)
    if m:
        return m.group(1)
    return hints[0] if hints else None


def _select_failed(deployments: list[dict[str, Any]]) -> dict[str, Any] | None:
    for dep in deployments:
        state = str(dep.get("state") or "").lower()
        if state in ("failed", "crashed", "error"):
            return dep
    return None


def _select_healthy(deployments: list[dict[str, Any]], *, exclude_id: str) -> dict[str, Any] | None:
    for dep in deployments:
        if str(dep.get("id") or "") == exclude_id:
            continue
        state = str(dep.get("state") or "").lower()
        if state in ("success", "ready", "active", "completed"):
            return dep
    return None


def _format_railway_report(
    service: str,
    logs_payload: dict[str, Any],
    correlation: dict[str, Any],
    log_text: str,
    *,
    failed: dict[str, Any] | None,
) -> str:
    failed_summary = correlation.get("failed_deployment") or {}
    healthy = correlation.get("last_healthy_deployment") or {}
    lines = [
        "# Railway deployment diagnostics (readonly)",
        "",
        f"**Service:** {service}",
        f"**Source:** Railway provider API",
        f"**Credential state:** available",
        f"**Logs available:** {'yes' if log_text.strip() else 'no'}",
        "",
    ]
    if failed and failed_summary.get("id"):
        lines.extend(
            [
                f"**Failed deployment:** `{failed_summary.get('id')}` · state **{failed_summary.get('state') or logs_payload.get('deployment_state') or 'unknown'}**",
                f"**Last healthy deployment:** `{healthy.get('id') or '—'}`",
                f"**Restart count:** {correlation.get('restart_count', 0)}",
                "",
            ]
        )
        if failed_summary.get("error_message"):
            lines.extend(["## Failure signal", str(failed_summary["error_message"]), ""])
    else:
        lines.extend(
            [
                "**Failed deployment:** none found in latest deployment list",
                f"**Latest queried deployment:** `{logs_payload.get('deployment_id') or '—'}` · state **{logs_payload.get('deployment_state') or 'unknown'}**",
                f"**Last healthy deployment:** `{healthy.get('id') or '—'}`",
                "",
                "> No failed Railway deployment was identified from current provider evidence.",
                "",
            ]
        )
    lines.append("## Recent log excerpt")
    if log_text:
        for ln in log_text.splitlines()[-12:]:
            lines.append(f"- `{ln[:220]}`")
    else:
        lines.append("- No log lines returned from provider API for this query.")
    return "\n".join(lines)
