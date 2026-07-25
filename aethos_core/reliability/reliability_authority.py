# SPDX-License-Identifier: Apache-2.0
"""Reliability authority — canonical operational truth fusion."""

from __future__ import annotations

from typing import Any

from aethos_core.reliability.confidence_normalization import normalize_confidence
from aethos_core.reliability.execution_convergence import assess_execution_convergence
from aethos_core.reliability.operational_truth import resolve_truth_state
from aethos_core.reliability.replay_integrity import assess_replay_integrity
from aethos_core.reliability.verification_integrity import assess_verification_integrity


def assess_reliability_authority(
    *,
    observations: dict[str, Any] | None = None,
    anomalies: list[dict[str, Any]] | None = None,
    telemetry: dict[str, Any] | None = None,
    trust: dict[str, Any] | None = None,
    replays: list[dict[str, Any]] | None = None,
    attention_quality: dict[str, Any] | None = None,
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Fuse signals into canonical operational truth authority."""
    obs = observations or {}
    tel = telemetry or {}
    events = events or list(obs.get("events") or [])

    stale_sources = len((obs.get("telemetry_freshness") or {}).get("stale_sources") or [])
    tel_quality = str(tel.get("telemetry_quality") or "medium")
    raw_conf = float((trust or {}).get("confidence") or 0.72)

    high_anomalies = sum(1 for a in (anomalies or []) if str(a.get("severity")) == "high")
    if high_anomalies >= 2:
        raw_conf = min(raw_conf + 0.08, 0.9)
    inflation = float((attention_quality or {}).get("urgency_inflation_ratio") or 0)
    if inflation > 0.5:
        raw_conf -= 0.08

    replay = assess_replay_integrity(replays=replays)
    confidence = normalize_confidence(
        raw_conf,
        telemetry_quality=tel_quality,
        stale_sources=stale_sources,
        conflicting_evidence=high_anomalies >= 2 and tel_quality == "low",
        replay_gaps=int(replay.get("replay_gaps") or 0),
    )

    failure_events = [e for e in events if _is_failure_event(e)]
    verification = assess_verification_integrity(
        executed=len(failure_events) > 0 or bool(anomalies),
        verified=high_anomalies == 0 and tel_quality != "low",
        verification_errors=high_anomalies,
        stale_verification=bool((obs.get("telemetry_freshness") or {}).get("stale")),
    )
    convergence = assess_execution_convergence(events=events, verification=verification)
    truth = resolve_truth_state(
        verification=verification,
        replay=replay,
        confidence=confidence,
        convergence=convergence,
    )

    return {
        **truth,
        "verification": verification,
        "replay_integrity": replay,
        "confidence_detail": confidence,
        "convergence": convergence,
        "telemetry_quality": tel_quality,
        "readonly": True,
        "autonomous_execution_blocked": True,
    }


def _is_failure_event(event: dict[str, Any]) -> bool:
    text = f"{event.get('source')} {event.get('summary')} {event.get('category')}".lower()
    return any(k in text for k in ("fail", "restart", "rerun", "instability", "drift"))
