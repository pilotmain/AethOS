# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun post-mutation follow-ups."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.providers.github.context.github_context_store import (
    assert_valid_repo_context,
    get_active_github_context,
    get_github_rerun_context,
)

_RERUN_STATUS_RX = re.compile(
    r"\b("
    r"did\s+(?:the\s+)?workflow\s+rerun"
    r"|did\s+it\s+pass"
    r"|what\s+failed\s+this\s+time"
    r"|did\s+it\s+deploy\s+after\s+(?:the\s+)?rerun"
    r"|did\s+deployment\s+reach\s+runtime"
    r"|where\s+is\s+the\s+failure\s+boundary"
    r"|should\s+we\s+rerun\s+again"
    r"|did\s+the\s+rerun\s+(?:pass|fail|work)"
    r")\b",
    re.I,
)


def is_github_workflow_rerun_followup(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_RERUN_STATUS_RX.search(raw))


def compose_github_workflow_rerun_followup_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
        compose_rerun_no_execution_followup,
    )

    no_exec = compose_rerun_no_execution_followup(text, session_id=session_id)
    if no_exec is not None:
        return no_exec

    if not _RERUN_STATUS_RX.search(text or ""):
        return None

    lifecycle = _recent_github_rerun_state(session_id=session_id)
    if lifecycle is None:
        return _compose_pre_execution_followup(text, session_id=session_id)

    verification = dict(lifecycle.get("verification") or {})
    provider_result = dict(lifecycle.get("provider_result") or {})
    rerun_ctx = get_github_rerun_context(session_id) or {}
    repo = _validated_repo(
        lifecycle.get("target_name"),
        provider_result.get("repository"),
        rerun_ctx.get("rerun_target_repo"),
        (get_active_github_context(session_id) or {}).get("repo_full_name"),
    )
    if not repo:
        return _compose_pre_execution_followup(text, session_id=session_id)

    lines = [f"GitHub workflow rerun follow-up for **{repo}**:"]
    original_run = rerun_ctx.get("original_run_id") or verification.get("source_run_id") or provider_result.get("source_run_id")
    rerun_run = rerun_ctx.get("rerun_run_id") or verification.get("rerun_run_id") or verification.get("new_run_id")
    if original_run or rerun_run:
        lines.append(f"- Lineage: `{original_run or '—'}` → `{rerun_run or '—'}`")

    lower = (text or "").lower()
    deployment_chain = dict(verification.get("deployment_chain") or rerun_ctx.get("deployment_chain") or {})

    if "did it pass" in lower or "did the rerun pass" in lower:
        outcome = str(
            verification.get("rerun_outcome")
            or rerun_ctx.get("rerun_outcome")
            or verification.get("verification_result")
            or verification.get("run_conclusion")
            or "unknown"
        )
        lines.append(f"- Workflow outcome: **{outcome}**")
        if verification.get("chain_summary") or rerun_ctx.get("chain_summary"):
            lines.append(f"- Chain: {verification.get('chain_summary') or rerun_ctx.get('chain_summary')}")
        elif outcome == "passed" and deployment_chain.get("workflow_passed_deploy_failed"):
            lines.append("- GitHub passed, but deployment success is **not confirmed**.")
    elif "what failed" in lower:
        job = verification.get("likely_failure_job") or rerun_ctx.get("likely_failure_job")
        step = verification.get("likely_failure_step") or rerun_ctx.get("likely_failure_step")
        if job:
            lines.append(f"- Likely failure: `{job}` / `{step or 'unknown step'}`")
        else:
            lines.append(
                f"- Failure classification: `{verification.get('failure_classification') or provider_result.get('failure_classification') or 'unknown'}`"
            )
            lines.append("- Next step: inspect failed workflow jobs/logs for the rerun run.")
    elif "deploy after rerun" in lower or "deployment reach runtime" in lower:
        boundary = deployment_chain.get("failure_boundary") or rerun_ctx.get("failure_boundary_after_rerun") or "unknown"
        verdict = str(deployment_chain.get("chain_verdict") or rerun_ctx.get("chain_verdict") or "")
        lines.append(f"- Failure boundary after rerun: **{boundary}**")
        if verdict:
            lines.append(f"- Chain verdict (refreshed evidence): **{verdict}**")
        if deployment_chain.get("evidence_refreshed") or rerun_ctx.get("evidence_refreshed"):
            lines.append("- Downstream Vercel/Railway evidence was **refreshed** after rerun completion.")
        if verdict == "deploy_not_triggered" or verdict == "deploy_not_triggered_after_wait":
            lines.append("- GitHub passed, but no Vercel deployment matched the rerun commit.")
        elif verdict == "deploy_still_pending":
            waited = int((deployment_chain.get("poll_metadata") or {}).get("deploy_poll_seconds") or 120)
            lines.append(
                f"- GitHub passed, but downstream deployment is still pending after a {waited}s wait window."
            )
        elif verdict == "inconclusive_timeout":
            lines.append("- Downstream evidence did not stabilize within the bounded wait window.")
        elif verdict == "deploy_blocked" or deployment_chain.get("workflow_passed_deploy_failed"):
            lines.append("- GitHub workflow passed, but correlated Vercel deployment is still failing.")
        elif verdict == "runtime_regressed" or deployment_chain.get("deploy_succeeded_runtime_unhealthy"):
            lines.append("- Deploy looks healthy, but Railway runtime is still unhealthy.")
        elif verdict == "chain_healthy" or deployment_chain.get("chain_healthy"):
            lines.append("- Deployment reached runtime on the refreshed chain.")
        elif deployment_chain.get("rerun_triggered_nothing"):
            lines.append("- No new workflow run was detected after rerun.")
        if deployment_chain.get("new_deployment_created"):
            lines.append("- A **new** Vercel deployment was observed for the rerun commit.")
        elif deployment_chain.get("deployment_reused_previous_build"):
            lines.append("- Vercel reused the **previous build** for the rerun commit.")
        timeline = list(deployment_chain.get("timeline") or rerun_ctx.get("timeline") or [])
        for event in timeline[:4]:
            lines.append(f"- Timeline · {event.get('phase')}: **{event.get('status')}** — {event.get('detail')}")
    elif "failure boundary" in lower:
        from aethos_core.cross_provider_correlation.correlation_runtime import build_correlation_state

        state = build_correlation_state(session_id=session_id)
        corr = dict(state.get("cross_provider_correlation") or {})
        boundary = corr.get("failure_boundary") or deployment_chain.get("failure_boundary") or rerun_ctx.get("failure_boundary_after_rerun") or "unknown"
        lines.append(f"- Current failure boundary: **{boundary}**")
        if rerun_ctx.get("evidence_refreshed") or deployment_chain.get("evidence_refreshed"):
            lines.append("- Boundary recomputed from **refreshed** Vercel/Railway evidence after rerun.")
        verdict = str(deployment_chain.get("chain_verdict") or rerun_ctx.get("chain_verdict") or "")
        if verdict:
            lines.append(f"- Chain verdict: **{verdict}**")
        if corr.get("conclusion"):
            lines.append(f"- {corr['conclusion']}")
    elif "rerun again" in lower:
        outcome = str(verification.get("rerun_outcome") or rerun_ctx.get("rerun_outcome") or "")
        if outcome == "passed" and deployment_chain.get("chain_healthy"):
            lines.append("- Latest rerun passed and the correlated chain looks healthy — another rerun is usually unnecessary.")
        elif outcome == "passed":
            lines.append("- Workflow passed, but downstream deploy/runtime may still need inspection before rerunning again.")
        else:
            lines.append("- Latest rerun did not fully succeed — you may create a new governed rerun preflight if CI is still failing.")
    else:
        from aethos_core.providers.github.mutations.workflow_rerun_verification import summarize_verification_for_operator

        lines.append(f"- {summarize_verification_for_operator({**rerun_ctx, **verification})}")

    lines.extend(["", "No new mutation has been performed."])
    return (
        "\n".join(lines),
        "github_workflow_rerun_followup",
        {
            "route_id": "github_workflow_rerun_followup",
            "matched_module": "providers.github.mutations.rerun_followup_router",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "repository": repo,
        },
    )


def _compose_pre_execution_followup(
    text: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    rerun_ctx = get_github_rerun_context(session_id) or {}
    gh_ctx = get_active_github_context(session_id) or {}
    repo = _validated_repo(
        rerun_ctx.get("rerun_target_repo"),
        gh_ctx.get("repo_full_name"),
    )
    lines = ["No GitHub workflow rerun has been executed yet."]
    if repo:
        lines.append(f"The last diagnosed repo was **{repo}**.")
    lines.append("I can rerun a failed workflow only if one exists and you approve the preflight.")
    lines.append("")
    lines.append("No mutation has been performed.")
    return (
        "\n".join(lines),
        "github_workflow_rerun_followup",
        {
            "route_id": "github_workflow_rerun_followup",
            "matched_module": "providers.github.mutations.rerun_followup_router",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "repository": repo or "",
            "rerun_executed": "false",
        },
    )


def _validated_repo(*candidates: Any) -> str:
    for candidate in candidates:
        repo = str(candidate or "").strip()
        valid, _ = assert_valid_repo_context(repo)
        if valid:
            return repo
    return ""


def _recent_github_rerun_state(*, session_id: str) -> dict[str, Any] | None:
    lifecycle = _recent_executed_github_rerun_lifecycle(session_id=session_id)
    if lifecycle is not None:
        return lifecycle
    rerun_ctx = get_github_rerun_context(session_id) or {}
    if rerun_ctx.get("rerun_run_id") or rerun_ctx.get("rerun_outcome"):
        repo = str(rerun_ctx.get("rerun_target_repo") or "")
        valid, _ = assert_valid_repo_context(repo)
        if not valid:
            return None
        return {
            "target_name": repo,
            "provider_result": {},
            "verification": dict(rerun_ctx),
            "executed": True,
        }
    return None


def _recent_executed_github_rerun_lifecycle(*, session_id: str) -> dict[str, Any] | None:
    from aethos_core.post_mutation_verification.verification_context_discovery import list_discovered_recent_mutations

    for state in list_discovered_recent_mutations(session_id=session_id, limit=8):
        if str(getattr(state, "provider", "") or "") != "github":
            continue
        if str(getattr(state, "operation", "") or "") != "workflow_rerun":
            continue
        params = dict(getattr(state, "params", {}) or {})
        exec_artifact = dict(params.get("mutation_execution") or {})
        if not exec_artifact.get("executed"):
            continue
        provider_result = dict(exec_artifact.get("provider_result") or {})
        verification = dict(params.get("verification_artifact") or {})
        evidence = dict(verification.get("evidence") or {})
        target_name = getattr(state, "service", None) or params.get("target_name")
        valid, _ = assert_valid_repo_context(str(target_name or provider_result.get("repository") or ""))
        if not valid:
            continue
        return {
            "target_name": target_name,
            "provider_result": provider_result,
            "verification": {**evidence, **params},
            "executed": True,
        }
    return None
