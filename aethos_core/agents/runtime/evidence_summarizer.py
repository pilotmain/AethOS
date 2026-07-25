# SPDX-License-Identifier: Apache-2.0
"""Human-readable evidence summaries from artifact records."""

from __future__ import annotations

from typing import Any


def summarize_evidence_record(item: dict[str, Any]) -> dict[str, Any]:
    """Return {artifact_id, summary, agent_id, source} with readable text."""
    eid = str(item.get("artifact_id") or "")
    source = str(item.get("source") or "unknown")
    rec = item.get("record") or {}
    atype = str(rec.get("artifact_type") or rec.get("type") or source)
    agent_id = rec.get("agent_id")
    summary = str(rec.get("summary") or "").strip()
    payload = rec.get("payload") or {}

    readable = summary or _summarize_payload(atype, payload, source)
    if not readable:
        readable = f"{atype.replace('_', ' ')} artifact"

    return {
        "artifact_id": eid,
        "source": source,
        "artifact_type": atype,
        "agent_id": agent_id,
        "summary": readable,
        "display": f"`{eid}` — {readable}",
    }


def summarize_evidence_bundle(bundle: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [summarize_evidence_record(item) for item in bundle]


def _summarize_payload(atype: str, payload: dict[str, Any], source: str) -> str:
    if atype == "dependency_audit" or "dependency" in atype:
        sev = payload.get("severity") or (payload.get("scan") or {}).get("severity")
        vulns = payload.get("vulnerabilities") or []
        risks = payload.get("risk_summary") or []
        parts = [f"Dependency audit: severity {sev or 'unknown'}"]
        if vulns:
            parts.append(f"{len(vulns)} vulnerabilities flagged")
        if risks and isinstance(risks, list):
            parts.append(str(risks[0])[:120])
        return "; ".join(parts)

    if atype == "architecture_analysis" or "architecture" in atype:
        layers = payload.get("layers") or payload.get("architecture", {}).get("layers") if isinstance(payload.get("architecture"), dict) else payload.get("layers")
        count = len(layers) if isinstance(layers, list) else 0
        bottlenecks = payload.get("bottlenecks") or []
        return f"Architecture analysis: {count} layers; {len(bottlenecks)} bottleneck(s)"

    if atype == "git_status_snapshot" or "git" in atype:
        git = payload.get("git") or {}
        hot = payload.get("hot_files") or []
        return f"Git hotspots: branch {git.get('branch') or 'unknown'}; {len(hot)} hot file(s)"

    if atype == "engineering_pr_proposal":
        targets = payload.get("modernization_targets") or payload.get("proposed_changes") or []
        return f"PR proposal: {len(targets)} modernization target(s); readonly only"

    if atype == "agent_provider_diagnostics":
        prov = str(payload.get("provider") or "provider")
        if payload.get("credential_required"):
            return f"{prov.title()} diagnostics: credential unavailable — no provider evidence fetched"
        dep_id = payload.get("deployment_id") or ((payload.get("correlation") or {}).get("failed_deployment") or {}).get("id")
        state = payload.get("deployment_state") or ((payload.get("correlation") or {}).get("failed_deployment") or {}).get("state")
        if dep_id:
            return f"{prov.title()} diagnostics: deployment `{dep_id}` state {state or 'unknown'}"
        return f"{prov.title()} diagnostics: no failed deployment ID in current evidence"

    if atype == "agent_browser_evidence":
        if payload.get("metadata_only"):
            return "Browser evidence: metadata-only capture (no public URL resolved)"
        return f"Browser evidence: {payload.get('summary') or 'capture completed'}"

    if atype == "agent_root_cause_analysis":
        conf = payload.get("confidence") or "low"
        return f"Analyst correlation: confidence {conf}; structured findings attached"

    if atype == "agent_operational_report":
        analysis = payload.get("analysis") or {}
        return f"Operational report: {analysis.get('report_mode', 'analysis')} mode"

    if source == "browser":
        return f"Browser artifact: {payload.get('artifact_type') or atype}"

    sub = payload.get("substrate_payload")
    if isinstance(sub, dict) and sub.get("summary"):
        return str(sub["summary"])[:200]

    return ""
