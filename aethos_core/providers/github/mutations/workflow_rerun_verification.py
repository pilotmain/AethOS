# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow rerun verification and correlation updates."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.mutations.post_rerun_evidence_refresh import (
    refresh_downstream_evidence_after_rerun,
)
from aethos_core.providers.github.mutations.workflow_rerun_outcome import (
    analyze_rerun_deployment_chain,
    chain_verification_result,
    compose_chain_summary,
)
from aethos_core.verification.github.workflow_rerun import verify_github_workflow_rerun


def verify_workflow_rerun(
    token: str,
    *,
    repository: str,
    source_run_id: str | int | None,
    workflow_id: str | int | None = None,
    source_created_at: Any = None,
    source_run_number: int | None = None,
    max_attempts: int = 5,
    session_id: str = "default",
) -> dict[str, Any]:
    result = verify_github_workflow_rerun(
        token,
        repository=repository,
        source_run_id=source_run_id,
        workflow_id=workflow_id,
        source_created_at=source_created_at,
        source_run_number=source_run_number,
        max_attempts=max_attempts,
    )
    if not result.get("new_run_detected"):
        return result
    refresh = refresh_downstream_evidence_after_rerun(
        session_id=session_id,
        repository=repository,
        verification=result,
    )
    deployment_chain = dict(refresh.get("deployment_chain") or {})
    if not deployment_chain:
        deployment_chain = analyze_rerun_deployment_chain(
            session_id=session_id,
            rerun_outcome=str(result.get("rerun_outcome") or "pending"),
        )
    result["evidence_refreshed"] = bool(refresh.get("evidence_refreshed"))
    result["chain_verdict"] = refresh.get("chain_verdict")
    result["timeline"] = refresh.get("timeline") or []
    result["deployment_chain"] = deployment_chain
    result["verification_result"] = chain_verification_result(
        rerun_outcome=str(result.get("rerun_outcome") or "pending"),
        deployment_chain=deployment_chain,
    )
    result["chain_summary"] = compose_chain_summary(
        rerun_outcome=str(result.get("rerun_outcome") or "pending"),
        deployment_chain=deployment_chain,
    )
    result["proactive_verification_reply"] = compose_proactive_github_rerun_verification_reply(result)
    return result


def update_correlation_after_rerun_verification(
    *,
    session_id: str,
    repository: str,
    verification: dict[str, Any],
) -> dict[str, Any]:
    from aethos_core.cross_provider_correlation.evidence_publisher import ingest_github_live_evidence
    from aethos_core.providers.github.context.github_context_store import save_github_rerun_context

    conclusion = str(verification.get("run_conclusion") or "").lower()
    status = str(verification.get("run_status") or "").lower()
    rerun_outcome = str(verification.get("rerun_outcome") or "")
    if not rerun_outcome or rerun_outcome == "unknown":
        from aethos_core.providers.github.mutations.workflow_rerun_outcome import classify_rerun_outcome

        rerun_outcome = classify_rerun_outcome(
            new_run_detected=bool(verification.get("new_run_detected")),
            run_status=status,
            run_conclusion=conclusion,
        )
    deployment_chain = dict(verification.get("deployment_chain") or {})
    if not deployment_chain or not verification.get("evidence_refreshed"):
        refresh = refresh_downstream_evidence_after_rerun(
            session_id=session_id,
            repository=repository,
            verification=verification,
        )
        deployment_chain = dict(refresh.get("deployment_chain") or deployment_chain)
        verification = {
            **verification,
            "evidence_refreshed": refresh.get("evidence_refreshed"),
            "chain_verdict": refresh.get("chain_verdict"),
            "timeline": refresh.get("timeline") or [],
            "deployment_chain": deployment_chain,
            "chain_summary": refresh.get("chain_summary") or verification.get("chain_summary"),
        }
    elif not deployment_chain:
        deployment_chain = analyze_rerun_deployment_chain(session_id=session_id, rerun_outcome=rerun_outcome)

    gh_status = "failed" if rerun_outcome in {"failed_again", "cancelled"} else (
        "passed" if rerun_outcome == "passed" else "unknown"
    )
    if status in {"queued", "in_progress", "waiting", "requested", "pending"} or rerun_outcome == "pending":
        gh_status = "pending"

    run_record = {
        "id": verification.get("rerun_run_id") or verification.get("new_run_id"),
        "name": verification.get("workflow_name") or "workflow rerun",
        "run_number": verification.get("run_number"),
        "head_branch": verification.get("head_branch"),
        "head_sha": verification.get("head_sha"),
        "status": verification.get("run_status"),
        "conclusion": verification.get("run_conclusion"),
    }
    evidence = {
        "repository": repository,
        "branch": {"branch": verification.get("head_branch") or "main", "sha": verification.get("head_sha") or ""},
        "commits": {
            "commits": [
                {
                    "sha": verification.get("head_sha") or "",
                    "message": "workflow rerun",
                    "author": "github",
                }
            ]
        },
        "checks": {"ok": True, "failed_count": 1 if gh_status == "failed" else 0, "checks": []},
        "workflow_diagnostic": {
            "ok": True,
            "latest_failed_run": run_record if gh_status == "failed" else None,
        },
        "workflow_runs": {"ok": True, "runs": [run_record]},
        "workflow_jobs": {
            "ok": True,
            "failed_jobs": verification.get("failed_jobs") or [],
            "likely_failure_job": verification.get("likely_failure_job"),
            "likely_failure_step": verification.get("likely_failure_step"),
        },
    }
    correlation = ingest_github_live_evidence(session_id, evidence)
    save_github_rerun_context(
        session_id,
        {
            "rerun_target_repo": repository,
            "original_run_id": verification.get("source_run_id"),
            "rerun_run_id": verification.get("rerun_run_id") or verification.get("new_run_id"),
            "workflow_name": verification.get("workflow_name") or "workflow rerun",
            "branch": verification.get("head_branch"),
            "commit_sha": verification.get("head_sha"),
            "verification_status": gh_status,
            "rerun_outcome": rerun_outcome,
            "failure_boundary_after_rerun": deployment_chain.get("failure_boundary"),
            "likely_failure_job": verification.get("likely_failure_job"),
            "likely_failure_step": verification.get("likely_failure_step"),
            "chain_healthy": deployment_chain.get("chain_healthy"),
            "chain_verdict": verification.get("chain_verdict") or deployment_chain.get("chain_verdict"),
            "evidence_refreshed": bool(verification.get("evidence_refreshed")),
            "timeline": verification.get("timeline") or deployment_chain.get("timeline") or [],
            "deployment_chain": deployment_chain,
            "chain_summary": verification.get("chain_summary") or compose_chain_summary(
                rerun_outcome=rerun_outcome,
                deployment_chain=deployment_chain,
            ),
            "proactive_verification_reply": verification.get("proactive_verification_reply")
            or compose_proactive_github_rerun_verification_reply({**verification, "deployment_chain": deployment_chain}),
        },
    )
    return {
        "ok": True,
        "github_status": gh_status,
        "correlation": correlation,
        "deployment_chain": deployment_chain,
        "new_run_detected": bool(verification.get("new_run_detected")),
        "rerun_outcome": rerun_outcome,
        "proactive_verification_reply": verification.get("proactive_verification_reply")
        or compose_proactive_github_rerun_verification_reply({**verification, "deployment_chain": deployment_chain}),
    }


def compose_proactive_github_rerun_verification_reply(verification: dict[str, Any]) -> str:
    deployment_chain = dict(verification.get("deployment_chain") or {})
    rerun_outcome = str(verification.get("rerun_outcome") or "unknown")
    number = verification.get("run_number") or verification.get("rerun_run_id") or "—"
    lines = [
        f"GitHub workflow rerun verification for run #{number}:",
        f"- Workflow outcome: **{rerun_outcome}**",
    ]
    if verification.get("likely_failure_job"):
        step = verification.get("likely_failure_step") or "unknown step"
        lines.append(f"- Likely failure: `{verification['likely_failure_job']}` / `{step}`")
    chain_verdict = str(verification.get("chain_verdict") or deployment_chain.get("chain_verdict") or "")
    if chain_verdict:
        lines.append(f"- Chain verdict: **{chain_verdict}**")
    summary = verification.get("chain_summary") or compose_chain_summary(
        rerun_outcome=rerun_outcome,
        deployment_chain=deployment_chain,
    )
    if summary:
        lines.extend(["", summary])
    boundary = deployment_chain.get("failure_boundary")
    if boundary and boundary != "unknown":
        lines.append(f"- Failure boundary: **{boundary}**")
    poll_metadata = dict(deployment_chain.get("poll_metadata") or {})
    if poll_metadata.get("polled"):
        lines.append(
            f"- Downstream wait: {poll_metadata.get('poll_attempt_count', 0)} poll attempt(s) over "
            f"{poll_metadata.get('waited_seconds', poll_metadata.get('deploy_poll_seconds', 0))}s."
        )
    elif deployment_chain.get("evidence_refreshed") or verification.get("evidence_refreshed"):
        lines.append("- Downstream evidence refreshed from Vercel/Railway.")
    timeline = list(verification.get("timeline") or deployment_chain.get("timeline") or [])
    if timeline:
        lines.append("")
        lines.append("**Timeline:**")
        for event in timeline[:6]:
            lines.append(f"- {event.get('phase')}: **{event.get('status')}** — {event.get('detail')}")
    return "\n".join(lines)


def summarize_verification_for_operator(verification: dict[str, Any]) -> str:
    deployment_chain = dict(verification.get("deployment_chain") or {})
    if verification.get("new_run_detected") and (
        verification.get("chain_verdict")
        or deployment_chain.get("chain_verdict")
        or deployment_chain.get("evidence_refreshed")
        or deployment_chain.get("poll_metadata")
    ):
        return compose_proactive_github_rerun_verification_reply(verification)
    if verification.get("chain_summary"):
        return str(verification["chain_summary"])
    rerun_outcome = str(verification.get("rerun_outcome") or "")
    deployment_chain = dict(verification.get("deployment_chain") or {})
    if deployment_chain:
        return compose_chain_summary(rerun_outcome=rerun_outcome, deployment_chain=deployment_chain)
    if not verification.get("new_run_detected"):
        return "No new workflow run was detected after the governed rerun yet."
    number = verification.get("run_number") or "—"
    if verification.get("likely_failure_job"):
        step = verification.get("likely_failure_step") or "unknown step"
        return (
            f"Workflow rerun **failed** on run #{number} — "
            f"likely failure in `{verification['likely_failure_job']}` / `{step}`."
        )
    conclusion = str(verification.get("run_conclusion") or verification.get("verification_result") or "unknown")
    status = str(verification.get("run_status") or "unknown")
    if conclusion == "success" or verification.get("verification_result") == "healthy":
        return f"Workflow rerun **passed** on run #{number}."
    if status in {"queued", "in_progress", "waiting", "requested", "pending"}:
        return f"Workflow rerun is **still running** (run #{number})."
    return f"Workflow rerun **failed** on run #{number} — inspect failed jobs/logs."
