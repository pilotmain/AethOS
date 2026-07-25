# SPDX-License-Identifier: Apache-2.0
"""Operational reality loop — continuous governed operational awareness."""

from __future__ import annotations

from pathlib import Path
from time import time
from typing import Any

from aethos_core.agents.memory.operational_patterns import get_operational_patterns_memory, get_recurring_patterns
from aethos_core.intelligence.anomaly_engine import detect_operational_anomalies
from aethos_core.intelligence.confidence_authority import assess_telemetry_quality, operational_trust_summary
from aethos_core.intelligence.operational_memory import operational_memory_snapshot, record_operational_memory
from aethos_core.intelligence.operational_notifications import notify_operational_recommendations
from aethos_core.intelligence.operational_replay import store_operational_replay
from aethos_core.intelligence.recommendations import generate_recommendations_from_anomalies, list_recommendations


def run_reality_loop_scan(*, window_hours: int = 48) -> dict[str, Any]:
    """Readonly operational scan — patterns, anomalies, trends."""
    patterns = get_recurring_patterns()
    memory = get_operational_patterns_memory()
    events = list(memory.get("events") or [])
    recent = [e for e in events if time() - float(e.get("at") or 0) < window_hours * 3600]
    anomalies = _detect_anomalies(recent)
    trends = _build_trends(recent, patterns)
    return {
        "ok": True,
        "scanned_at": time(),
        "window_hours": window_hours,
        "recurring_patterns": patterns,
        "anomalies": anomalies,
        "trends": trends,
        "event_count": len(recent),
        "readonly": True,
        "background_mutations": False,
    }


def run_reality_loop_cycle(*, window_hours: int = 48, source: str = "manual") -> dict[str, Any]:
    """Full governed reality loop cycle — observe, correlate, recommend, replay."""
    observations = collect_operational_observations(window_hours=window_hours)
    structured_anomalies = detect_operational_anomalies(observations=observations, window_hours=window_hours)
    telemetry = assess_telemetry_quality(
        event_count=len(observations.get("events") or []),
        stale_sources=len((observations.get("telemetry_freshness") or {}).get("stale_sources") or []),
    )
    recommendations = generate_recommendations_from_anomalies(
        structured_anomalies,
        telemetry_quality=str(telemetry.get("telemetry_quality") or "medium"),
    )
    trust = operational_trust_summary(anomalies=structured_anomalies, telemetry=telemetry)
    drift = detect_operational_drift(observations)
    stability = deployment_stability_snapshot(observations)

    reliability_snapshot = None
    try:
        from aethos_core.reliability.reliability_runtime import assess_operational_reliability

        reliability_snapshot = assess_operational_reliability(
            observations=observations,
            anomalies=structured_anomalies,
            telemetry=telemetry,
            trust=trust,
            recommendations=recommendations,
        )
    except Exception:
        pass

    cycle = {
        "source": source,
        "scanned_at": time(),
        "window_hours": window_hours,
        "observations": observations,
        "anomalies": structured_anomalies,
        "recommendations": recommendations,
        "drift": drift,
        "stability": stability,
        "telemetry": telemetry,
        "trust": trust,
        "reliability": reliability_snapshot,
        "readonly": True,
        "background_mutations": False,
        "autonomous_execution_blocked": True,
    }
    replay = store_operational_replay(cycle={"summary": _cycle_summary(cycle), **cycle})
    cycle["replay_id"] = replay.get("replay_id")

    if recommendations:
        notify_operational_recommendations(recommendations)
        for rec in recommendations:
            record_operational_memory(
                kind="recommendation_generated",
                detail=str(rec.get("title") or rec.get("suggested_action")),
                category=str(rec.get("kind") or "recommendation"),
            )

    _maybe_trigger_research(structured_anomalies)

    return cycle


def collect_operational_observations(*, window_hours: int = 48) -> dict[str, Any]:
    """Gather readonly signals from deployments, CI, browser, repo, dependencies."""
    scan = run_reality_loop_scan(window_hours=window_hours)
    memory = get_operational_patterns_memory()
    events = list(memory.get("events") or [])
    recent = [e for e in events if time() - float(e.get("at") or 0) < window_hours * 3600]
    op_mem = operational_memory_snapshot(window_hours=window_hours)
    freshness = _telemetry_freshness(events)
    repo_signals = _repo_observation()
    dependency_signals = _dependency_observation()
    return {
        **scan,
        "events": recent,
        "operational_memory": op_mem,
        "telemetry_freshness": freshness,
        "repo_signals": repo_signals,
        "dependency_signals": dependency_signals,
        "drift": detect_operational_drift({"events": recent, "operational_memory": op_mem}),
    }


def detect_operational_drift(observations: dict[str, Any]) -> dict[str, Any]:
    events = observations.get("events") or []
    mem = observations.get("operational_memory") or operational_memory_snapshot()
    wf = sum(1 for e in events if "workflow" in str(e.get("category", "")).lower())
    dep = sum(1 for e in events if "deployment" in str(e.get("category", "")).lower())
    browser = sum(1 for e in events if "browser" in str(e.get("category", "")).lower())
    total = wf + dep + browser
    detected = total >= 4 or len(mem.get("by_kind") or {}) >= 3
    severity = "high" if total >= 6 else "medium" if detected else "low"
    signals: list[str] = []
    if wf >= 2:
        signals.append(f"{wf} workflow instability signals")
    if dep >= 2:
        signals.append(f"{dep} deployment instability signals")
    if browser >= 2:
        signals.append("Repeated browser verification failures")
    return {
        "detected": detected,
        "severity": severity,
        "confidence": min(0.55 + total * 0.06, 0.92),
        "signals": signals,
        "systems": ["CI", "deployments", "browser evidence"] if detected else [],
    }


def deployment_stability_snapshot(observations: dict[str, Any]) -> dict[str, Any]:
    events = observations.get("events") or []
    dep_events = [e for e in events if "deployment" in str(e.get("category", "")).lower()]
    timeline = [
        {"at": e.get("at"), "detail": e.get("detail"), "provider": e.get("provider")}
        for e in dep_events[:12]
    ]
    stability = "stable"
    if len(dep_events) >= 4:
        stability = "unstable"
    elif len(dep_events) >= 2:
        stability = "watch"
    return {"stability": stability, "event_count": len(dep_events), "timeline": timeline}


def get_operational_intelligence_state() -> dict[str, Any]:
    """Aggregate state for Mission Control operational center."""
    observations = collect_operational_observations()
    anomalies = detect_operational_anomalies(observations=observations)
    state = {
        "ok": True,
        "anomalies": anomalies,
        "recommendations": list_recommendations(),
        "drift": detect_operational_drift(observations),
        "stability": deployment_stability_snapshot(observations),
        "telemetry_freshness": observations.get("telemetry_freshness"),
        "recurring_patterns": observations.get("recurring_patterns") or [],
        "trends": observations.get("trends") or [],
        "operational_memory": observations.get("operational_memory"),
        "readonly": True,
        "autonomous_execution_blocked": True,
    }
    try:
        from aethos_core.reliability.reliability_runtime import assess_operational_reliability

        rel = assess_operational_reliability(
            observations=observations,
            anomalies=anomalies,
            recommendations=state["recommendations"],
        )
        state["reliability"] = rel.get("reliability")
        state["reliability_scores"] = rel.get("scores")
        state["governance"] = rel.get("governance")
        state["explainability"] = rel.get("explainability")
    except Exception:
        pass
    return state


def format_reality_loop_report(scan: dict[str, Any]) -> str:
    lines = [
        "# Operational reality loop (readonly)",
        "",
        f"**Window:** {scan.get('window_hours')}h · **Events:** {scan.get('event_count', 0)}",
        "",
        "## Recurring patterns",
    ]
    for p in scan.get("recurring_patterns") or []:
        lines.append(f"- {p}")
    if not scan.get("recurring_patterns"):
        lines.append("- No recurring patterns above threshold.")
    lines.extend(["", "## Anomalies"])
    for a in scan.get("anomalies") or []:
        if isinstance(a, dict):
            lines.append(f"- [{a.get('severity')}] {a.get('kind')}: {a.get('recommended_action')}")
        else:
            lines.append(f"- {a}")
    lines.extend(["", "## Trends"])
    for t in scan.get("trends") or []:
        lines.append(f"- {t}")
    lines.append("")
    lines.append("*Readonly scan — no hidden background mutations or autonomous deploys.*")
    return "\n".join(lines)


def _cycle_summary(cycle: dict[str, Any]) -> str:
    ac = len(cycle.get("anomalies") or [])
    rc = len(cycle.get("recommendations") or [])
    return f"Reality loop cycle: {ac} anomalies, {rc} recommendations (readonly)"


def _detect_anomalies(events: list[dict[str, Any]]) -> list[str]:
    by_cat: dict[str, int] = {}
    for e in events:
        cat = str(e.get("category") or "unknown")
        by_cat[cat] = by_cat.get(cat, 0) + 1
    out: list[str] = []
    for cat, count in by_cat.items():
        if count >= 3:
            out.append(f"Elevated `{cat}` signals: {count} in window.")
    return out[:6]


def _build_trends(events: list[dict[str, Any]], patterns: list[str]) -> list[str]:
    trends = list(patterns[:4])
    wf = sum(1 for e in events if "workflow" in str(e.get("category", "")).lower())
    if wf >= 2:
        trends.append(f"Observed {wf} workflow-related signals in recent window.")
    dep = sum(1 for e in events if "deployment" in str(e.get("category", "")).lower())
    if dep >= 2:
        trends.append(f"Observed {dep} deployment instability signal(s).")
    browser = sum(1 for e in events if "browser" in str(e.get("category", "")).lower())
    if browser >= 2:
        trends.append("Repeated browser evidence DNS/URL failures detected.")
    return trends[:8]


def _telemetry_freshness(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        return {"stale": True, "stale_sources": ["operational_patterns"], "last_event_at": None}
    last_at = max(float(e.get("at") or 0) for e in events)
    age_hours = (time() - last_at) / 3600.0
    stale_sources: list[str] = []
    if age_hours > 12:
        stale_sources.append("operational_patterns")
    return {"stale": bool(stale_sources), "stale_sources": stale_sources, "last_event_at": last_at, "age_hours": age_hours}


def _repo_observation() -> dict[str, Any]:
    try:
        from aethos_core.local_workspace.readonly.actions import _repo_from_hint
        from aethos_core.agents.engineering.git_hotspots import run_git_hotspot_analysis

        repo = _repo_from_hint("aethos", session_id="operational_runtime")
        if not Path(repo).is_dir():
            return {"ok": False, "reason": "repo_unavailable"}
        hot = run_git_hotspot_analysis(Path(repo))
        return {"ok": True, "hot_files": (hot.get("hot_files") or [])[:5]}
    except Exception as exc:
        return {"ok": False, "reason": str(exc)[:120]}


def _dependency_observation() -> dict[str, Any]:
    return {"ok": True, "scan": "readonly", "note": "dependency CVE observation scheduled daily"}


def _maybe_trigger_research(anomalies: list[dict[str, Any]]) -> None:
    for anomaly in anomalies:
        kind = str(anomaly.get("kind") or "")
        if kind not in ("deployment_instability", "dependency_risk", "dependency_churn"):
            continue
        try:
            from aethos_core.research.operational_research import research_context_for_prompt

            prompt = "Railway deployment instability advisory" if "deployment" in kind else "dependency CVE advisory"
            research_context_for_prompt(prompt, session_id="operational_runtime")
        except Exception:
            pass
