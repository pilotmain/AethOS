# SPDX-License-Identifier: Apache-2.0
"""Fresh Railway runtime log retrieval for restart verification."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

_SPACE_TS_RX = re.compile(
    r"^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})(?:\.(\d+))?$"
)


def normalize_railway_timestamp_to_utc(value: Any) -> str | None:
    """Normalize Railway API/CLI/UI timestamps to UTC ISO-8601 with Z suffix."""
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=UTC)
        return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    text = str(value).strip()
    if not text:
        return None

    match = _SPACE_TS_RX.match(text)
    if match:
        date_part, time_part, micro = match.groups()
        iso = f"{date_part}T{time_part}"
        if micro:
            iso += f".{micro}"
        iso += "+00:00"
        text = iso

    from aethos_core.providers.railway.hardening.restart_transition import _parse_datetime

    parsed = _parse_datetime(text)
    if parsed is None:
        return None
    return parsed.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_log_row(row: dict[str, Any], *, source: str = "") -> dict[str, Any]:
    ts = normalize_railway_timestamp_to_utc(
        row.get("timestamp") or row.get("created") or row.get("created_at")
    )
    out = {
        "timestamp": ts,
        "level": str(row.get("level") or row.get("severity") or "INFO"),
        "message": str(row.get("message") or row.get("text") or row.get("line") or ""),
        "source": source or str(row.get("source") or ""),
    }
    return out


def resolve_verification_target(job: Any) -> dict[str, Any]:
    params = getattr(job, "params", None) or {}
    target = dict(params.get("target") or {})
    artifact = dict(params.get("mutation_execution") or {})
    provider_result = dict(artifact.get("provider_result") or params.get("provider_result") or {})
    rollback = dict(provider_result.get("rollback_metadata") or {})

    approval_time = str(
        params.get("mutation_execution_approved_at_iso")
        or (params.get("provider_evidence_bundle") or {}).get("approved_at")
        or artifact.get("mutation_execution_approved_at_iso")
        or ""
    ) or None
    if approval_time:
        approval_time = normalize_railway_timestamp_to_utc(approval_time) or approval_time

    return {
        "service_name": str(
            params.get("target_name")
            or target.get("service_name")
            or provider_result.get("service_name")
            or ""
        ),
        "service_id": str(
            target.get("service_id")
            or provider_result.get("service_id")
            or rollback.get("service_id")
            or ""
        ),
        "project_id": str(target.get("project_id") or provider_result.get("project_id") or ""),
        "project_name": str(target.get("project_name") or provider_result.get("project_name") or ""),
        "environment": str(target.get("environment") or "production"),
        "environment_id": str(
            target.get("environment_id")
            or provider_result.get("environment_id")
            or rollback.get("environment_id")
            or ""
        ),
        "deployment_id": str(
            params.get("deployment_id")
            or provider_result.get("deployment_id")
            or rollback.get("deployment_id")
            or ""
        ),
        "approval_time": approval_time,
    }


def fetch_runtime_logs_after(
    token: str,
    *,
    service_id: str,
    service_name: str,
    environment_id: str | None = None,
    since_iso: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Fetch runtime-oriented logs after ``since_iso`` using CLI first, then latest deployments."""
    rows: list[dict[str, Any]] = []
    since_norm = normalize_railway_timestamp_to_utc(since_iso) if since_iso else None

    try:
        from aethos_core.providers.railway.cli_executor import railway_logs

        cli_since = since_norm.replace("T", " ").replace("Z", "") if since_norm else None
        payload = railway_logs(service_name=service_name or service_id, since=cli_since, limit=limit)
        for row in payload.get("logs") or []:
            if isinstance(row, dict):
                normalized = normalize_log_row(row, source="runtime_cli_logs")
                if normalized["message"]:
                    rows.append(normalized)
    except Exception:
        pass

    if token and service_id:
        try:
            from aethos_core.providers.railway.api_client import (
                fetch_deployment_logs,
                list_service_deployments,
                logs_after_timestamp,
            )

            deployments = list_service_deployments(token, service_id=service_id, limit=5)
            deployments.sort(key=lambda dep: str(dep.get("created_at") or ""), reverse=True)
            for dep in deployments:
                dep_id = dep.get("id")
                if not dep_id:
                    continue
                dep_logs = fetch_deployment_logs(token, deployment_id=str(dep_id))
                if since_norm:
                    dep_logs = logs_after_timestamp(dep_logs, since_iso=since_norm)
                for row in dep_logs:
                    normalized = normalize_log_row(row, source="deployment_logs")
                    if normalized["message"]:
                        rows.append(normalized)
                if rows and since_norm:
                    break
        except Exception:
            pass

    _ = environment_id
    return _dedupe_and_sort(rows, limit=limit)


def fetch_fresh_logs_for_verification(
    *,
    target: dict[str, Any],
    approval_time: str | None = None,
    bypass_cache: bool = True,
    limit: int = 50,
) -> dict[str, Any]:
    """Fetch fresh Railway logs for restart verification."""
    if not bypass_cache:
        return {"ok": False, "logs": [], "sources_checked": [], "errors": ["cache_only"], "from_cache": True}

    service_name = str(target.get("service_name") or "")
    service_id = str(target.get("service_id") or "")
    environment_id = str(target.get("environment_id") or "") or None
    since = normalize_railway_timestamp_to_utc(approval_time) if approval_time else None

    sources_checked: list[str] = []
    errors: list[str] = []
    merged: list[dict[str, Any]] = []

    token = None
    try:
        from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

        token, _, err = resolve_railway_mutation_credentials()
        if err:
            errors.append(str(err))
    except Exception as exc:
        errors.append(str(exc))

    if token and service_name and not service_id:
        try:
            from aethos_core.providers.railway.api_client import find_service_by_name

            svc = find_service_by_name(token, service_name)
            if svc:
                service_id = str(svc.get("service_id") or "")
                if not target.get("project_id"):
                    target = {**target, "project_id": str(svc.get("project_id") or "")}
        except Exception as exc:
            errors.append(f"resolve_service: {exc}")

    if token and service_id and not environment_id and target.get("project_id"):
        try:
            from aethos_core.providers.railway.operations.mutations_api import resolve_environment_id

            resolved = resolve_environment_id(
                token,
                project_id=str(target["project_id"]),
                preferred_name=str(target.get("environment") or "production"),
            )
            if resolved:
                environment_id = str(resolved.get("environment_id") or "") or None
        except Exception as exc:
            errors.append(f"resolve_environment: {exc}")

    if service_name or service_id:
        sources_checked.append("runtime_logs_after")
        try:
            runtime_rows = fetch_runtime_logs_after(
                token or "",
                service_id=service_id,
                service_name=service_name,
                environment_id=environment_id,
                since_iso=since,
                limit=limit * 2,
            )
            merged.extend(runtime_rows)
        except Exception as exc:
            errors.append(f"runtime_logs_after: {exc}")

    if token and service_name:
        sources_checked.append("service_events")
        try:
            from aethos_core.providers.railway.api_client import find_service_by_name, list_service_deployments

            svc = find_service_by_name(token, service_name)
            if svc:
                sid = str(svc.get("service_id") or service_id)
                deployments = list_service_deployments(token, service_id=sid, limit=3)
                for dep in sorted(deployments, key=lambda d: str(d.get("created_at") or ""), reverse=True):
                    state = str(dep.get("state") or "")
                    created = normalize_railway_timestamp_to_utc(dep.get("created_at"))
                    if created:
                        merged.append(
                            {
                                "timestamp": created,
                                "level": "INFO",
                                "message": f"Deployment {dep.get('id')} state={state}",
                                "source": "service_events",
                            }
                        )
        except Exception as exc:
            errors.append(f"service_events: {exc}")

    selected = _dedupe_and_sort(merged, limit=limit)
    latest = selected[0]["timestamp"] if selected else None

    return {
        "ok": bool(selected),
        "logs": selected,
        "sources_checked": sources_checked,
        "errors": errors,
        "latest_timestamp": latest,
        "from_cache": False,
        "fetched_at": datetime.now(UTC).isoformat(),
        "since": since,
    }


def pick_newer_log_entries(
    cached: list[dict[str, Any]],
    fresh: list[dict[str, Any]],
    *,
    prefer_fresh: bool = True,
) -> list[dict[str, Any]]:
    """Choose log set with the newest timestamp; prefer fresh runtime logs on ties."""
    cached_latest = _latest_timestamp(cached)
    fresh_latest = _latest_timestamp(fresh)
    if prefer_fresh and fresh:
        if fresh_latest is None or cached_latest is None or fresh_latest >= cached_latest:
            return fresh
    if fresh_latest and cached_latest and fresh_latest > cached_latest:
        return fresh
    return cached or fresh


def _latest_timestamp(rows: list[dict[str, Any]]) -> str | None:
    latest: str | None = None
    for row in rows:
        ts = normalize_railway_timestamp_to_utc(row.get("timestamp"))
        if ts and (latest is None or ts > latest):
            latest = ts
    return latest


def _dedupe_and_sort(rows: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    seen: set[str] = set()
    runtime_first: list[dict[str, Any]] = []
    other: list[dict[str, Any]] = []
    for row in rows:
        ts = normalize_railway_timestamp_to_utc(row.get("timestamp")) or ""
        key = f"{ts}:{row.get('level')}:{row.get('message')}"
        if key in seen:
            continue
        seen.add(key)
        normalized = {**row, "timestamp": ts or row.get("timestamp")}
        if normalized.get("source") == "runtime_cli_logs":
            runtime_first.append(normalized)
        else:
            other.append(normalized)

    combined = runtime_first + other
    combined.sort(key=lambda row: str(row.get("timestamp") or ""), reverse=True)

    runtime_after = [row for row in runtime_first if row.get("timestamp")]
    if runtime_after:
        return runtime_after[:limit]

    return combined[:limit]
