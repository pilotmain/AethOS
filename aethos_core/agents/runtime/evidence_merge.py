# SPDX-License-Identifier: Apache-2.0
"""Evidence merge — canonical aggregation with substrate hydration."""

from __future__ import annotations

from typing import Any

from aethos_core.agents.runtime.confidence_engine import score_merged_confidence
from aethos_core.agents.runtime.evidence_correlation_engine import correlate_operational_evidence
from aethos_core.agents.runtime.evidence_summarizer import summarize_evidence_bundle
from aethos_core.agents.runtime.report_mode import infer_report_mode
from aethos_core.agents.runtime.report_templates import render_merged_report
from aethos_core.agents.runtime.severity_authority import resolve_final_severity


def resolve_evidence_record(artifact_id: str) -> dict[str, Any] | None:
    """Load evidence from agent, local workspace, or browser stores."""
    if not artifact_id:
        return None
    from aethos_core.agents.runtime.artifacts import get_agent_artifact

    rec = get_agent_artifact(artifact_id)
    if rec:
        return {"source": "agent", "artifact_id": artifact_id, "record": rec}
    if artifact_id.startswith("lart-"):
        from aethos_core.local_workspace.artifacts.store import get_workspace_artifact

        ws = get_workspace_artifact(artifact_id)
        if ws:
            return {"source": "local_workspace", "artifact_id": artifact_id, "record": ws}
    from aethos_core.browser.runtime.browser_artifacts import get_artifact

    br = get_artifact(artifact_id)
    if br:
        return {"source": "browser", "artifact_id": artifact_id, "record": br}
    return None


def hydrate_evidence_bundle(evidence_ids: list[str]) -> list[dict[str, Any]]:
    """Resolve artifact IDs to records — duplicate suppression by id."""
    seen: set[str] = set()
    bundle: list[dict[str, Any]] = []
    for eid in evidence_ids:
        if not eid or eid in seen:
            continue
        seen.add(eid)
        row = resolve_evidence_record(eid)
        if row:
            bundle.append(row)
    return bundle


def merge_agent_evidence(
    *,
    plan_id: str,
    goal: str,
    agent_results: list[dict[str, Any]],
    report_mode: str | None = None,
) -> dict[str, Any]:
    """Deduplicate timelines, hydrate evidence, score confidence and canonical severity."""
    mode = report_mode or infer_report_mode(goal)
    timeline: list[dict[str, Any]] = []
    evidence_ids: list[str] = []
    failures: list[dict[str, Any]] = []
    substrate_invoked: list[str] = []
    agent_contracts: list[dict[str, Any]] = []

    for row in agent_results:
        agent_id = str(row.get("agent_id") or "unknown")
        status = row.get("status") or "unknown"
        if row.get("artifact_id"):
            evidence_ids.append(str(row["artifact_id"]))
        evidence_ids.extend([str(e) for e in row.get("evidence_ids") or []])
        substrate = row.get("substrate_invoked") or []
        if isinstance(substrate, list):
            substrate_invoked.extend(substrate)
        elif substrate:
            substrate_invoked.append(str(substrate))
        timeline.append(
            {
                "agent_id": agent_id,
                "task": row.get("task"),
                "status": status,
                "duration_ms": row.get("duration_ms"),
                "evidence_count": len(row.get("evidence_ids") or []) + (1 if row.get("artifact_id") else 0),
                "substrate_invoked": row.get("substrate_invoked") or [],
                "at": row.get("finished_at"),
            }
        )
        if row.get("contract"):
            agent_contracts.append(row["contract"])
        if status == "failed":
            failures.append({"agent_id": agent_id, "error": row.get("error") or "failed"})

    overall = "completed"
    if failures and len(failures) < len(agent_results):
        overall = "partial"
    elif failures and len(failures) == len(agent_results):
        overall = "failed"

    unique_evidence = _dedupe_ids(evidence_ids)
    bundle = hydrate_evidence_bundle(unique_evidence)
    evidence_summaries = summarize_evidence_bundle(bundle)
    conflicts = _detect_conflicts(agent_results)
    deployment_intel = _deployment_intel(agent_results)
    correlation = _correlation_payload(agent_results, mode, deployment_intel)
    confidence = score_merged_confidence(
        bundle=bundle,
        agent_results=agent_results,
        correlation=correlation,
        deployment_intel=deployment_intel,
        conflicts=conflicts,
    )

    provider_payload = _provider_payload(agent_results)
    severity_authority = resolve_final_severity(
        agent_results=agent_results,
        report_mode=mode,
        confidence=confidence,
        provider_payload=provider_payload,
    )

    conclusions = _extract_conclusions(agent_results, mode, correlation)
    architecture_analysis = _architecture_payload(agent_results)
    pr_proposal = _pr_proposal_payload(agent_results)
    next_steps = _collect_next_steps(agent_results, mode, conclusions)
    recurring_patterns = _recurring_patterns()

    return {
        "plan_id": plan_id,
        "goal": goal,
        "report_mode": mode,
        "status": overall,
        "timeline": timeline,
        "evidence_ids": unique_evidence,
        "evidence_bundle_count": len(bundle),
        "evidence_summaries": evidence_summaries,
        "evidence_attributions": evidence_summaries,
        "conflicts": conflicts,
        "failures": failures,
        "agent_count": len(agent_results),
        "agent_contracts": agent_contracts,
        "substrate_invoked": sorted(set(substrate_invoked)),
        "confidence": confidence,
        "correlation": correlation,
        "deployment_intelligence": deployment_intel,
        "recurring_patterns": recurring_patterns,
        "severity": severity_authority.get("severity"),
        "severity_authority": severity_authority,
        "conclusions": conclusions,
        "architecture_analysis": architecture_analysis,
        "pr_proposal": pr_proposal,
        "recommendations": (architecture_analysis or {}).get("scalability_observations") or [],
        "next_steps": next_steps,
        "read_only": True,
        "mutation_execution_enabled": False,
    }


def format_merged_report(merged: dict[str, Any]) -> str:
    return render_merged_report(merged)


def _dedupe_ids(ids: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for eid in ids:
        if eid and eid not in seen:
            seen.add(eid)
            out.append(eid)
    return out


def _provider_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    for r in results:
        if r.get("agent_id") == "provider_ops":
            return dict(r.get("substrate_payload") or {})
    return {}


def _architecture_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    for r in results:
        if r.get("agent_id") == "code_intelligence":
            payload = r.get("substrate_payload") or {}
            if payload.get("bottlenecks") or payload.get("layers"):
                return payload
    return {}


def _pr_proposal_payload(results: list[dict[str, Any]]) -> dict[str, Any]:
    for r in results:
        payload = r.get("substrate_payload") or {}
        if r.get("agent_id") == "code_intelligence" and payload.get("modernization_targets") is not None:
            return payload
        if payload.get("title") and payload.get("phased_migration"):
            return payload
    return {}


def _extract_conclusions(results: list[dict[str, Any]], mode: str, correlation: dict[str, Any] | None = None) -> dict[str, Any]:
    for r in results:
        if r.get("agent_id") == "operations_analyst":
            analysis = r.get("analysis") or r.get("substrate_payload") or {}
            conc = analysis.get("conclusions")
            if conc:
                return conc
    if correlation and correlation.get("conclusions"):
        return correlation["conclusions"]
    if mode == "architecture_risk":
        arch = _architecture_payload(results)
        return {
            "confirmed": [f"Architecture scan completed for `{arch.get('repo') or 'workspace'}`."],
            "hypotheses": [],
            "signals": [b.get("detail", "") for b in (arch.get("bottlenecks") or [])],
            "gaps": [],
        }
    return {"confirmed": [], "hypotheses": [], "signals": [], "gaps": ["Analyst correlation not available."]}


def _collect_next_steps(results: list[dict[str, Any]], mode: str, conclusions: dict[str, Any]) -> list[str]:
    steps: list[str] = []
    for r in results:
        contract = r.get("contract") or {}
        steps.extend(contract.get("next_steps") or [])
        analysis = r.get("analysis") or {}
        steps.extend(analysis.get("next_steps") or [])
    gaps = conclusions.get("gaps") or []
    if mode == "deployment_failure" and gaps and not steps:
        steps.append("Address evidence gaps above before treating any hypothesis as confirmed.")
    return list(dict.fromkeys(steps))[:8]


def _deployment_intel(results: list[dict[str, Any]]) -> dict[str, Any]:
    for r in results:
        if r.get("agent_id") == "provider_ops":
            return dict(r.get("deployment_intelligence") or r.get("substrate_payload") or {})
    return {}


def _correlation_payload(
    results: list[dict[str, Any]],
    mode: str,
    deployment_intel: dict[str, Any],
) -> dict[str, Any]:
    for r in results:
        analysis = r.get("analysis") or r.get("substrate_payload") or {}
        if r.get("agent_id") == "operations_analyst" and analysis.get("correlation"):
            return analysis["correlation"]
    provider = next((r.get("substrate_payload") for r in results if r.get("agent_id") == "provider_ops"), {})
    engineering = next((r.get("substrate_payload") for r in results if r.get("agent_id") == "code_intelligence"), {})
    browser = next((r.get("substrate_payload") for r in results if r.get("agent_id") == "web_evidence"), {})
    return correlate_operational_evidence(
        provider=provider,
        engineering=engineering,
        browser=browser,
        deployment_intel=deployment_intel,
        report_mode=mode,
    )


def _recurring_patterns() -> list[str]:
    from aethos_core.agents.memory.operational_patterns import get_recurring_patterns

    return get_recurring_patterns()


def _detect_conflicts(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    conflicts: list[dict[str, str]] = []
    prov = next((r for r in results if r.get("agent_id") == "provider_ops"), {})
    analyst = next((r for r in results if r.get("agent_id") == "operations_analyst"), {})
    prov_sev = str((prov.get("analysis") or {}).get("severity") or "").upper()
    final_note = "Severity resolved by severity authority — analyst recommendation is advisory only."
    if prov_sev and prov_sev in ("HIGH", "CRITICAL"):
        conflicts.append({"detail": final_note})
    if prov.get("credential_required") and prov.get("status") == "completed":
        conflicts.append({"detail": "Provider credentials missing — deployment failure cannot be confirmed."})
    if analyst.get("analysis") and prov.get("substrate_payload", {}).get("credential_required"):
        pass
    return conflicts
