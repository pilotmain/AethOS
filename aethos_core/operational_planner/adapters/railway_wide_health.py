# SPDX-License-Identifier: Apache-2.0
"""Railway provider-wide health and inventory reporting."""

from __future__ import annotations

import re
from typing import Any

_FAILED_FOLLOWUP_RX = re.compile(
    r"\b("
    r"which\s+services?\s+failed"
    r"|what\s+services?\s+failed"
    r"|show\s+(?:me\s+)?(?:only\s+)?failed"
    r"|list\s+(?:the\s+)?failed\s+services?"
    r"|failed\s+services?"
    r"|only\s+failed"
    r")\b",
    re.I,
)

_FIX_FIRST_RX = re.compile(
    r"\b("
    r"what\s+should\s+i\s+fix\s+first"
    r"|what\s+to\s+fix\s+first"
    r"|which\s+(?:one|service)\s+should\s+i\s+fix\s+first"
    r"|priority\s+fix(?:es)?"
    r")\b",
    re.I,
)

_UNKNOWN_FOLLOWUP_RX = re.compile(
    r"\b("
    r"which\s+services?\s+(?:are\s+)?unknown"
    r"|show\s+(?:me\s+)?unknown"
    r"|unknown\s+services?"
    r")\b",
    re.I,
)


def _classify_status_and_health(service_status: str, deployment_state: str) -> tuple[str, str]:
    dep = (deployment_state or "unknown").lower()
    svc = (service_status or "unknown").lower()

    if dep in {"failed", "crashed", "error", "removed"} or svc in {"failed", "crashed", "error"}:
        return "failed", "failed"
    if dep in {"building", "deploying", "queued", "pending"}:
        return "deploying", "unknown"
    if dep in {
        "success",
        "active",
        "running",
        "deployed",
        "completed",
        "ready",
        "sleeping",
    } or svc in {
        "online",
        "running",
        "active",
        "success",
    }:
        return "running", "healthy"
    if svc == "online":
        return "running", "healthy"
    return "unknown", "unknown"


def summarize_health_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    healthy = sum(1 for row in rows if row.get("health") == "healthy")
    failed_rows = [row for row in rows if row.get("health") == "failed" or row.get("status") == "failed"]
    unknown_rows = [
        row
        for row in rows
        if row not in failed_rows and (row.get("health") == "unknown" or row.get("status") in {"unknown", "deploying"})
    ]
    return {
        "total": len(rows),
        "healthy": healthy,
        "failed": len(failed_rows),
        "unknown": len(unknown_rows),
        "failed_rows": failed_rows,
        "unknown_rows": unknown_rows,
    }


def build_health_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = summarize_health_rows(rows)
    return {
        "services": list(rows),
        "counts": {key: summary[key] for key in ("total", "healthy", "failed", "unknown")},
        "failures": list(summary["failed_rows"]),
        "unknown": list(summary["unknown_rows"]),
    }


def _attention_label(row: dict[str, Any]) -> str:
    project = str(row.get("project") or "—")
    environment = str(row.get("environment") or "—")
    service = str(row.get("service") or "—")
    state = str(row.get("health") or row.get("status") or "unknown")
    dep = str(row.get("deployment_state") or "")
    dep_suffix = f" (deployment: {dep})" if dep and dep != "unknown" else ""
    return f"{project} / {environment} / {service} — {state}{dep_suffix}"


def _enrich_health_rows_with_live_deployments(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Probe latest deployment when inventory topology omits deployment status."""
    needs_probe = any(
        str(row.get("deployment_state") or "unknown").lower() == "unknown"
        and str(row.get("service_id") or "")
        for row in rows
    )
    if not needs_probe:
        return rows

    from aethos_core.providers.railway.api_client import list_service_deployments
    from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

    token, _, _ = resolve_railway_mutation_credentials()
    if not token:
        return rows

    enriched: list[dict[str, Any]] = []
    for row in rows:
        row = dict(row)
        if str(row.get("deployment_state") or "unknown").lower() != "unknown":
            enriched.append(row)
            continue
        service_id = str(row.get("service_id") or "")
        if not service_id:
            enriched.append(row)
            continue
        deployments = list_service_deployments(token, service_id=service_id, limit=1)
        latest = deployments[0] if deployments else {}
        dep_state = str(latest.get("state") or "unknown")
        row["deployment_state"] = dep_state
        if latest.get("id"):
            row["deployment_id"] = latest.get("id")
        if latest.get("created_at"):
            row["deployment_created_at"] = latest.get("created_at")
        if latest.get("url"):
            row["deployment_url"] = latest.get("url")
        status, health = _classify_status_and_health("", dep_state)
        row["status"] = status
        row["health"] = health
        enriched.append(row)
    return enriched


def format_health_report_body(
    rows: list[dict[str, Any]],
    *,
    intro: str = "I checked all Railway services.",
    include_full_table: bool = True,
    filter_mode: str = "all",
) -> str:
    summary = summarize_health_rows(rows)
    display_rows = rows
    if filter_mode == "failed":
        display_rows = list(summary["failed_rows"])
    elif filter_mode == "unknown":
        display_rows = list(summary["unknown_rows"])

    lines = [
        intro,
        "",
        "Summary:",
        f"- Total: **{summary['total']}**",
        f"- Healthy/running: **{summary['healthy']}**",
        f"- Failed: **{summary['failed']}**",
        f"- Unknown: **{summary['unknown']}**",
    ]

    needs_attention: list[str] = []
    for row in summary["failed_rows"]:
        needs_attention.append(f"- {_attention_label(row)}")
    for row in summary["unknown_rows"]:
        needs_attention.append(f"- {_attention_label(row)}")

    if needs_attention and filter_mode == "all":
        lines.extend(["", "Needs attention:"])
        lines.extend(needs_attention)

    if filter_mode == "failed" and summary["failed_rows"]:
        lines.extend(["", "Failed services:"])
        for row in summary["failed_rows"]:
            lines.append(f"- {_attention_label(row)}")
    elif filter_mode == "unknown" and summary["unknown_rows"]:
        lines.extend(["", "Unknown services:"])
        for row in summary["unknown_rows"]:
            lines.append(f"- {_attention_label(row)}")

    if include_full_table and display_rows:
        lines.extend(["", "Full inventory:", ""])
        lines.extend(_format_table(display_rows))
    elif filter_mode != "all" and not display_rows:
        lines.extend(["", "(No matching services in the last provider-wide health report.)"])

    return "\n".join(lines)


def _format_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Service | Project | Environment | Status | Health |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['service']} | {row['project']} | {row['environment']} | {row['status']} | {row['health']} |"
        )
    return lines


def collect_railway_service_health_rows() -> tuple[list[dict[str, Any]], str | None]:
    from aethos_core.operational_planner.adapters.railway_wide_health_certification import (
        certification_fixture_rows,
        is_certification_mode,
    )

    if is_certification_mode():
        return certification_fixture_rows(), None

    from aethos_core.operational_planner.adapters.railway_wide_health_cache import (
        is_rate_limit_error,
        load_cached_railway_health_rows,
        save_cached_railway_health_rows,
    )
    from aethos_core.providers.railway.discovery import discover_railway_inventory

    inventory = discover_railway_inventory()
    if inventory.error and not inventory.projects:
        if is_rate_limit_error(str(inventory.error)):
            cached_rows, cached_at = load_cached_railway_health_rows()
            if cached_rows:
                note = (
                    "cached_due_to_rate_limit"
                    f"{f' (snapshot from {cached_at})' if cached_at else ''}: {inventory.error}"
                )
                return cached_rows, note
        return [], str(inventory.error)

    rows: list[dict[str, Any]] = []
    for project in inventory.projects:
        for environment in project.environments:
            for service in environment.services:
                dep = service.latest_deployment
                dep_state = dep.status if dep is not None else "unknown"
                status, health = _classify_status_and_health(service.status, dep_state)
                rows.append(
                    {
                        "service": service.name,
                        "project": project.name,
                        "environment": environment.name,
                        "status": status,
                        "health": health,
                        "deployment_state": dep_state,
                        "service_id": service.id,
                    }
                )
    rows = _enrich_health_rows_with_live_deployments(rows)
    rows.sort(key=lambda row: (str(row.get("project") or ""), str(row.get("service") or "")))
    if rows:
        save_cached_railway_health_rows(rows)
    return rows, inventory.error


def is_provider_wide_health_followup(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if _FIX_FIRST_RX.search(raw):
        return "fix_first"
    if _FAILED_FOLLOWUP_RX.search(raw):
        return "failed_only"
    if _UNKNOWN_FOLLOWUP_RX.search(raw):
        return "unknown_only"
    return None


def compose_provider_wide_health_followup(
    text: str,
    *,
    session_id: str = "default",
    provider: str = "railway",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.response_composition.response_composer import try_compose_rerender_reply

    _ = provider
    return try_compose_rerender_reply(text, session_id=session_id)


def compose_railway_provider_wide_health_reply(
    *,
    user_text: str = "",
    active_service: str = "",
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.operational_planner.adapters.railway_wide_health_cache import (
        is_rate_limit_error,
        parse_rate_limit_retry_seconds,
    )

    rows, error = collect_railway_service_health_rows()

    intro = "I checked all Railway services."
    if active_service:
        intro += f"\n\n(Active thread was `{active_service}` — this request is **provider-wide**, not that single service.)"

    using_cached = bool(error and str(error).startswith("cached_due_to_rate_limit"))
    if using_cached and rows:
        intro += (
            "\n\nRailway provider-wide health is temporarily rate-limited. "
            "Using last known snapshot.\n"
            "**Source:** cached_due_to_rate_limit"
        )

    if error and not rows:
        if is_rate_limit_error(str(error)):
            retry = parse_rate_limit_retry_seconds(str(error))
            retry_line = f"Try again after: **{retry}** seconds\n\n" if retry else ""
            body = (
                f"{intro}\n\n"
                "Railway provider-wide health is temporarily rate-limited.\n\n"
                f"Reason: {error}\n\n"
                f"{retry_line}"
                "No mutation has been performed."
            )
            return body, "railway_provider_wide_health_rate_limited", {
                "provider": "railway",
                "scope": "provider_wide",
                "source": "rate_limited",
            }
        body = (
            f"{intro}\n\n"
            "I could not retrieve Railway service inventory.\n\n"
            f"Reason: {error}\n\n"
            "Add a Railway API token in **Mission Control → Advanced settings → Credentials → Railway**.\n\n"
            "No mutation has been performed."
        )
        return body, "railway_provider_wide_health_unavailable", {"provider": "railway", "scope": "provider_wide"}

    if not rows:
        body = f"{intro}\n\nRailway inventory completed, but no services were returned for this account/token."
        return body, "railway_provider_wide_health_empty", {"provider": "railway", "scope": "provider_wide"}

    from aethos_core.response_composition.response_composer import (
        compose_operational_response,
        store_provider_wide_health_result,
    )
    from aethos_core.response_composition.response_intent_classifier import classify_response_intent

    summary = summarize_health_rows(rows)
    payload = build_health_payload(rows)
    counts = {key: summary[key] for key in ("total", "healthy", "failed", "unknown")}
    result = store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload=payload,
        summary=counts,
        scope="provider_wide",
    )

    response_intent = classify_response_intent(user_text, session_id=session_id)
    output_format = response_intent.output_format
    filter_mode = response_intent.filter_mode if response_intent.kind == "filter" else "all"

    body, intent, meta = compose_operational_response(
        result,
        output_format=output_format,
        filter_mode=filter_mode,
        intro=intro,
        session_id=session_id,
    )
    if user_text:
        body += f"\n\n_Request:_ {user_text[:240]}"

    meta.update(
        {
            "provider": "railway",
            "scope": "provider_wide",
            "service_count": str(summary["total"]),
            "healthy_count": str(summary["healthy"]),
            "failed_count": str(summary["failed"]),
            "unknown_count": str(summary["unknown"]),
            "output_format": output_format,
        }
    )
    if using_cached:
        meta["source"] = "cached_due_to_rate_limit"
    return body, intent, meta


def compose_provider_wide_stub_reply(*, provider: str, intent: str) -> tuple[str, str, dict[str, str]]:
    body = (
        f"I recognized a **provider-wide** `{intent.replace('_', ' ')}` request for **{provider}**, "
        f"but that provider-wide adapter is not implemented yet.\n\n"
        "I will not narrow this to the active service thread."
    )
    return body, "provider_wide_capability_gap", {"provider": provider, "scope": "provider_wide", "intent": intent}
