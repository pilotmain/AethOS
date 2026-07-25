# SPDX-License-Identifier: Apache-2.0
"""Shared Railway service hint extraction — preemption helpers after Wave 2 router deletion."""

from __future__ import annotations

import re
from typing import Any

_RAILWAY_RX = re.compile(r"\brailway\b", re.I)
_HEALTH_RX = re.compile(r"\bhealth\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)
_REPORT_RX = re.compile(r"\breport\s+back\b", re.I)

_POST_MUTATION_HEALTH_RX = re.compile(
    r"\b("
    r"after\s+restart|post[- ]restart|after\s+mutation|after\s+redeploy"
    r"|did\s+it\s+recover|did\s+the\s+restart|did\s+recovery\s+hold"
    r")\b",
    re.I,
)

_LOG_INTENT_RX = re.compile(
    r"\b("
    r"(?:give\s+me|show\s+me|get|fetch|check|tail|read|list)\s+(?:the\s+)?(?:some\s+)?(?:\d+\s+)?(?:top|latest|recent)?\s*\d*\s*logs?"
    r"|(?:top|latest|recent)\s+\d+\s+logs?"
    r"|logs?\s+(?:that\s+)?(?:show|prove|confirm|reflect)\s+(?:the\s+)?health"
    r"|logs?\s+for\s+each"
    r")\b",
    re.I,
)

_POST_MUTATION_LOG_RX = re.compile(
    r"\b("
    r"after\s+restart|post[- ]restart|after\s+mutation|after\s+redeploy"
    r"|did\s+it\s+recover|did\s+the\s+restart|startup\s+marker"
    r")\b",
    re.I,
)


def extract_railway_service_hints(text: str) -> list[str]:
    from aethos_core.providers.railway.railway_inventory_target_picker import extract_service_hints

    hints = extract_service_hints(text, project_hint="pilotos")
    cleaned = [hint for hint in hints if hint and "-" in hint]
    if cleaned:
        return cleaned
    found: list[str] = []
    for match in re.finditer(r"\b(aethos-(?:api|ui)|[\w-]+-(?:api|ui))\b", text or "", re.I):
        token = match.group(1).lower()
        if token not in found:
            found.append(token)
    return found


def filter_railway_health_rows(
    rows: list[dict[str, Any]],
    services: list[str],
    *,
    text: str = "",
) -> list[dict[str, Any]]:
    needles = {service.lower() for service in services}
    matched = [row for row in rows if str(row.get("service") or "").lower() in needles]
    if not matched:
        partial: list[dict[str, Any]] = []
        for row in rows:
            name = str(row.get("service") or "").lower()
            if any(needle in name or name in needle for needle in needles):
                partial.append(row)
        matched = partial
    if not matched:
        return []

    from aethos_core.providers.railway.railway_inventory_target_picker import (
        extract_environment_hint,
        extract_project_hint,
        infer_redeploy_environment,
    )

    project_hint = extract_project_hint(text, default="")
    env_hint = extract_environment_hint(text) or infer_redeploy_environment(text)
    if any("aethos" in needle for needle in needles):
        project_hint = project_hint or "pilotos"
        env_hint = env_hint or "staging"

    filtered = matched
    if project_hint:
        project_matches = [
            row for row in filtered if str(row.get("project") or "").lower() == project_hint.lower()
        ]
        if project_matches:
            filtered = project_matches
    if env_hint:
        env_matches = [
            row for row in filtered if str(row.get("environment") or "").lower() == env_hint.lower()
        ]
        if env_matches:
            filtered = env_matches
    return filtered if filtered else matched


def _has_named_railway_service_target(text: str) -> bool:
    services = extract_railway_service_hints(text)
    return bool(services) or bool(re.search(r"\baethos[-\w]*\b", text or "", re.I))


def is_railway_named_service_health_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or not _HEALTH_RX.search(raw) or not _RAILWAY_RX.search(raw):
        return False
    if _POST_MUTATION_HEALTH_RX.search(raw):
        return False
    return _has_named_railway_service_target(raw)


def mentions_railway_service_health(text: str) -> bool:
    return is_railway_named_service_health_request(text)


def is_multi_provider_health_request(text: str) -> bool:
    raw = (text or "").strip()
    if is_railway_named_service_health_request(raw):
        return True
    if not _HEALTH_RX.search(raw):
        return False
    has_railway = bool(_RAILWAY_RX.search(raw)) and _has_named_railway_service_target(raw)
    has_vercel = bool(_VERCEL_RX.search(raw))
    if has_railway and has_vercel:
        return True
    if has_railway and _REPORT_RX.search(raw):
        return True
    return False


def should_route_inline_health_check(text: str) -> bool:
    return is_multi_provider_health_request(text)


def should_defer_vercel_only_external_health(text: str) -> bool:
    return should_route_inline_health_check(text)


def _explicit_non_railway_log_target(text: str) -> bool:
    from aethos_core.operational_target_resolution.explicit_target_resolver import (
        resolve_explicit_operational_target,
    )

    explicit = resolve_explicit_operational_target(text)
    if explicit is None or not explicit.has_diagnostic_intent:
        return False
    if explicit.provider in {"vercel", "github"}:
        return True
    label = (explicit.vercel_project or explicit.alias or explicit.project or explicit.repo).lower()
    if label and "aethos" not in label and not _RAILWAY_RX.search(text):
        return True
    return False


def _has_recent_named_health_context(*, session_id: str) -> bool:
    from aethos_core.failed_service_investigation.failed_service_memory import get_health_report_rows
    from aethos_core.response_composition.operational_result_store import find_latest_provider_wide_health

    result = find_latest_provider_wide_health(session_id=session_id, provider="railway")
    if result is not None:
        meta = dict(result.meta or {})
        if meta.get("route_id") in {"multi_provider_health", "operational_conversation_kernel"} or result.scope == "named_service_health":
            return True
        services = list((result.result_payload or {}).get("services") or [])
        if any("aethos" in str(row.get("service") or "").lower() for row in services):
            return True
    rows = get_health_report_rows(session_id=session_id, provider="railway")
    return any("aethos" in str(row.get("service") or "").lower() for row in rows)


def is_railway_named_service_log_request(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw or not _LOG_INTENT_RX.search(raw):
        return False
    if _POST_MUTATION_LOG_RX.search(raw):
        return False
    if _explicit_non_railway_log_target(raw):
        return False

    services = extract_railway_service_hints(raw)
    if services:
        return True
    if _RAILWAY_RX.search(raw):
        return True
    if _HEALTH_RX.search(raw) and _has_recent_named_health_context(session_id=session_id):
        return True
    if re.search(r"\bfor\s+each\b", raw, re.I) and _has_recent_named_health_context(session_id=session_id):
        return True
    if _has_recent_named_health_context(session_id=session_id) and not _explicit_non_railway_log_target(raw):
        return True
    return False
