# SPDX-License-Identifier: Apache-2.0
"""Evidence freshness assessment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

Freshness = Literal["fresh", "stale", "unknown"]

LOG_FRESH_MINUTES = 15
EVENT_FRESH_HOURS = 24
INVENTORY_FRESH_MINUTES = 10
HEALTH_FRESH_MINUTES = 5


@dataclass
class SourceFreshness:
    source: str
    freshness: Freshness
    latest_timestamp: datetime | None = None
    age_seconds: float | None = None
    detail: str = ""


def parse_timestamp(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw or raw in {"—", "-", "unknown"}:
        return None
    normalized = raw.replace("Z", "+00:00")
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            parsed = datetime.strptime(normalized.replace("+00:00", ""), fmt.replace("%z", ""))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except ValueError:
            continue
    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return None


def _freshness_for_age(*, age: timedelta, fresh_limit: timedelta) -> Freshness:
    if age <= fresh_limit:
        return "fresh"
    return "stale"


def assess_log_freshness(
    logs: list[dict[str, Any]],
    *,
    reference_time: datetime | None = None,
) -> SourceFreshness:
    now = reference_time or datetime.now(tz=UTC)
    timestamps = [
        ts
        for entry in logs
        if (ts := parse_timestamp(entry.get("timestamp") or entry.get("time") or entry.get("created_at")))
    ]
    if not timestamps:
        return SourceFreshness(
            source="runtime_logs",
            freshness="unknown",
            detail="No log timestamps available",
        )
    latest = max(timestamps)
    age = now - latest
    freshness = _freshness_for_age(age=age, fresh_limit=timedelta(minutes=LOG_FRESH_MINUTES))
    return SourceFreshness(
        source="runtime_logs",
        freshness=freshness,
        latest_timestamp=latest,
        age_seconds=age.total_seconds(),
        detail=f"latest log at {latest.isoformat()}",
    )


def assess_event_freshness(
    events: list[dict[str, Any]],
    *,
    reference_time: datetime | None = None,
) -> SourceFreshness:
    now = reference_time or datetime.now(tz=UTC)
    timestamps = [ts for event in events if (ts := parse_timestamp(event.get("created_at")))]
    if not timestamps:
        return SourceFreshness(
            source="service_events",
            freshness="unknown",
            detail="No service event timestamps available",
        )
    latest = max(timestamps)
    age = now - latest
    freshness = _freshness_for_age(age=age, fresh_limit=timedelta(hours=EVENT_FRESH_HOURS))
    return SourceFreshness(
        source="service_events",
        freshness=freshness,
        latest_timestamp=latest,
        age_seconds=age.total_seconds(),
        detail=f"latest event at {latest.isoformat()}",
    )


def assess_inventory_freshness(
    *,
    collected_at: datetime | None,
    reference_time: datetime | None = None,
) -> SourceFreshness:
    now = reference_time or datetime.now(tz=UTC)
    if collected_at is None:
        return SourceFreshness(source="provider_inventory", freshness="unknown", detail="Inventory age unknown")
    age = now - collected_at
    freshness = _freshness_for_age(age=age, fresh_limit=timedelta(minutes=INVENTORY_FRESH_MINUTES))
    return SourceFreshness(
        source="provider_inventory",
        freshness=freshness,
        latest_timestamp=collected_at,
        age_seconds=age.total_seconds(),
        detail=f"inventory collected at {collected_at.isoformat()}",
    )


def assess_health_freshness(
    *,
    collected_at: datetime | None,
    reference_time: datetime | None = None,
) -> SourceFreshness:
    now = reference_time or datetime.now(tz=UTC)
    if collected_at is None:
        return SourceFreshness(source="health_check", freshness="unknown", detail="Health check age unknown")
    age = now - collected_at
    freshness = _freshness_for_age(age=age, fresh_limit=timedelta(minutes=HEALTH_FRESH_MINUTES))
    return SourceFreshness(
        source="health_check",
        freshness=freshness,
        latest_timestamp=collected_at,
        age_seconds=age.total_seconds(),
        detail=f"health check at {collected_at.isoformat()}",
    )


def is_low_signal_logs(logs: list[dict[str, Any]], *, root_category: str = "") -> bool:
    if not logs:
        return True
    if root_category in {
        "database_startup_or_storage_activity",
        "insufficient_evidence",
        "unknown_runtime_failure",
    }:
        return True
    corpus = " ".join(str(entry.get("message") or entry.get("msg") or "") for entry in logs).lower()
    if "wiredtiger" in corpus and not any(token in corpus for token in ("fatal", "error", "exit code", "corrupt", "oom")):
        return True
    return False
