# SPDX-License-Identifier: Apache-2.0
"""Cross-evidence correlation — temporal, structural, operational fusion."""

from __future__ import annotations

from typing import Any


def correlate_operational_evidence(
    *,
    provider: dict[str, Any] | None,
    engineering: dict[str, Any] | None,
    browser: dict[str, Any] | None,
    deployment_intel: dict[str, Any] | None,
    report_mode: str = "deployment_failure",
) -> dict[str, Any]:
    """Fuse parallel evidence into correlated operational intelligence."""
    temporal: list[dict[str, str]] = []
    structural: list[dict[str, str]] = []
    operational: list[dict[str, str]] = []
    graph_edges: list[dict[str, str]] = []

    prov = provider or {}
    eng = engineering or {}
    br = browser or {}
    intel = deployment_intel or prov

    failed = (
        (prov.get("correlation") or {}).get("failed_deployment")
        or (intel.get("correlation") or {}).get("failed_deployment")
        or {}
    )
    if not failed.get("id") and _is_failed_state((intel.get("latest_deployment") or {}).get("state")):
        failed = intel.get("latest_deployment") or {}
    if _is_failed_state(failed.get("state")) and failed.get("commit"):
        commits = eng.get("recent_commits") or []
        if commits:
            temporal.append(
                {
                    "type": "temporal",
                    "detail": f"Git commit `{failed.get('commit')}` aligns with failed deployment `{failed.get('id', '')[:12]}`.",
                }
            )
            graph_edges.append({"from": "git", "to": "deployment", "label": "commit correlation"})

    hot_files = eng.get("hot_files") or []
    if hot_files and failed.get("id"):
        path = hot_files[0].get("path") if isinstance(hot_files[0], dict) else str(hot_files[0])
        structural.append(
            {
                "type": "structural",
                "detail": f"Modified hotspot `{path}` may intersect deployment pipeline — related signal only.",
            }
        )
        graph_edges.append({"from": "engineering", "to": "deployment", "label": "hotspot overlap"})

    deps = eng.get("modernization_targets") or (eng.get("dependency_findings") or {}).get("vulnerabilities")
    if deps and report_mode == "pr_proposal":
        structural.append(
            {
                "type": "structural",
                "detail": f"Dependency audit flagged {len(deps) if isinstance(deps, list) else 1} modernization target(s) for PR scope.",
            }
        )

    ci = eng.get("failure_clusters") or (eng.get("diagnostics") or {}).get("workflows")
    if ci and failed.get("id"):
        operational.append(
            {
                "type": "operational",
                "detail": "CI/workflow evidence should be correlated with deployment failure window.",
            }
        )
        graph_edges.append({"from": "ci", "to": "deployment", "label": "pipeline correlation"})

    if br.get("target_unresolved"):
        prov_healthy = not _is_failed_state((intel.get("latest_deployment") or {}).get("state"))
        if prov_healthy:
            operational.append(
                {
                    "type": "operational",
                    "detail": "Browser capture skipped — latest provider deployment appears healthy; no public URL mapped.",
                }
            )
        else:
            operational.append(
                {
                    "type": "operational",
                    "detail": "Browser capture skipped — provider deployment unhealthy but public URL unresolved.",
                }
            )
        graph_edges.append({"from": "browser", "to": "provider", "label": "URL resolution gap"})
    elif br.get("metadata_only"):
        operational.append(
            {
                "type": "operational",
                "detail": "Browser metadata captured — correlates with provider deployment state when URL resolves.",
            }
        )

    if intel.get("restart_count", 0) >= 2:
        operational.append(
            {
                "type": "operational",
                "detail": f"Observed {intel['restart_count']} failed/restart deployment signal(s) in recent window.",
            }
        )

    confirmed: list[str] = []
    hypotheses: list[str] = []
    signals: list[str] = []
    gaps: list[str] = []

    if intel.get("failed_deployment_found") and failed.get("id"):
        confirmed.append(f"Provider telemetry: deployment `{failed.get('id')}` state `{failed.get('state')}`.")
    elif intel.get("credential_state") == "unavailable":
        confirmed.append("Provider credential unavailable — deployment telemetry not fetched.")
        gaps.append("Connect provider credentials for deployment timeline evidence.")
    elif report_mode == "deployment_failure":
        confirmed.append("No confirmed failed deployment in latest provider telemetry.")
        gaps.append("Need deployment ID + logs or explicit failed service query.")

    for row in temporal + structural + operational:
        signals.append(row["detail"])

    if temporal and failed.get("error_message"):
        hypotheses.append(f"Failure may relate to changes near commit `{failed.get('commit') or 'unknown'}`.")

    return {
        "temporal": temporal,
        "structural": structural,
        "operational": operational,
        "graph_edges": graph_edges,
        "conclusions": {
            "confirmed": confirmed,
            "hypotheses": hypotheses,
            "signals": signals,
            "gaps": gaps,
        },
        "correlation_count": len(temporal) + len(structural) + len(operational),
    }


def _is_failed_state(state: Any) -> bool:
    return str(state or "").lower() in ("failed", "crashed", "error")
