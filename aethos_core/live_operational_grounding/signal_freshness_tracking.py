# SPDX-License-Identifier: Apache-2.0
"""Signal freshness tracking — unified operational truth freshness."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.intelligence.confidence_authority import evidence_freshness_hours


_STALE_HOURS = 12.0
_RECENT_HOURS = 2.0


def _freshness_tier(age_hours: float | None) -> str:
    if age_hours is None:
        return "unknown"
    if age_hours <= _RECENT_HOURS:
        return "current"
    if age_hours <= _STALE_HOURS:
        return "recently_verified"
    return "stale"


def track_signal_freshness(
    *,
    session_id: str = "default",
    channel: str = "chat",
    provider_checked_at: float | None = None,
) -> dict[str, Any]:
    """Unify freshness across provider truth, context store, MC, and Telegram memory."""
    sources: dict[str, Any] = {}

    try:
        from aethos_core.operational_context_memory.context_store import recall_operational_context

        stored = recall_operational_context(session_id=session_id)
        ctx_age = evidence_freshness_hours(stored.get("updated_at"))
        sources["operational_context"] = {
            "updated_at": stored.get("updated_at"),
            "age_hours": ctx_age,
            "tier": _freshness_tier(ctx_age),
        }
    except Exception:
        sources["operational_context"] = {"tier": "unknown"}

    try:
        from aethos_core.human_centered.continuity_memory import load_continuity_memory

        hc = load_continuity_memory(session_id=session_id)
        mc_age = evidence_freshness_hours(hc.get("updated_at"))
        sources["mission_control"] = {
            "updated_at": hc.get("updated_at"),
            "age_hours": mc_age,
            "tier": _freshness_tier(mc_age),
        }
    except Exception:
        sources["mission_control"] = {"tier": "unknown"}

    provider_age = evidence_freshness_hours(provider_checked_at or time())
    sources["provider_truth"] = {
        "checked_at": provider_checked_at or time(),
        "age_hours": provider_age,
        "tier": _freshness_tier(provider_age),
    }

    if channel == "telegram" or session_id.startswith("tg-"):
        sources["telegram_memory"] = sources.get("operational_context", {"tier": "unknown"})

    stale_sources = [name for name, meta in sources.items() if meta.get("tier") == "stale"]
    unknown_sources = [name for name, meta in sources.items() if meta.get("tier") == "unknown"]
    signals_fresh = len(stale_sources) == 0 and len(unknown_sources) <= 2

    if stale_sources:
        operational_state = "contradictory" if len(stale_sources) >= 2 else "stale_memory"
    elif not signals_fresh:
        operational_state = "missing_runtime_evidence"
    elif all(meta.get("tier") == "current" for meta in sources.values() if meta.get("tier") != "unknown"):
        operational_state = "current_truth"
    else:
        operational_state = "recently_verified"

    state_labels = {
        "current_truth": "actively verified",
        "recently_verified": "still reliable",
        "stale_memory": "continuity only",
        "contradictory": "degraded confidence",
        "missing_runtime_evidence": "not operationally confirmed",
    }

    return {
        "sources": sources,
        "stale_sources": stale_sources,
        "signals_fresh": signals_fresh,
        "stale": bool(stale_sources),
        "operational_state": operational_state,
        "operational_state_label": state_labels.get(operational_state, "unknown"),
        "summary": (
            "Operational signals are current across tracked surfaces."
            if signals_fresh
            else f"Stale operational signals detected: {', '.join(stale_sources) or 'unknown freshness'}."
        ),
    }
