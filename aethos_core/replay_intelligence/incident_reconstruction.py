# SPDX-License-Identifier: Apache-2.0
"""Incident reconstruction — rebuild operational sequences."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.replay_intelligence.causality_engine import infer_causal_chain
from aethos_core.replay_intelligence.operational_story import build_operational_story
from aethos_core.replay_intelligence.replay_confidence import score_replay_confidence
from aethos_core.replay_intelligence.replay_graph import build_replay_graph


def reconstruct_incident_timeline(*, window_hours: int = 48) -> dict[str, Any]:
    """Reconstruct operational incident timeline from available evidence."""
    events = _collect_events(window_hours)
    chains = infer_causal_chain(events)
    graph = build_replay_graph(events=events, chains=chains)
    confidence = score_replay_confidence(replays=_load_replays(), graph=graph, chains=chains)
    story = build_operational_story(chains=chains, events=events, window_hours=window_hours)

    return {
        "ok": True,
        "window_hours": window_hours,
        "event_count": len(events),
        "causal_chains": chains,
        "replay_graph": graph,
        "replay_confidence": confidence,
        "operational_story": story,
        "reconstructed_at": time(),
        "readonly": True,
        "autonomous_execution_blocked": True,
    }


def _collect_events(window_hours: int) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        from aethos_core.agents.memory.operational_patterns import get_operational_patterns_memory

        cutoff = time() - window_hours * 3600
        for row in get_operational_patterns_memory().get("events") or []:
            if float(row.get("at") or 0) >= cutoff:
                events.append(row)
    except Exception:
        pass
    try:
        from aethos_core.presence.operational_feed import collect_raw_feed_events

        events.extend(collect_raw_feed_events(window_hours=window_hours))
    except Exception:
        pass
    events.sort(key=lambda e: float(e.get("at") or 0))
    return events


def _load_replays() -> list[dict[str, Any]]:
    try:
        from aethos_core.intelligence.operational_replay import list_operational_replays

        return list_operational_replays(limit=10)
    except Exception:
        return []
