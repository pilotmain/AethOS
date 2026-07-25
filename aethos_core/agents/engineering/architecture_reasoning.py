# SPDX-License-Identifier: Apache-2.0
"""Architecture reasoning — graph, bottlenecks, governance observations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.local_workspace.analysis.architecture import analyze_architecture, format_architecture_report


def run_architecture_reasoning(repo: Path) -> dict[str, Any]:
    analysis = analyze_architecture(repo)
    bottlenecks = _detect_bottlenecks(analysis)
    governance = _mutation_governance_observations(analysis)
    scalability = _scalability_observations(analysis)
    analysis["bottlenecks"] = bottlenecks
    analysis["governance_observations"] = governance
    analysis["scalability_observations"] = scalability
    analysis["risk_signals"] = _architecture_signals(bottlenecks, governance)
    return analysis


def format_architecture_reasoning_report(analysis: dict[str, Any]) -> str:
    base = format_architecture_report(analysis)
    extra: list[str] = ["", "## Orchestration bottlenecks"]
    for b in analysis.get("bottlenecks") or []:
        extra.append(f"- **{b.get('area')}** — {b.get('detail')}")
    extra.extend(["", "## Mutation governance observations"])
    for g in analysis.get("governance_observations") or []:
        extra.append(f"- {g}")
    extra.extend(["", "## Scalability observations"])
    for s in analysis.get("scalability_observations") or []:
        extra.append(f"- {s}")
    return base + "\n".join(extra)


def _detect_bottlenecks(analysis: dict[str, Any]) -> list[dict[str, str]]:
    layers = {l.get("layer"): l for l in analysis.get("layers") or []}
    rows: list[dict[str, str]] = []
    if layers.get("Orchestration brain", {}).get("present"):
        rows.append(
            {
                "area": "Orchestration brain",
                "detail": "Central intent routing — monitor deterministic lane coverage vs LLM fallback.",
            }
        )
    if layers.get("Job runtime", {}).get("present"):
        rows.append(
            {
                "area": "Job runtime",
                "detail": "Serialized job executor — long provider/browser jobs may queue under burst load.",
            }
        )
    if layers.get("Browser evidence", {}).get("present"):
        rows.append(
            {
                "area": "Browser evidence",
                "detail": "Playwright thread pool — capture latency bounded by operator approval + runtime health.",
            }
        )
    if not layers.get("Credential vault", {}).get("present"):
        rows.append(
            {
                "area": "Credential vault",
                "detail": "Missing vault layer increases provider auth fragility.",
            }
        )
    return rows


def _mutation_governance_observations(analysis: dict[str, Any]) -> list[str]:
    semantic = analysis.get("semantic_modules") or []
    labels = {m.get("label") for m in semantic}
    obs: list[str] = []
    if "Governed mutation execution lifecycle" in labels:
        obs.append("Mutation preflight → approval → execution path is present in codebase.")
    else:
        obs.append("Mutation governance modules not detected — verify approval gates before writes.")
    if "Provider runtime layer" in labels:
        obs.append("Provider runtime centralizes auth — good for credential isolation.")
    obs.append("Agents and chat lanes must never bypass orchestration authority for mutations.")
    return obs


def _scalability_observations(analysis: dict[str, Any]) -> list[str]:
    flows = analysis.get("operational_flows") or []
    obs = [
        "Readonly analysis scales with workspace size — cache scan artifacts to avoid duplicate work.",
        "Multi-agent coordination is bounded (max 5 agents, 120s budget).",
    ]
    if any("browser capture" in f.lower() for f in flows):
        obs.append("Browser capture is the highest-latency readonly path — prefer metadata-only when URL unknown.")
    return obs


def _architecture_signals(bottlenecks: list[dict], governance: list[str]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    if len(bottlenecks) >= 3:
        signals.append({"kind": "hotspot", "weight": 1, "detail": "multiple orchestration bottlenecks"})
    if any("not detected" in g.lower() for g in governance):
        signals.append({"kind": "missing_verification", "weight": 1, "detail": "governance gap detected"})
    return signals
