# SPDX-License-Identifier: Apache-2.0
"""Operational feed — unified presence stream."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.presence.paths import presence_artifacts_root
from aethos_core.presence.presence_memory import record_presence_event


def aggregate_operational_feed(*, window_hours: int = 48) -> list[dict[str, Any]]:
    """Collect feed events from operational subsystems — deduplicated before persist."""
    from aethos_core.presence.signal_deduplication import deduplicate_signals

    events = collect_raw_feed_events(window_hours=window_hours)
    deduped = deduplicate_signals(events)
    stored: list[dict[str, Any]] = []
    for event in deduped[:30]:
        art = store_feed_event(event)
        stored.append(art)
        if str(event.get("signal_class") or "") != "internal_substrate":
            record_presence_event(
                kind=event.get("source", "feed"),
                detail=str(event.get("summary") or ""),
                payload={"event_id": event.get("event_id")},
            )
    return stored


def collect_raw_feed_events(*, window_hours: int = 48) -> list[dict[str, Any]]:
    """Collect raw feed events without persisting."""
    events: list[dict[str, Any]] = []
    events.extend(_from_operational_patterns(window_hours))
    events.extend(_from_recommendations())
    events.extend(_from_engineering_state())
    events.extend(_from_workspace_artifacts())
    events.extend(_from_intelligence_anomalies())
    events.sort(key=lambda e: float(e.get("at") or 0), reverse=True)
    return events


def aggregate_operational_feed_legacy(*, window_hours: int = 48) -> list[dict[str, Any]]:
    return aggregate_operational_feed(window_hours=window_hours)


def store_feed_event(event: dict[str, Any]) -> dict[str, Any]:
    event_id = event.get("event_id") or f"pfee-{uuid4().hex[:12]}"
    record = {
        "artifact_type": "presence_feed_event",
        "event_id": event_id,
        "created_at": time(),
        **event,
    }
    path = presence_artifacts_root() / f"{event_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _update_feed_index(event_id)
    return record


def list_feed_events(*, limit: int = 30) -> list[dict[str, Any]]:
    index = presence_artifacts_root() / "feed_index.json"
    if not index.is_file():
        return []
    try:
        ids = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows: list[dict[str, Any]] = []
    for eid in ids[:limit]:
        path = presence_artifacts_root() / f"{eid}.json"
        if path.is_file():
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
    return rows


def _update_feed_index(event_id: str) -> None:
    index = presence_artifacts_root() / "feed_index.json"
    ids: list[str] = []
    if index.is_file():
        try:
            ids = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            ids = []
    ids.insert(0, event_id)
    index.write_text(json.dumps(ids[:300], indent=2), encoding="utf-8")


def _from_operational_patterns(window_hours: int) -> list[dict[str, Any]]:
    from aethos_core.agents.memory.operational_patterns import get_operational_patterns_memory

    memory = get_operational_patterns_memory()
    cutoff = time() - window_hours * 3600
    events: list[dict[str, Any]] = []
    for row in memory.get("events") or []:
        if float(row.get("at") or 0) < cutoff:
            continue
        cat = str(row.get("category") or "operational")
        detail = str(row.get("detail") or cat)
        signal_class = "internal_substrate" if "repo_drift" in detail or cat == "operational_drift" else None
        events.append(
            _feed_item(
                source=cat,
                summary=detail,
                severity=_severity_for_category(cat),
                provider=row.get("provider"),
                signal_class=signal_class,
            )
        )
    return events


def _from_recommendations() -> list[dict[str, Any]]:
    from aethos_core.intelligence.recommendations import list_recommendations

    events: list[dict[str, Any]] = []
    for rec in list_recommendations(limit=10):
        events.append(
            _feed_item(
                source="recommendation",
                summary=str(rec.get("title") or rec.get("suggested_action")),
                severity=str(rec.get("severity") or "medium"),
                confidence=float(rec.get("confidence") or 0.7),
                recurrence=1,
                operational_impact=rec.get("approval_required"),
                extra={"recommendation_id": rec.get("recommendation_id")},
            )
        )
    return events


def _from_engineering_state() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        from aethos_core.engineering.governance.engineering_preflight_store import list_pending_preflights

        for pf in list_pending_preflights(limit=5):
            events.append(
                _feed_item(
                    source="engineering",
                    summary=f"Pending preflight: {pf.get('task', {}).get('title', 'engineering')}",
                    severity="elevated",
                    operational_impact=True,
                    extra={"preflight_id": pf.get("preflight_id")},
                )
            )
    except Exception:
        pass
    return events


def _from_workspace_artifacts() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        from aethos_core.workspace_runtime.workspace_artifacts import list_workspace_runtime_artifacts

        for art in list_workspace_runtime_artifacts(limit=8):
            if art.get("artifact_type") in ("workspace_policy_denial", "workspace_terminal_output"):
                events.append(
                    _feed_item(
                        source="workspace",
                        summary=str(art.get("summary") or art.get("artifact_type")),
                        severity="medium" if "denial" in str(art.get("artifact_type")) else "low",
                    )
                )
    except Exception:
        pass
    return events


def _from_intelligence_anomalies() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        from aethos_core.intelligence.anomaly_engine import detect_operational_anomalies
        from aethos_core.operations.reality_loop import collect_operational_observations

        anomalies = detect_operational_anomalies(observations=collect_operational_observations())
        for a in anomalies[:6]:
            events.append(
                _feed_item(
                    source="operational_intelligence",
                    summary=str(a.get("summary") or a.get("kind")),
                    severity=str(a.get("severity") or "medium"),
                    confidence=float(a.get("confidence") or 0.7),
                    operational_impact=True,
                    extra={"anomaly_id": a.get("anomaly_id")},
                )
            )
    except Exception:
        pass
    return events


def _feed_item(
    *,
    source: str,
    summary: str,
    severity: str = "low",
    confidence: float = 0.6,
    recurrence: int = 0,
    operational_impact: bool = False,
    provider: str | None = None,
    signal_class: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": f"pfee-{uuid4().hex[:12]}",
        "at": time(),
        "source": source,
        "summary": summary[:240],
        "severity": severity,
        "confidence": confidence,
        "recurrence": recurrence,
        "operational_impact": operational_impact,
        "provider": provider,
        "signal_class": signal_class,
        **(extra or {}),
    }


def _severity_for_category(cat: str) -> str:
    if cat in ("flaky_workflow", "deployment_instability", "provider_auth_failure"):
        return "high"
    if cat in ("browser_evidence_failure", "dependency_churn"):
        return "medium"
    return "low"


def clear_operational_feed_for_tests() -> None:
    root = presence_artifacts_root()
    if root.is_dir():
        for p in root.glob("*.json"):
            p.unlink()
