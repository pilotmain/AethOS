# SPDX-License-Identifier: Apache-2.0
"""Bounded agent delegation — substrate-first execution."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from aethos_core.agents.runtime.agent_context import AgentContext
from aethos_core.agents.runtime.agent_result_contract import build_agent_contract
from aethos_core.agents.runtime.artifacts import store_agent_artifact
from aethos_core.agents.runtime.registry import get_agent, validate_agent_action

_log = logging.getLogger("aethos.agents.delegation")


def delegate_agent_step(ctx: AgentContext) -> dict[str, Any]:
    """Execute one bounded agent step — returns evidence row, never mutates."""
    started = time.time()
    spec = get_agent(ctx.agent_id)
    if not spec:
        return _failure(ctx, "unknown_agent", started)

    policy = validate_agent_action(ctx.agent_id, ctx.action)
    if not policy.get("allowed"):
        return _failure(ctx, str(policy.get("reason") or "blocked"), started)

    try:
        output, summary, evidence_ids, extra = _run_substrate(ctx)
    except Exception as exc:
        artifact = store_agent_artifact(
            artifact_type="agent_failure",
            agent_id=ctx.agent_id,
            plan_id=None,
            payload={"context": ctx.to_dict(), "error": str(exc)},
            summary=f"{ctx.agent_id} failed: {exc}",
        )
        return {
            "agent_id": ctx.agent_id,
            "task": ctx.task,
            "action": ctx.action,
            "status": "failed",
            "error": str(exc),
            "artifact_id": artifact["artifact_id"],
            "duration_ms": int((time.time() - started) * 1000),
            "finished_at": time.time(),
            "policy_result": "blocked" if "blocked" in str(exc).lower() else "error",
        }

    duration_ms = int((time.time() - started) * 1000)
    typed = extra.get("typed_artifact_type") or "agent_evidence"
    evidence_art = store_agent_artifact(
        artifact_type=typed if typed in _ALLOWED_TYPED else "agent_evidence",
        agent_id=ctx.agent_id,
        plan_id=None,
        payload={
            "context": ctx.to_dict(),
            "output_preview": (output or "")[:2000],
            "substrate_payload": extra.get("substrate_payload") or {},
            "policy_result": "allowed",
        },
        summary=summary[:500],
    )
    evidence_ids = [evidence_art["artifact_id"], *evidence_ids]
    exec_art = store_agent_artifact(
        artifact_type="agent_execution",
        agent_id=ctx.agent_id,
        plan_id=None,
        payload={
            "agent_id": ctx.agent_id,
            "task": ctx.task,
            "inputs": [r.get("agent_id") for r in ctx.prior_results],
            "outputs": [summary[:240]],
            "duration_ms": duration_ms,
            "evidence_ids": evidence_ids,
            "substrate_invoked": extra.get("substrate_invoked") or [],
            "policy_result": "allowed",
        },
        summary=f"{ctx.agent_id} — {ctx.task}",
    )
    row: dict[str, Any] = {
        "agent_id": ctx.agent_id,
        "task": ctx.task,
        "action": ctx.action,
        "status": "completed",
        "summary": summary,
        "output": output,
        "artifact_id": exec_art["artifact_id"],
        "evidence_ids": evidence_ids,
        "duration_ms": duration_ms,
        "finished_at": time.time(),
        "policy_result": "allowed",
        "substrate_invoked": extra.get("substrate_invoked") or [],
    }
    if extra.get("analysis"):
        row["analysis"] = extra["analysis"]
    if extra.get("credential_required"):
        row["credential_required"] = True
    if extra.get("substrate_payload"):
        row["substrate_payload"] = extra["substrate_payload"]
    if extra.get("contract"):
        row["contract"] = extra["contract"]
    if extra.get("deployment_intelligence"):
        row["deployment_intelligence"] = extra["deployment_intelligence"]
    return row


_ALLOWED_TYPED = frozenset(
    {
        "agent_evidence",
        "agent_provider_diagnostics",
        "agent_browser_evidence",
        "agent_root_cause_analysis",
        "engineering_architecture_graph",
        "engineering_dependency_risk",
        "engineering_git_hotspots",
        "engineering_ci_analysis",
        "engineering_pr_proposal",
        "engineering_preflight",
        "engineering_patch_plan",
        "engineering_execution",
        "engineering_pr_draft",
    }
)


def _failure(ctx: AgentContext, reason: str, started: float) -> dict[str, Any]:
    artifact = store_agent_artifact(
        artifact_type="agent_failure",
        agent_id=ctx.agent_id,
        plan_id=None,
        payload={"context": ctx.to_dict(), "reason": reason},
        summary=f"{ctx.agent_id} blocked: {reason}",
    )
    return {
        "agent_id": ctx.agent_id,
        "task": ctx.task,
        "status": "failed",
        "error": reason,
        "artifact_id": artifact["artifact_id"],
        "duration_ms": int((time.time() - started) * 1000),
        "finished_at": time.time(),
        "policy_result": "blocked",
    }


def _repo_from_hint(hint: str | None, session_id: str) -> Path:
    from aethos_core.local_workspace.readonly.actions import _repo_from_hint as resolve

    return resolve(hint, session_id=session_id)


def _run_planning(ctx: AgentContext, extra: dict[str, Any]) -> tuple[str, str, list[str], dict[str, Any]]:
    """Generative team-planning agent — produces this role's slice of a coordinated plan via the
    LLM. Read-only: it writes a PLAN, never code or infrastructure. Used when the orchestrator
    builds a named team (architect/developer/tester/devops/…) for a build/plan goal.
    """
    role, _, deliverable = (ctx.task or "").partition(":")
    role = (role or ctx.agent_id).strip() or "specialist"
    deliverable = deliverable.strip() or "your part of the plan"

    from aethos_core.provider.completion import complete_chat, provider_configured

    if not provider_configured():
        body = (
            f"# {role.title()} agent\n\nNo model provider is configured, so the {deliverable} "
            "can't be generated. Connect a provider key in Mission Control → Advanced settings → Credentials."
        )
        extra["contract"] = build_agent_contract(
            agent_id=ctx.agent_id, task=ctx.task, status="blocked", findings=[],
            evidence=[], limitations=["No model provider configured."],
            next_steps=["Add a provider API key, then re-run."], confidence="low",
        )
        return body, f"{role}: provider not configured", [], extra

    system = (
        f"You are the {role.title()} on a software delivery team (alongside an architect, developer, "
        f"tester, and devops engineer). Produce ONLY your slice: the {deliverable}. Be concrete, "
        "structured, and actionable, with concise bullet points. This is a PLAN — never claim "
        "anything was built, committed, or deployed."
    )
    try:
        result = complete_chat(ctx.user_request, session_id=ctx.session_id, include_identity=False, system_overlay=system)
        plan_text = (result.text or "").strip()
    except Exception as exc:  # noqa: BLE001 — surface honestly, never crash coordination.
        plan_text = ""
        _log.warning("planning agent %s failed: %s", role, exc.__class__.__name__)

    if not plan_text:
        plan_text = f"(The {role} could not produce a {deliverable} this run.)"
    findings = [ln.strip("-• ").strip() for ln in plan_text.splitlines() if ln.strip()][:8]
    body = f"# {role.title()} — {deliverable}\n\n{plan_text}"
    extra["contract"] = build_agent_contract(
        agent_id=ctx.agent_id, task=ctx.task, status="completed", findings=findings,
        evidence=[], limitations=[], next_steps=[], confidence="medium",
        substrate_invoked=["llm_planning"],
    )
    extra["typed_artifact_type"] = "agent_evidence"
    return body, f"{role}: {deliverable}", [], extra


def _run_substrate(ctx: AgentContext) -> tuple[str, str, list[str], dict[str, Any]]:
    hint = ctx.workspace_hint or "aethos"
    evidence_ids: list[str] = []
    extra: dict[str, Any] = {}

    # Generative team-planning (build/plan goals) — any role capability routes here.
    if ctx.action == "team_planning":
        return _run_planning(ctx, extra)

    if ctx.agent_id == "code_intelligence":
        return _run_engineering(ctx, hint, evidence_ids, extra)

    if ctx.agent_id == "provider_ops":
        return _run_provider_ops(ctx, evidence_ids, extra)

    if ctx.agent_id == "web_evidence":
        return _run_browser_evidence(ctx, evidence_ids, extra)

    if ctx.agent_id == "research":
        return _run_research(ctx.user_request, evidence_ids, extra)

    if ctx.agent_id == "operations_analyst":
        return _run_analyst(ctx, extra)

    if ctx.agent_id == "dev_workspace":
        return _run_developer(ctx, hint, evidence_ids, extra)

    return ("No substrate for agent.", f"{ctx.agent_id} — no handler", evidence_ids, extra)


def _run_engineering(
    ctx: AgentContext,
    hint: str,
    evidence_ids: list[str],
    extra: dict[str, Any],
) -> tuple[str, str, list[str], dict[str, Any]]:
    from aethos_core.agents.engineering.architecture_reasoning import (
        format_architecture_reasoning_report,
        run_architecture_reasoning,
    )
    from aethos_core.agents.engineering.ci_reasoning import format_ci_reasoning_report, run_ci_reasoning
    from aethos_core.agents.engineering.dependency_reasoning import (
        format_dependency_reasoning_report,
        run_dependency_reasoning,
    )
    from aethos_core.agents.engineering.git_hotspots import format_git_hotspot_report, run_git_hotspot_analysis
    from aethos_core.agents.engineering.pr_proposal_engine import (
        build_dependency_modernization_proposal,
        format_pr_proposal_report,
    )
    from aethos_core.agents.engineering.risk_scoring import classify_severity
    from aethos_core.local_workspace.artifacts.store import store_workspace_artifact

    repo = _repo_from_hint(hint, ctx.session_id)
    action = ctx.action
    extra["substrate_invoked"] = ["local_workspace"]

    if action in ("architecture_analysis", "architecture_scan"):
        from aethos_core.agents.engineering.architecture_intelligence import (
            format_architecture_intelligence_report,
            run_architecture_intelligence,
        )

        analysis = run_architecture_intelligence(repo)
        art = store_workspace_artifact(
            artifact_type="architecture_analysis",
            workspace_id=None,
            repo_path=str(repo),
            payload=analysis,
            summary="Engineering architecture graph",
        )
        if art.get("artifact_id"):
            evidence_ids.append(art["artifact_id"])
        sev = classify_severity(signals=analysis.get("risk_signals") or [])
        extra.update(
            {
                "typed_artifact_type": "engineering_architecture_graph",
                "substrate_payload": analysis,
                "analysis": {"severity": sev.get("severity")},
            }
        )
        return format_architecture_intelligence_report(analysis), "Architecture intelligence + operational health", evidence_ids, extra

    if action in ("dependency_audit",):
        analysis = run_dependency_reasoning(repo)
        art = store_workspace_artifact(
            artifact_type="dependency_audit",
            workspace_id=None,
            repo_path=str(repo),
            payload=analysis,
            summary=f"Dependency risk — {analysis.get('severity')}",
        )
        if art.get("artifact_id"):
            evidence_ids.append(art["artifact_id"])
        sev = classify_severity(signals=analysis.get("risk_signals") or [])
        extra.update(
            {
                "typed_artifact_type": "engineering_dependency_risk",
                "substrate_payload": analysis,
                "analysis": {"severity": sev.get("severity")},
            }
        )
        return format_dependency_reasoning_report(analysis), "Dependency audit + modernization targets", evidence_ids, extra

    if action in ("ci_analysis",):
        analysis = run_ci_reasoning(repo)
        extra["typed_artifact_type"] = "engineering_ci_analysis"
        extra["substrate_payload"] = analysis
        return format_ci_reasoning_report(analysis), "CI/workflow analysis", evidence_ids, extra

    if action in ("git_correlation", "git_hotspots"):
        analysis = run_git_hotspot_analysis(repo)
        art = store_workspace_artifact(
            artifact_type="git_status_snapshot",
            workspace_id=None,
            repo_path=str(repo),
            payload=analysis,
            summary="Git hotspot analysis",
        )
        if art.get("artifact_id"):
            evidence_ids.append(art["artifact_id"])
        extra.update(
            {
                "typed_artifact_type": "engineering_git_hotspots",
                "substrate_payload": analysis,
            }
        )
        return format_git_hotspot_report(analysis), "Git hotspot + recent commit correlation", evidence_ids, extra

    if action == "pr_proposal_generation":
        proposal = build_dependency_modernization_proposal(repo, user_request=ctx.user_request)
        art = store_agent_artifact(
            artifact_type="engineering_pr_proposal",
            agent_id="code_intelligence",
            plan_id=None,
            payload=proposal,
            summary="PR proposal — dependency modernization (preflight only)",
        )
        evidence_ids.append(art["artifact_id"])
        extra["typed_artifact_type"] = "engineering_pr_proposal"
        extra["substrate_payload"] = proposal
        return format_pr_proposal_report(proposal), "PR proposal artifact generated", evidence_ids, extra

    if action in ("engineering_preflight", "patch_planning"):
        from aethos_core.engineering.governance.engineering_preflight import run_and_record_engineering_preflight

        preflight = run_and_record_engineering_preflight(
            user_request=ctx.user_request,
            repo=repo,
            workspace_hint=hint,
            session_id=ctx.session_id,
            source="agent",
        )
        art = store_agent_artifact(
            artifact_type="engineering_preflight",
            agent_id="code_intelligence",
            plan_id=None,
            payload=preflight,
            summary=f"Engineering preflight — {preflight.get('risk_tier')}",
        )
        evidence_ids.append(art["artifact_id"])
        extra["typed_artifact_type"] = "engineering_preflight"
        extra["substrate_payload"] = preflight
        return preflight.get("report") or "", "Engineering preflight (approval required)", evidence_ids, extra

    analysis = run_architecture_reasoning(repo)
    return format_architecture_reasoning_report(analysis), "Engineering scan complete", evidence_ids, extra


def _run_provider_ops(
    ctx: AgentContext,
    evidence_ids: list[str],
    extra: dict[str, Any],
) -> tuple[str, str, list[str], dict[str, Any]]:
    from aethos_core.agents.providers.github_reasoning import run_github_diagnostics
    from aethos_core.agents.providers.railway_reasoning import run_railway_diagnostics
    from aethos_core.agents.providers.vercel_reasoning import run_vercel_diagnostics

    lower = ctx.user_request.lower()
    extra["substrate_invoked"] = ["provider_readonly"]

    if "railway" in lower or "deployment" in lower:
        from aethos_core.agents.providers.deployment_intelligence import build_deployment_intelligence

        intel = build_deployment_intelligence(ctx.user_request)
        diag = intel if intel.get("provider") == "railway" else run_railway_diagnostics(ctx.user_request)
        if intel.get("provider") == "railway":
            diag = {**diag, **intel}
        extra["typed_artifact_type"] = "agent_provider_diagnostics"
        extra["substrate_payload"] = diag
        extra["deployment_intelligence"] = intel
        if diag.get("credential_required") or intel.get("credential_state") == "unavailable":
            extra["credential_required"] = True
        art = store_agent_artifact(
            artifact_type="agent_provider_diagnostics",
            agent_id="provider_ops",
            plan_id=None,
            payload=diag,
            summary="Railway deployment diagnostics",
        )
        evidence_ids.append(art["artifact_id"])
        findings = []
        limitations = []
        next_steps = []
        if diag.get("credential_required") or intel.get("credential_state") == "unavailable":
            findings.append("Railway credential unavailable — provider evidence could not be fetched.")
            limitations.append("No deployment list or logs without valid Railway API token.")
            next_steps.append('Connect Railway in Mission Control, then rerun failure analysis.')
        elif diag.get("failed_deployment_found"):
            dep_id = diag.get("deployment_id") or ((diag.get("correlation") or {}).get("failed_deployment") or {}).get("id")
            findings.append(f"Failed deployment evidence: `{dep_id}` state {diag.get('deployment_state') or 'unknown'}.")
            if not diag.get("logs_available"):
                limitations.append("Railway logs were empty or unavailable for this query.")
                next_steps.append(f'Run: "check railway logs for {diag.get("service_name") or "target-service"}".')
        else:
            findings.append("No failed Railway deployment found in latest deployment evidence.")
            limitations.append("Latest deployment list did not include a failed/crashed state.")
            next_steps.append(f'Confirm service name and run: "check railway logs for {diag.get("service_name") or "<service>"}".')
        extra["contract"] = _provider_contract(ctx, diag, findings, limitations, next_steps)
        return diag.get("report") or "", "Railway deployment diagnostics (substrate-backed)", evidence_ids, extra

    if "vercel" in lower:
        diag = run_vercel_diagnostics(ctx.user_request)
        extra["substrate_payload"] = diag
        art = store_agent_artifact(
            artifact_type="agent_provider_diagnostics",
            agent_id="provider_ops",
            plan_id=None,
            payload=diag,
            summary="Vercel deployment diagnostics",
        )
        evidence_ids.append(art["artifact_id"])
        return diag.get("report") or "", "Vercel deployment diagnostics", evidence_ids, extra

    if "github" in lower or "workflow" in lower:
        diag = run_github_diagnostics(ctx.user_request)
        extra["substrate_payload"] = diag
        art = store_agent_artifact(
            artifact_type="agent_provider_diagnostics",
            agent_id="provider_ops",
            plan_id=None,
            payload=diag,
            summary="GitHub workflow diagnostics",
        )
        evidence_ids.append(art["artifact_id"])
        return diag.get("report") or "", "GitHub workflow diagnostics", evidence_ids, extra

    diag = run_railway_diagnostics(ctx.user_request)
    extra["substrate_payload"] = diag
    return diag.get("report") or "Provider diagnostics unavailable.", "Provider operational diagnostics", evidence_ids, extra


def _run_browser_evidence(
    ctx: AgentContext,
    evidence_ids: list[str],
    extra: dict[str, Any],
) -> tuple[str, str, list[str], dict[str, Any]]:
    from aethos_core.browser.deployment_url_resolution import is_deployment_evidence_prompt, resolve_deployment_evidence_target
    from aethos_core.browser.runtime.browser_runtime import run_deployment_evidence_capture

    extra["substrate_invoked"] = ["browser_capture_execution"]
    user_request = ctx.user_request

    if is_deployment_evidence_prompt(user_request) or ctx.action in ("deployment_capture", "metadata"):
        target_info = resolve_deployment_evidence_target(user_request)
        if not target_info:
            provider_hint = "railway" if "railway" in user_request.lower() else "target"
            prov_intel = _provider_intel_from_prior(ctx.prior_results)
            correlation_lines = _browser_provider_correlation(prov_intel, provider_hint)
            body = (
                "# Browser evidence (governed)\n\n"
                "Browser capture **skipped** because no public deployment URL was resolved.\n\n"
                + ("\n".join(f"- {line}" for line in correlation_lines) + "\n\n" if correlation_lines else "")
                + "- Provider metadata evidence may still be available from the provider agent.\n"
                f"- **Suggested next step:** run `show project details for <{provider_hint}-service>` "
                "or configure public URL mapping in Mission Control.\n"
                "- Browser capture requires a resolved deployment target — never direct Playwright bypass."
            )
            browser_payload = {
                "ok": False,
                "target_unresolved": True,
                "provider_hint": provider_hint,
                "provider_correlation": correlation_lines,
            }
            extra["substrate_payload"] = browser_payload
            extra["substrate_invoked"] = []
            extra["contract"] = _browser_contract(
                ctx,
                browser_payload,
                findings=["Browser capture skipped — deployment target URL unresolved."]
                + ([correlation_lines[0]] if correlation_lines else []),
                limitations=["No screenshot, console, or network capture without resolved URL."],
                next_steps=[
                    f'Show project details for your deployment target, or run deployment evidence with explicit URL.',
                ],
                confidence="low",
            )
            return body, "Browser capture skipped — target unresolved", evidence_ids, extra

        provider, target = target_info
        result = run_deployment_evidence_capture(
            user_request=user_request,
            provider=provider,
            target=target,
            session_id=ctx.session_id,
            approved=True,
            capture_type="full",
        )
        artifacts = result.get("artifacts") or []
        for art in artifacts:
            aid = art.get("artifact_id")
            if aid:
                evidence_ids.append(str(aid))

        metadata = {}
        for art in artifacts:
            payload = art.get("payload") or {}
            meta = payload.get("metadata") or payload
            if isinstance(meta, dict):
                metadata.update(meta)

        health = "failed" if result.get("metadata_only") and not result.get("ok") else "degraded" if result.get("metadata_only") else "ok"
        browser_payload = {
            "ok": result.get("ok"),
            "metadata_only": result.get("metadata_only"),
            "health_badge": health,
            "metadata": metadata,
            "artifact_ids": [a.get("artifact_id") for a in artifacts],
            "summary": result.get("summary"),
        }
        art = store_agent_artifact(
            artifact_type="agent_browser_evidence",
            agent_id="web_evidence",
            plan_id=None,
            payload=browser_payload,
            summary=result.get("summary") or "Browser deployment evidence",
        )
        evidence_ids.append(art["artifact_id"])
        extra["typed_artifact_type"] = "agent_browser_evidence"
        extra["substrate_payload"] = browser_payload
        findings = [result.get("summary") or "Browser capture completed."]
        limitations = []
        if result.get("metadata_only"):
            limitations.append("Metadata-only fallback — no live screenshot (public URL unavailable or capture skipped).")
        extra["contract"] = _browser_contract(ctx, browser_payload, findings, limitations, [
            "Review attached browser artifacts in Mission Control → Browser Evidence.",
        ], confidence="medium" if artifacts else "low")

        lines = [
            "# Browser deployment evidence (governed capture)",
            "",
            result.get("summary") or "Capture completed.",
            "",
            f"**Artifacts attached:** {len(artifacts)}",
        ]
        for art in artifacts[:4]:
            lines.append(f"- `{art.get('artifact_id')}` · {art.get('artifact_type')}")
        if result.get("metadata_only"):
            lines.append("- Metadata-only fallback (no public URL or capture skipped)")
        return "\n".join(lines), "Browser evidence captured via governed pipeline", evidence_ids, extra

    body = (
        "# Browser evidence agent (governed)\n\n"
        "Deployment/page evidence requires a **governed browser capture** with resolved target.\n"
        "Include deployment context: e.g. analyze why Railway deployment failed."
    )
    return body, "Browser evidence requires deployment context", evidence_ids, extra


def _run_research(user_request: str, evidence_ids: list[str], extra: dict[str, Any]) -> tuple[str, str, list[str], dict[str, Any]]:
    body = (
        "# Research agent (evidence-first)\n\n"
        "Research outputs require citations and provenance. "
        "Use provider readonly jobs for inventory — not uncited LLM claims.\n\n"
        f"Query scope: {user_request[:200]}"
    )
    extra["substrate_invoked"] = []
    return body, "Research scaffold (evidence-only)", evidence_ids, extra


def _run_developer(
    ctx: AgentContext,
    hint: str,
    evidence_ids: list[str],
    extra: dict[str, Any],
) -> tuple[str, str, list[str], dict[str, Any]]:
    from aethos_core.workspace_runtime.workspace_runtime import run_workspace_diagnostics

    repo = _repo_from_hint(hint, ctx.session_id)
    diagnostics = run_workspace_diagnostics(workspace_id=None, hint=hint, user_request=ctx.user_request)
    extra["substrate_invoked"] = ["workspace_runtime", "local_workspace"]
    extra["substrate_payload"] = diagnostics
    art = store_agent_artifact(
        artifact_type="agent_evidence",
        agent_id="dev_workspace",
        plan_id=None,
        payload={"diagnostics": diagnostics, "repo_path": str(repo), "action": ctx.action},
        summary="Developer workspace diagnostics (readonly)",
    )
    evidence_ids.append(art["artifact_id"])
    lines = [
        "# Developer agent — workspace diagnostics (governed)",
        "",
        f"**Repo:** `{repo}`",
        "",
        "Cursor/terminal mutations require **terminal preflight + approval** — this agent does not auto-run Cursor.",
        "",
        "## Findings",
    ]
    for row in list(diagnostics.get("checks") or [])[:8]:
        if isinstance(row, dict):
            lines.append(f"- **{row.get('name') or 'check'}** — {row.get('status') or row.get('detail') or 'ok'}")
    summary = diagnostics.get("summary") or "Workspace diagnostics complete."
    lines.extend(["", summary])
    return "\n".join(lines), "Developer workspace diagnostics", evidence_ids, extra


def _run_analyst(ctx: AgentContext, extra: dict[str, Any]) -> tuple[str, str, list[str], dict[str, Any]]:
    from aethos_core.agents.providers.runtime_failure_analysis import (
        analyze_architecture_risks,
        analyze_runtime_failure,
        format_analysis_report,
    )
    from aethos_core.agents.engineering.architecture_intelligence import run_architecture_intelligence
    from aethos_core.agents.runtime.evidence_correlation_engine import correlate_operational_evidence
    from aethos_core.agents.runtime.report_mode import infer_report_mode

    report_mode = infer_report_mode(ctx.user_request)
    provider_evidence: dict[str, Any] | None = None
    engineering_evidence: dict[str, Any] | None = None
    browser_evidence: dict[str, Any] | None = None
    deployment_intel: dict[str, Any] | None = None

    for prior in ctx.prior_results:
        aid = str(prior.get("agent_id") or "")
        payload = prior.get("substrate_payload") or {}
        if not payload:
            continue
        if aid == "provider_ops":
            provider_evidence = payload
            deployment_intel = prior.get("deployment_intelligence") or payload
        elif aid == "code_intelligence":
            engineering_evidence = payload
        elif aid == "web_evidence":
            browser_evidence = payload

    correlation = correlate_operational_evidence(
        provider=provider_evidence,
        engineering=engineering_evidence,
        browser=browser_evidence,
        deployment_intel=deployment_intel,
        report_mode=report_mode,
    )

    if report_mode == "architecture_risk":
        repo = _repo_from_hint(ctx.workspace_hint or "aethos", ctx.session_id)
        arch_intel = run_architecture_intelligence(repo)
        analysis = analyze_architecture_risks(engineering_evidence=arch_intel, goal=ctx.user_request)
        analysis["architecture_health"] = arch_intel.get("architecture_health")
        analysis["top_risks"] = arch_intel.get("top_risks")
    else:
        analysis = analyze_runtime_failure(
            provider_evidence=provider_evidence,
            engineering_evidence=engineering_evidence,
            browser_evidence=browser_evidence,
            goal=ctx.user_request,
            report_mode=report_mode,
        )
        conc = correlation.get("conclusions") or {}
        merged_conc = analysis.get("conclusions") or {}
        for key in ("confirmed", "hypotheses", "signals", "gaps"):
            existing = list(merged_conc.get(key) or [])
            for item in conc.get(key) or []:
                if item not in existing:
                    existing.append(item)
            merged_conc[key] = existing
        analysis["conclusions"] = merged_conc
        analysis["correlation"] = correlation
    report = format_analysis_report(analysis)
    art = store_agent_artifact(
        artifact_type="agent_root_cause_analysis",
        agent_id="operations_analyst",
        plan_id=None,
        payload=analysis,
        summary=f"Analyst — {report_mode.replace('_', ' ')}",
    )
    op_art = store_agent_artifact(
        artifact_type="agent_operational_report",
        agent_id="operations_analyst",
        plan_id=None,
        payload={"analysis": analysis, "report": report, "report_mode": report_mode},
        summary=f"Operational report — {report_mode.replace('_', ' ')}",
    )
    evidence_ids = [art["artifact_id"], op_art["artifact_id"]]
    from aethos_core.agents.runtime.agent_result_contract import build_agent_contract

    conc = analysis.get("conclusions") or {}
    extra.update(
        {
            "typed_artifact_type": "agent_root_cause_analysis",
            "substrate_payload": analysis,
            "analysis": analysis,
            "substrate_invoked": ["evidence_correlation"],
            "contract": build_agent_contract(
                agent_id="operations_analyst",
                task=ctx.task,
                status="completed",
                findings=(conc.get("confirmed") or [])[:3] + (conc.get("hypotheses") or [])[:2],
                evidence=[f"Correlated {len(ctx.prior_results)} prior agent result(s)"],
                limitations=conc.get("gaps") or [],
                next_steps=analysis.get("next_steps") or [],
                confidence=str(analysis.get("confidence") or "low"),
                substrate_invoked=["evidence_correlation"],
            ),
        }
    )
    label = report_mode.replace("_", " ")
    return report, f"Mission analyst — {label}", evidence_ids, extra


def _provider_intel_from_prior(prior_results: list[dict[str, Any]]) -> dict[str, Any]:
    for prior in prior_results:
        if prior.get("agent_id") == "provider_ops":
            return dict(prior.get("deployment_intelligence") or prior.get("substrate_payload") or {})
    return {}


def _browser_provider_correlation(intel: dict[str, Any], provider_hint: str) -> list[str]:
    lines: list[str] = []
    latest = intel.get("latest_deployment") or {}
    state = str(latest.get("state") or intel.get("deployment_state") or "").lower()
    if state and state not in ("failed", "crashed", "error"):
        lines.append("Latest deployment appears healthy — browser failure likely due to missing public domain mapping.")
    elif state in ("failed", "crashed", "error"):
        lines.append("Latest deployment is unhealthy — browser capture may have failed due to unresolved production URL.")
    else:
        lines.append("No public deployment domain was found for browser capture.")
    if intel.get("credential_state") == "unavailable":
        lines.append("Provider credentials unavailable — DNS/domain health could not be verified.")
    if not latest.get("id"):
        lines.append(f"No mapped production domain was found for {provider_hint}.")
    return lines[:4]


def _provider_contract(
    ctx: AgentContext,
    diag: dict[str, Any],
    findings: list[str],
    limitations: list[str],
    next_steps: list[str],
) -> dict[str, Any]:
    from aethos_core.agents.runtime.agent_result_contract import build_agent_contract

    conf = "low" if diag.get("credential_required") or diag.get("credential_state") == "unavailable" else "medium" if diag.get("ok") else "low"
    evidence = []
    if diag.get("deployment_id"):
        evidence.append(f"Deployment query: `{diag.get('deployment_id')}`")
    if diag.get("service_name"):
        evidence.append(f"Service: {diag.get('service_name')}")
    return build_agent_contract(
        agent_id="provider_ops",
        task=ctx.task,
        status="completed",
        findings=findings,
        evidence=evidence,
        limitations=limitations,
        next_steps=next_steps,
        confidence=conf,
        substrate_invoked=["provider_readonly"],
    )


def _browser_contract(
    ctx: AgentContext,
    payload: dict[str, Any],
    findings: list[str],
    limitations: list[str],
    next_steps: list[str],
    *,
    confidence: str = "low",
) -> dict[str, Any]:
    from aethos_core.agents.runtime.agent_result_contract import build_agent_contract

    evidence = [f"Artifacts: {len(payload.get('artifact_ids') or [])}"]
    return build_agent_contract(
        agent_id="web_evidence",
        task=ctx.task,
        status="completed" if payload.get("ok") else "partial",
        findings=findings,
        evidence=evidence,
        limitations=limitations,
        next_steps=next_steps,
        confidence=confidence,
        substrate_invoked=["browser_capture_execution"] if not payload.get("target_unresolved") else [],
    )
