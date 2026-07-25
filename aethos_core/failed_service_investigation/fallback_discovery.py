# SPDX-License-Identifier: Apache-2.0
"""Failed-service fallback discovery when provider-wide health cache is missing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.failed_service_investigation.failed_service_memory import get_health_report_meta, get_health_report_rows
from aethos_core.failed_service_investigation.failed_service_resolver import (
    FailedServiceResolution,
    InvestigationKind,
    resolve_failed_service_target,
)


@dataclass
class FallbackDiscoveryResult:
    discovered: bool = False
    refreshed: bool = False
    provider: str = "railway"
    error: str | None = None
    service_count: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


def cache_has_health_report(*, session_id: str = "default", provider: str = "railway") -> bool:
    meta = get_health_report_meta(session_id=session_id)
    if not meta.get("has_report"):
        return False
    if provider and meta.get("provider") and str(meta.get("provider")) != provider:
        return False
    return bool(get_health_report_rows(session_id=session_id, provider=provider))


def discover_provider_if_cache_missing(*, session_id: str = "default", provider: str = "railway") -> FallbackDiscoveryResult:
    if cache_has_health_report(session_id=session_id, provider=provider):
        return FallbackDiscoveryResult(discovered=False, refreshed=False, provider=provider)

    ok, error = refresh_health_report_if_needed(session_id=session_id, provider=provider)
    rows = get_health_report_rows(session_id=session_id, provider=provider)
    return FallbackDiscoveryResult(
        discovered=bool(rows),
        refreshed=ok,
        provider=provider,
        error=error,
        service_count=len(rows),
        meta={"discovery_source": "railway_inventory_refresh"},
    )


def refresh_health_report_if_needed(*, session_id: str = "default", provider: str = "railway") -> tuple[bool, str | None]:
    if provider != "railway":
        return False, f"fallback discovery not implemented for provider `{provider}`"

    from aethos_core.operational_planner.adapters.railway_wide_health import (
        build_health_payload,
        collect_railway_service_health_rows,
        summarize_health_rows,
    )
    from aethos_core.response_composition.response_composer import store_provider_wide_health_result

    rows, error = collect_railway_service_health_rows()
    if not rows:
        return False, error or "Railway inventory returned no services"

    summary = summarize_health_rows(rows)
    payload = build_health_payload(rows)
    store_provider_wide_health_result(
        session_id=session_id,
        provider="railway",
        payload=payload,
        summary={key: summary[key] for key in ("total", "healthy", "failed", "unknown")},
        scope="provider_wide",
    )
    return True, error


def resolve_failed_service_with_fallback(
    text: str,
    *,
    session_id: str = "default",
    kind: InvestigationKind | None = None,
    provider: str = "railway",
) -> tuple[FailedServiceResolution, FallbackDiscoveryResult]:
    resolution = resolve_failed_service_target(text, session_id=session_id, kind=kind, provider=provider)
    if resolution.ok or resolution.reason in {"ambiguous_service", "service_not_found", "not_investigation_request"}:
        return resolution, FallbackDiscoveryResult(provider=provider)

    if resolution.reason != "missing_health_report":
        return resolution, FallbackDiscoveryResult(provider=provider)

    discovery = discover_provider_if_cache_missing(session_id=session_id, provider=provider)
    if not discovery.discovered:
        return FailedServiceResolution(
            ok=False,
            kind=resolution.kind,
            reason="discovery_failed",
        ), discovery

    resolution = resolve_failed_service_target(text, session_id=session_id, kind=kind, provider=provider)
    return resolution, discovery


def format_discovery_preamble(*, discovery: FallbackDiscoveryResult, resolution: FailedServiceResolution) -> str:
    if not discovery.discovered:
        return ""
    lines = [
        "I don't have a fresh cached Railway health report, so I'll refresh Railway inventory first.",
        "",
    ]
    if resolution.ok and resolution.target is not None:
        row = resolution.target.row
        project = str(row.get("project") or "—")
        environment = str(row.get("environment") or "—")
        service = str(row.get("service") or "—")
        status = str(row.get("status") or row.get("health") or "unknown")
        lines.extend(
            [
                "I found:",
                f"- **{project} / {environment} / {service}**",
                f"- Status: **{status}**",
                "",
            ]
        )
    elif discovery.service_count:
        lines.append(f"I refreshed Railway inventory (**{discovery.service_count}** service(s)).")
        lines.append("")
    return "\n".join(lines)


def extract_target_label(text: str) -> str:
    from aethos_core.failed_service_investigation.global_preemption import classify_failed_service_intent
    from aethos_core.failed_service_investigation.failed_service_resolver import classify_failed_service_investigation

    kind = classify_failed_service_investigation(text)
    if kind == "none":
        return "that service"
    from aethos_core.failed_service_investigation.failed_service_resolver import _extract_phrase

    phrase = _extract_phrase(text, kind)
    return phrase or "that service"
