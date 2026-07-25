# SPDX-License-Identifier: Apache-2.0
"""Runtime failure analysis — grounded conclusions without overreach."""

from __future__ import annotations

from typing import Any


def analyze_runtime_failure(
    *,
    provider_evidence: dict[str, Any] | None,
    engineering_evidence: dict[str, Any] | None,
    browser_evidence: dict[str, Any] | None,
    goal: str,
    report_mode: str = "deployment_failure",
) -> dict[str, Any]:
    """Structured conclusions: confirmed, hypothesis, signals, gaps — never exaggerate."""
    if report_mode == "architecture_risk":
        return _analyze_architecture_risk(engineering_evidence, goal)
    if report_mode == "pr_proposal":
        return _analyze_pr_proposal(engineering_evidence, goal)

    confirmed: list[str] = []
    hypotheses: list[str] = []
    signals: list[str] = []
    gaps: list[str] = []
    confidence_reasons: list[str] = []
    next_steps: list[str] = []

    prov = provider_evidence or {}
    corr = prov.get("correlation") or {}
    failed = corr.get("failed_deployment") or {}
    failed_state = str(failed.get("state") or prov.get("deployment_state") or "").lower()
    logs = str(prov.get("log_excerpt") or prov.get("log_text") or "")

    if prov.get("credential_required"):
        confirmed.append("Railway/provider credential unavailable — provider evidence could not be fetched.")
        gaps.append("Connect provider credentials in Mission Control → Advanced settings → Credentials.")
        next_steps.append('Reconnect provider token, then rerun: "analyze why the latest Railway deployment failed".')
    elif failed.get("id") and failed_state in ("failed", "crashed", "error"):
        confirmed.append(f"Failed deployment `{failed.get('id')}` reported with state `{failed_state}`.")
        confidence_reasons.append("provider deployment API")
        if failed.get("error_message"):
            confirmed.append(f"Provider error message: {str(failed['error_message'])[:240]}")
    elif prov.get("ok"):
        confirmed.append("Provider diagnostics query completed.")
        if not failed.get("id") or failed_state not in ("failed", "crashed", "error"):
            confirmed.append("No failed Railway deployment found in latest deployment evidence.")
            gaps.append("Need a specific failed deployment ID or service-scoped log pull to confirm runtime failure.")
            next_steps.append('Run: "check railway logs for <service-name>" after confirming target service.')
    else:
        gaps.append("Provider diagnostics did not return usable deployment evidence.")
        next_steps.append("Verify provider credentials and target service name.")

    healthy = corr.get("last_healthy_deployment") or {}
    if healthy.get("id"):
        signals.append(f"Last healthy deployment observed: `{healthy.get('id')}`.")

    if logs.strip():
        confidence_reasons.append("provider logs")
        low = logs.lower()
        if "module not found" in low or "cannot find module" in low:
            hypotheses.append(
                "Dependency/module resolution failure during startup — correlate package manifest changes with failing deployment."
            )
        if "memory" in low or "oom" in low or "heap" in low:
            hypotheses.append("Memory exhaustion during startup — inspect boot path and recent dependency changes.")

    eng = engineering_evidence or {}
    commits = eng.get("recent_commits") or []
    if commits:
        signals.append(f"Recent commit: {commits[0][:120]}")
        confidence_reasons.append("recent git activity")
    hot = eng.get("hot_files") or []
    if hot:
        path = hot[0].get("path") if isinstance(hot[0], dict) else str(hot[0])
        signals.append(f"Local repo change signal: `{path}` — related context only, not a confirmed deployment cause.")
    modified = int((eng.get("git") or {}).get("modified_count") or 0)
    if modified > 0:
        signals.append(f"Working tree has {modified} modified file(s).")

    browser = browser_evidence or {}
    if browser.get("target_unresolved"):
        signals.append("Browser capture skipped — deployment target URL could not be resolved.")
        gaps.append("Resolve public deployment URL or use provider metadata evidence.")
        next_steps.append('Run: "show project details for <target>" or configure public URL mapping.')
    elif browser.get("metadata_only"):
        signals.append("Browser metadata-only evidence captured (no live page screenshot).")
        confidence_reasons.append("browser metadata")
    elif browser.get("ok"):
        confidence_reasons.append("browser evidence")
        if browser.get("health_badge") == "failed":
            signals.append("Browser UI health indicator: failed.")

    if not hypotheses and confirmed and any("failed deployment" in c.lower() for c in confirmed):
        err = str(failed.get("error_message") or "")
        if err:
            hypotheses.append(f"Provider-reported failure may be explained by: {err[:240]}")
        elif logs.strip():
            hypotheses.append("Inspect attached log excerpt for startup/build failure class.")
        else:
            gaps.append("Provider confirmed failure state but no detailed error or logs in evidence.")

    if not confirmed and not hypotheses:
        gaps.append("Insufficient substrate evidence to confirm root cause.")

    confidence = "high" if len(confidence_reasons) >= 3 and hypotheses else "medium" if len(confidence_reasons) >= 2 else "low"

    return {
        "ok": True,
        "goal": goal[:500],
        "report_mode": report_mode,
        "conclusions": {
            "confirmed": confirmed,
            "hypotheses": hypotheses,
            "signals": signals,
            "gaps": gaps,
        },
        "findings": confirmed + hypotheses + signals,
        "confidence": confidence,
        "confidence_reason": confidence_reasons[:6],
        "next_steps": next_steps[:5],
        "read_only": True,
        "mutation_execution_enabled": False,
    }


def analyze_architecture_risks(
    *,
    engineering_evidence: dict[str, Any] | None,
    goal: str,
) -> dict[str, Any]:
    return _analyze_architecture_risk(engineering_evidence, goal)


def _analyze_architecture_risk(engineering_evidence: dict[str, Any] | None, goal: str) -> dict[str, Any]:
    eng = engineering_evidence or {}
    recommendations: list[str] = []
    for b in eng.get("bottlenecks") or []:
        recommendations.append(f"Harden {b.get('area')}: {b.get('detail')}")
    for s in eng.get("scalability_observations") or []:
        recommendations.append(str(s))
    if not recommendations:
        recommendations.append("Continue readonly architecture scans as codebase evolves.")

    return {
        "ok": True,
        "goal": goal[:500],
        "report_mode": "architecture_risk",
        "architecture_analysis": eng,
        "recommendations": recommendations[:8],
        "conclusions": {
            "confirmed": [f"Architecture scan completed for `{eng.get('repo') or 'workspace'}`."],
            "hypotheses": [],
            "signals": [b.get("detail", "") for b in (eng.get("bottlenecks") or [])[:4]],
            "gaps": [],
        },
        "confidence": "medium" if eng.get("layers") else "low",
        "confidence_reason": ["local workspace architecture scan"] if eng else [],
        "next_steps": ["Review bottleneck list and schedule next hardening slice under governance."],
        "read_only": True,
    }


def _analyze_pr_proposal(engineering_evidence: dict[str, Any] | None, goal: str) -> dict[str, Any]:
    eng = engineering_evidence or {}
    return {
        "ok": True,
        "goal": goal[:500],
        "report_mode": "pr_proposal",
        "pr_proposal": eng,
        "conclusions": {
            "confirmed": ["Dependency audit and PR proposal artifact generated (readonly)."],
            "hypotheses": [],
            "signals": [str(t.get("reason", "")) for t in (eng.get("modernization_targets") or [])[:4]],
            "gaps": [],
        },
        "confidence": "medium" if eng.get("modernization_targets") else "low",
        "confidence_reason": ["dependency audit"] if eng else [],
        "next_steps": ["Review phased migration plan; run mutation preflight before any write."],
        "read_only": True,
    }


def format_analysis_report(analysis: dict[str, Any]) -> str:
    mode = analysis.get("report_mode") or "deployment_failure"
    if mode == "architecture_risk":
        lines = ["# Architecture risk correlation", ""]
        for r in analysis.get("recommendations") or []:
            lines.append(f"- {r}")
        return "\n".join(lines)
    if mode == "pr_proposal":
        return "# PR proposal correlation\n\nDependency modernization proposal attached to merged report."

    conclusions = analysis.get("conclusions") or {}
    lines = [
        "# Evidence correlation (analyst)",
        "",
        f"**Confidence:** {analysis.get('confidence', 'low')}",
        "",
        "## Confirmed findings",
    ]
    for c in conclusions.get("confirmed") or []:
        lines.append(f"- {c}")
    lines.extend(["", "## Likely hypothesis"])
    for h in conclusions.get("hypotheses") or []:
        lines.append(f"- {h}")
    if not conclusions.get("hypotheses"):
        lines.append("- None supported by current evidence.")
    lines.extend(["", "## Related signals"])
    for s in conclusions.get("signals") or []:
        lines.append(f"- {s}")
    lines.extend(["", "## Evidence gaps"])
    for g in conclusions.get("gaps") or []:
        lines.append(f"- {g}")
    return "\n".join(lines)
