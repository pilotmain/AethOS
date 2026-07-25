# SPDX-License-Identifier: Apache-2.0
"""Vercel deployment logs — API-first with structured excerpts."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.vercel.api_client import (
    find_project_by_name,
    get_deployment_events,
    list_deployments,
    parse_deployment_record,
)


def _extract_log_lines(events: list[dict[str, Any]], *, limit: int = 80) -> list[str]:
    lines: list[str] = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        text = str(ev.get("text") or ev.get("payload") or ev.get("message") or "").strip()
        if not text and isinstance(ev.get("payload"), dict):
            text = str(ev["payload"].get("text") or "").strip()
        if text:
            lines.append(text[:500])
        if len(lines) >= limit:
            break
    return lines


def _parse_event_record(ev: dict[str, Any]) -> dict[str, Any]:
    text = str(ev.get("text") or ev.get("message") or "").strip()
    if not text and isinstance(ev.get("payload"), dict):
        text = str(ev["payload"].get("text") or "").strip()
    return {
        "type": str(ev.get("type") or ev.get("event") or "log"),
        "text": text[:500],
        "created": ev.get("created") or ev.get("createdAt") or ev.get("timestamp"),
    }


def _select_deployment_for_logs(raw: list[Any]) -> list[dict[str, Any]]:
    """Deployment candidates for log extraction — READY first, then newest."""
    parsed = [parse_deployment_record(d) for d in raw if isinstance(d, dict)]
    ready = [d for d in parsed if str(d.get("state") or "").lower() in {"ready", "success"}]
    other = [d for d in parsed if d not in ready]
    return ready + other


def fetch_deployment_logs(
    token: str,
    *,
    project_name: str,
    deployment_id: str | None = None,
    project_id: str | None = None,
    team_id: str | None = None,
) -> dict[str, Any]:
    project: dict[str, Any] | None = None
    if project_id:
        project = {"id": project_id, "name": project_name, "teamId": team_id}
    else:
        project = find_project_by_name(token, project_name)
    if not project:
        return {
            "ok": False,
            "source": "provider_api",
            "error": f"Project `{project_name}` not found via Vercel API.",
            "log_lines": [],
        }
    project_id = str(project.get("id") or "")
    team_id = str(project.get("teamId") or "") or None
    dep_id = (deployment_id or "").strip()
    deployment: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = []
    if dep_id:
        candidates = [{"id": dep_id, "state": "unknown"}]
    else:
        raw = list_deployments(token, project_id=project_id, team_id=team_id, limit=10)
        candidates = _select_deployment_for_logs(raw)
    if not candidates:
        return {
            "ok": False,
            "source": "provider_api",
            "error": "No deployments found for log extraction.",
            "log_lines": [],
        }

    preferred = candidates[0]
    last_error = ""
    last_events: list[dict[str, Any]] = []
    for candidate in candidates[:6]:
        dep_id = str(candidate.get("id") or "")
        if not dep_id:
            continue
        deployment = candidate
        try:
            events = get_deployment_events(token, dep_id, limit=120)
        except Exception as exc:
            last_error = f"Vercel deployment events unavailable: {exc}"
            last_events = []
            continue
        log_lines = _extract_log_lines(events)
        structured_events = [_parse_event_record(ev) for ev in events if isinstance(ev, dict)][:50]
        has_text = any(str(e.get("text") or "").strip() for e in structured_events)
        if log_lines or has_text:
            return {
                "ok": True,
                "source": "provider_api",
                "project_name": str(project.get("name") or project_name),
                "deployment_id": dep_id,
                "deployment": deployment,
                "event_count": len(events),
                "events": structured_events,
                "log_lines": log_lines,
                "api_limited": False,
            }
        last_events = events
        last_error = ""

    structured_events = [_parse_event_record(ev) for ev in last_events if isinstance(ev, dict)][:50]
    report = preferred if isinstance(preferred, dict) else deployment or {}
    report_id = str(report.get("id") or dep_id or "")
    return {
        "ok": False,
        "source": "provider_api",
        "project_name": str(project.get("name") or project_name),
        "deployment_id": report_id,
        "deployment": report,
        "deployments_tried": min(len(candidates), 6),
        "event_count": len(last_events),
        "events": structured_events,
        "log_lines": [],
        "api_limited": True,
        "error": last_error or "No log lines returned from Vercel deployment events API.",
    }


def format_logs_output(payload: dict[str, Any]) -> str:
    if not payload.get("ok") and not payload.get("log_lines"):
        err = str(payload.get("error") or "Log fetch failed.")
        if payload.get("api_limited"):
            return err + "\n\n(Runtime logs may require browser fallback.)"
        return err
    lines = [
        f"Project: {payload.get('project_name')}",
        f"Deployment: `{payload.get('deployment_id')}`",
        f"Events: {payload.get('event_count', 0)}",
        "",
        "## Log excerpt",
        "",
    ]
    for ln in payload.get("log_lines") or []:
        lines.append(ln)
    if len(lines) <= 5:
        lines.append("(no log lines returned from Vercel API)")
    return "\n".join(lines)
