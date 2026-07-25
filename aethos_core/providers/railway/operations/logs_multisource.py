# SPDX-License-Identifier: Apache-2.0
"""Fetch Railway logs from deployment, runtime, and CLI evidence surfaces."""

from __future__ import annotations

from typing import Any


def fetch_railway_logs_multisource(
    *,
    service_name: str,
    limit: int = 5,
    since_iso: str | None = None,
    approval_time: str | None = None,
    bypass_cache: bool = True,
    service_id: str | None = None,
    environment_id: str | None = None,
) -> dict[str, Any]:
    """Fetch fresh Railway logs across runtime, deployment, and service-event sources."""
    since = since_iso or approval_time
    target = {
        "service_name": service_name,
        "service_id": service_id or "",
        "environment_id": environment_id or "",
    }

    if bypass_cache:
        from aethos_core.providers.railway.railway_log_evidence import fetch_fresh_logs_for_verification

        fresh_payload = fetch_fresh_logs_for_verification(
            target=target,
            approval_time=since,
            bypass_cache=True,
            limit=max(limit, 5),
        )
        if fresh_payload.get("ok"):
            return fresh_payload
        sources_checked: list[str] = list(fresh_payload.get("sources_checked") or [])
        errors: list[str] = list(fresh_payload.get("errors") or [])
    else:
        sources_checked = []
        errors = []

    from aethos_core.operational_thread_memory.railway_log_evidence import normalize_log_entries

    merged: list[dict[str, Any]] = []

    token = None
    try:
        from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

        token, _, err = resolve_railway_mutation_credentials()
        if err:
            errors.append(str(err))
    except Exception as exc:
        errors.append(str(exc))

    if token:
        try:
            from aethos_core.providers.railway.api_client import fetch_deployment_logs, find_service_by_name, list_service_deployments
            from aethos_core.providers.railway.railway_log_evidence import normalize_railway_timestamp_to_utc

            svc = find_service_by_name(token, service_name)
            if svc:
                since_norm = normalize_railway_timestamp_to_utc(since) if since else None
                deployments = list_service_deployments(token, service_id=str(svc["service_id"]), limit=5)
                deployments.sort(key=lambda dep: str(dep.get("created_at") or ""), reverse=True)
                sources_checked.append("deployment_logs")
                for dep in deployments:
                    dep_id = dep.get("id")
                    if not dep_id:
                        continue
                    rows = fetch_deployment_logs(token, deployment_id=str(dep_id))
                    for entry in normalize_log_entries(rows):
                        row = entry.to_dict()
                        if since_norm and row.get("timestamp") and str(row["timestamp"]) <= since_norm:
                            continue
                        merged.append(row)
                    if len(merged) >= limit * 3:
                        break
            else:
                errors.append(f"Service `{service_name}` not found via Railway API.")
        except Exception as exc:
            errors.append(f"deployment_logs: {exc}")

    try:
        from aethos_core.providers.railway.cli_executor import railway_logs
        from aethos_core.providers.railway.railway_log_evidence import normalize_railway_timestamp_to_utc

        sources_checked.append("runtime_cli_logs")
        since_norm = normalize_railway_timestamp_to_utc(since) if since else None
        cli_since = since_norm.replace("T", " ").replace("Z", "") if since_norm else None
        raw = list((railway_logs(service_name=service_name, since=cli_since).get("logs") or []))
        for entry in normalize_log_entries(raw):
            merged.append({**entry.to_dict(), "source": "runtime_cli_logs"})
    except Exception as exc:
        errors.append(f"runtime_cli_logs: {exc}")

    if token and not merged:
        try:
            from aethos_core.providers.railway.operations.logs_api import fetch_service_logs

            sources_checked.append("service_logs_api")
            payload = fetch_service_logs(token, service_name=service_name)
            if payload.get("ok"):
                for entry in normalize_log_entries(payload.get("logs") or []):
                    merged.append(entry.to_dict())
            elif payload.get("error"):
                errors.append(str(payload.get("error")))
        except Exception as exc:
            errors.append(f"service_logs_api: {exc}")

    deduped = _dedupe_logs(merged)
    deduped.sort(key=lambda row: str(row.get("timestamp") or ""), reverse=True)
    selected = deduped[:limit]

    return {
        "ok": bool(selected),
        "logs": selected,
        "sources_checked": sources_checked,
        "errors": errors,
        "all_sources_failed": not selected and bool(sources_checked),
        "from_cache": False,
    }


def fetch_railway_service_logs_fast(
    *,
    service_name: str,
    service_id: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """API-only log fetch for inline chat diagnostics — avoids slow CLI multisource waterfall."""
    from aethos_core.operational_thread_memory.railway_log_evidence import normalize_log_entries
    from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

    token, _, err = resolve_railway_mutation_credentials()
    errors: list[str] = []
    if err:
        errors.append(str(err))
    if not token:
        return {
            "ok": False,
            "logs": [],
            "sources_checked": [],
            "errors": errors or ["Railway credentials missing."],
        }

    from aethos_core.providers.railway.api_client import (
        fetch_deployment_logs,
        find_service_by_name,
        list_service_deployments,
    )

    sid = str(service_id or "").strip()
    if not sid:
        svc = find_service_by_name(token, service_name)
        if svc:
            sid = str(svc.get("service_id") or "")
        else:
            errors.append(f"Service `{service_name}` not found via Railway API.")
            return {"ok": False, "logs": [], "sources_checked": ["resolve_service"], "errors": errors}

    sources_checked = ["deployment_logs"]
    merged: list[dict[str, Any]] = []
    deployments = list_service_deployments(token, service_id=sid, limit=3)
    deployments.sort(key=lambda dep: str(dep.get("created_at") or ""), reverse=True)
    for dep in deployments:
        dep_id = dep.get("id")
        if not dep_id:
            continue
        rows = fetch_deployment_logs(token, deployment_id=str(dep_id))
        for entry in normalize_log_entries(rows):
            merged.append({**entry.to_dict(), "source": "deployment_logs"})
        if merged:
            break

    if not merged:
        from aethos_core.providers.railway.operations.logs_api import fetch_service_logs

        sources_checked.append("service_logs_api")
        payload = fetch_service_logs(token, service_name=service_name)
        if payload.get("ok"):
            for entry in normalize_log_entries(payload.get("logs") or []):
                merged.append({**entry.to_dict(), "source": "service_logs_api"})
        elif payload.get("error"):
            errors.append(str(payload.get("error")))

    merged.sort(key=lambda row: str(row.get("timestamp") or ""), reverse=True)
    selected = merged[:limit]
    return {
        "ok": bool(selected),
        "logs": selected,
        "sources_checked": sources_checked,
        "errors": errors,
        "all_sources_failed": not selected and bool(sources_checked),
        "from_cache": False,
    }


def _dedupe_logs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = f"{row.get('timestamp')}:{row.get('level')}:{row.get('message')}"
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out
