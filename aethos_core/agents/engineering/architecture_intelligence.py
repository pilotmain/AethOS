# SPDX-License-Identifier: Apache-2.0
"""Architecture intelligence — operational bottlenecks, risk zones, health score."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.agents.engineering.architecture_reasoning import run_architecture_reasoning


def run_architecture_intelligence(repo: Path) -> dict[str, Any]:
    """Operational architecture intelligence — extends static graph with health scoring."""
    analysis = run_architecture_reasoning(repo)
    bottlenecks = _operational_bottlenecks(analysis)
    risk_zones = _risk_zones(analysis)
    growth_risks = _growth_risks(analysis)
    health = _health_score(bottlenecks, risk_zones, growth_risks)
    analysis["operational_bottlenecks"] = bottlenecks
    analysis["risk_zones"] = risk_zones
    analysis["growth_risks"] = growth_risks
    analysis["architecture_health"] = health
    analysis["top_risks"] = _top_risks(bottlenecks, risk_zones, growth_risks)
    return analysis


def format_architecture_intelligence_report(analysis: dict[str, Any]) -> str:
    health = analysis.get("architecture_health") or {}
    lines = [
        "# Architecture intelligence (operational)",
        "",
        f"**Architecture health:** {health.get('architecture_health', '—')}/100",
        f"**Risk level:** {health.get('risk_level', 'unknown')}",
        "",
        "## Operational bottlenecks",
    ]
    for b in analysis.get("operational_bottlenecks") or analysis.get("bottlenecks") or []:
        lines.append(f"- **{b.get('area')}** — {b.get('detail')}")
    lines.extend(["", "## Risk zones"])
    for r in analysis.get("risk_zones") or []:
        lines.append(f"- **{r.get('zone')}** — {r.get('detail')}")
    lines.extend(["", "## Growth risks"])
    for g in analysis.get("growth_risks") or []:
        lines.append(f"- {g}")
    lines.extend(["", "## Top risks"])
    for t in analysis.get("top_risks") or []:
        lines.append(f"- {t}")
    lines.extend(["", "## Recommendations"])
    for s in analysis.get("scalability_observations") or []:
        lines.append(f"- {s}")
    return "\n".join(lines)


def _operational_bottlenecks(analysis: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    layers = {l.get("layer"): l for l in analysis.get("layers") or []}
    if layers.get("Job runtime", {}).get("present"):
        rows.append({"area": "Serialized executors", "detail": "Job runtime queues long provider/browser work under burst load."})
    if layers.get("Orchestration brain", {}).get("present"):
        rows.append({"area": "Orchestration hotspot", "detail": "Central intent routing — monitor deterministic lane vs LLM fallback ratio."})
    if layers.get("Browser evidence", {}).get("present"):
        rows.append({"area": "Browser queue pressure", "detail": "Playwright capture latency bounded by approval gates and thread pool."})
    if layers.get("Provider runtime layer", {}).get("present"):
        rows.append({"area": "Provider fanout", "detail": "Multi-provider auth and telemetry paths increase readonly latency."})
    if not rows:
        rows.extend(analysis.get("bottlenecks") or [])
    return rows


def _risk_zones(analysis: dict[str, Any]) -> list[dict[str, str]]:
    semantic = {m.get("label") for m in analysis.get("semantic_modules") or []}
    zones: list[dict[str, str]] = []
    if "Governed mutation execution lifecycle" not in semantic:
        zones.append({"zone": "Mutation lifecycle", "detail": "Mutation preflight bypass risk if orchestration gates are skipped."})
    else:
        zones.append({"zone": "Mutation lifecycle", "detail": "Preflight → approval → execution path present — maintain audit trail."})
    if "Provider runtime layer" in semantic:
        zones.append({"zone": "Credential centralization", "detail": "Provider auth centralized — monitor token expiry and scope isolation."})
    zones.append({"zone": "Orchestration SPOF", "detail": "Multi-agent planner is single coordination authority — bounded by runtime budget."})
    return zones


def _growth_risks(analysis: dict[str, Any]) -> list[str]:
    flows = analysis.get("operational_flows") or []
    risks = [
        "Agent explosion — cap at 5 agents per coordination plan.",
        "Artifact storage growth — index capped at 500 entries; archive old coordination artifacts.",
        "Timeline replay cost — hydrate only referenced evidence IDs during merge.",
    ]
    if any("browser" in f.lower() for f in flows):
        risks.append("Memory hydration latency — browser artifacts are largest payload class.")
    return risks


def _health_score(
    bottlenecks: list[dict[str, str]],
    risk_zones: list[dict[str, str]],
    growth_risks: list[str],
) -> dict[str, Any]:
    score = 100
    score -= min(len(bottlenecks) * 4, 24)
    score -= min(len(risk_zones) * 3, 15)
    score -= min(len(growth_risks) * 2, 12)
    score = max(40, min(100, score))
    if score >= 80:
        level = "low"
    elif score >= 65:
        level = "medium"
    else:
        level = "high"
    return {"architecture_health": score, "risk_level": level}


def _top_risks(
    bottlenecks: list[dict[str, str]],
    risk_zones: list[dict[str, str]],
    growth_risks: list[str],
) -> list[str]:
    out: list[str] = []
    for b in bottlenecks[:2]:
        out.append(f"{b.get('area')}: {b.get('detail')}")
    for r in risk_zones[:2]:
        out.append(f"{r.get('zone')}: {r.get('detail')}")
    out.extend(growth_risks[:2])
    return out[:5]
