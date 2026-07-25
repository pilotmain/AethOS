# SPDX-License-Identifier: Apache-2.0
"""Chat replies for mutation execution truth."""

from __future__ import annotations

import re

from aethos_core.mission_control.visible_navigation_registry import resolve_visible_navigation_path, INTERNAL_SURFACE_MUTATION_APPROVAL

_JOB_ID_RX = re.compile(r"\b((?:job|dj)-[a-f0-9]+)\b", re.I)
_EXEC_TRUTH_RX = re.compile(
    r"\b("
    r"did\s+the\s+restart\s+actually\s+happen"
    r"|did\s+the\s+mutation\s+actually\s+(?:run|execute|happen)"
    r"|did\s+you\s+stop\b"
    r"|did\s+the\s+(?:projects?|services?)\s+stop\b"
    r"|were\s+(?:the\s+)?(?:projects?|services?)\s+stopped\b"
    r"|what\s+happened\s+after\s+approval"
    r"|is\s+(?:job|dj)-[a-f0-9]+\s+done"
    r"|was\s+the\s+restart\s+(?:actually\s+)?(?:performed|executed)"
    r"|was\s+(?:the\s+)?stop\s+(?:actually\s+)?(?:performed|executed)"
    r")\b",
    re.I,
)


def is_mutation_execution_truth_intent(text: str) -> bool:
    return bool(_EXEC_TRUTH_RX.search(text or ""))


def _runtime_actions_path() -> str:
    return resolve_visible_navigation_path(internal_surface=INTERNAL_SURFACE_MUTATION_APPROVAL, mode="operator")


def _find_execution_job(*, text: str, session_id: str):
    from aethos_core.runtime.jobs import job_store

    job_id_match = _JOB_ID_RX.search(text)
    if job_id_match:
        job = job_store.get(job_id_match.group(1))
        if job and job.job_type == "mutation_execution":
            return job
        if job and job.job_type == "mutation_preflight":
            exec_id = job.params.get("mutation_execution_job_id")
            if exec_id:
                return job_store.get(str(exec_id))
    for row in reversed(job_store.list_all()):
        if row.job_type != "mutation_execution":
            continue
        if str(getattr(row, "session_id", "") or "") != session_id:
            continue
        return row
    return None


def _restart_verification_state(job) -> str:
    return str(
        job.params.get("restart_verification_state")
        or (job.params.get("verification_artifact") or {}).get("evidence", {}).get("restart_verification_state")
        or ""
    )


def compose_mutation_execution_truth_reply(text: str, *, session_id: str = "default") -> tuple[str, str, dict[str, str]] | None:
    if not is_mutation_execution_truth_intent(text):
        return None

    from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
        compose_rerun_no_execution_followup,
    )

    no_exec = compose_rerun_no_execution_followup(text, session_id=session_id)
    if no_exec is not None:
        return no_exec

    job = _find_execution_job(text=text, session_id=session_id)
    if job is None:
        return (
            "I couldn't find a governed mutation execution job in this session yet.\n\n"
            "If you just approved a restart, check **"
            f"{_runtime_actions_path()}** for the execution job state.",
            "mutation_execution_truth",
            {},
        )

    artifact = dict(job.params.get("mutation_execution") or {})
    provider = str(job.params.get("provider") or artifact.get("provider") or "provider")
    operation = str(job.params.get("operation_type") or artifact.get("operation_type") or "mutation")
    target = str(job.params.get("target_name") or artifact.get("target_name") or "unknown")
    exec_state = str(job.params.get("execution_state") or artifact.get("execution_state") or "")
    ver_state = str(job.params.get("verification_state") or artifact.get("verification_state") or "")
    provider_result = artifact.get("provider_result") or {}
    error = (
        artifact.get("error")
        or provider_result.get("detail")
        or (artifact.get("railway_mutation_result") or {}).get("error")
    )
    verified = bool(job.params.get("verified")) and ver_state == "verified"
    restart_state = _restart_verification_state(job)
    restart_command_submitted = job.params.get("restart_command_submitted")
    if restart_command_submitted is None:
        restart_command_submitted = artifact.get("restart_command_submitted")
    provider_requested = bool(
        restart_command_submitted is True
        or job.params.get("provider_mutation_requested")
        or artifact.get("provider_mutation_requested")
    )
    if provider == "github" and operation == "workflow_rerun":
        proactive = str(job.params.get("proactive_verification_reply") or job.params.get("chain_summary") or "")
        if proactive and ver_state in {"verified", "verification_completed", ""}:
            return (
                f"GitHub workflow rerun for **{target}** — verification summary:\n\n{proactive}\n\n"
                f"Execution job: `{job.id}`.",
                "mutation_execution_truth",
                {"job_id": job.id, "verification_state": ver_state or "completed"},
            )

    if job.params.get("executed") is False or exec_state == "execution_failed":
        reason = str(error or "provider mutation did not execute.")
        if "credential" in reason.lower():
            reason = "Railway mutation credentials are not configured."
        if operation == "stop":
            return (
                f"No — approval was recorded, but the **{provider} stop** for **{target}** did not execute because {reason}\n\n"
                "**No deployment was stopped.**\n\n"
                f"Review execution job `{job.id}` in **{_runtime_actions_path()}**.",
                "mutation_execution_truth",
                {"job_id": job.id, "execution_state": exec_state or "execution_failed", "operation": "stop"},
            )
        if provider == "railway" and restart_command_submitted is False:
            return (
                f"No — I cannot confirm Railway restarted **{target}**.\n\n"
                "The approval was recorded, but Railway did not show provider-side restart evidence.\n\n"
                f"Execution job: `{job.id}`. Review diagnostics in **{_runtime_actions_path()}**.",
                "mutation_execution_truth",
                {"job_id": job.id, "execution_state": exec_state or "execution_failed"},
            )
        return (
            f"No — approval was recorded, but the **{provider} {operation.replace('_', ' ')}** did not execute because {reason}\n\n"
            "**No provider mutation was performed.**\n\n"
            f"Review execution job `{job.id}` in **{_runtime_actions_path()}**.",
            "mutation_execution_truth",
            {"job_id": job.id, "execution_state": exec_state or "execution_failed"},
        )

    if provider == "railway" and restart_state in {"restart_transition_detected", "log_restart_detected"} and verified:
        proof = str(job.params.get("restart_transition_proof") or "deployment")
        bundle = job.params.get("provider_evidence_bundle") or {}
        if isinstance(bundle, dict) and bundle.get("verification", {}).get("status") == "verified_restart":
            return (
                f"Yes — Railway accepted the restart command for **{target}**, and provider evidence shows runtime activity "
                "after approval. The service is currently healthy. No new deployment was required because this was a restart, not a redeploy.\n\n"
                f"Execution job: `{job.id}`.",
                "mutation_execution_truth",
                {"job_id": job.id, "verification_state": ver_state, "restart_verification_state": restart_state},
            )
        if proof == "logs":
            return (
                f"Yes — Railway log activity after approval indicates **{target}** restarted, "
                "and the service is reachable again. Recovery verification is complete.\n\n"
                f"Execution job: `{job.id}`.",
                "mutation_execution_truth",
                {"job_id": job.id, "verification_state": ver_state, "restart_verification_state": restart_state},
            )
        return (
            f"Yes — Railway shows a new restart/deployment transition after approval for **{target}**, "
            "and the service is reachable again. Recovery verification is complete.\n\n"
            f"Execution job: `{job.id}`.",
            "mutation_execution_truth",
            {"job_id": job.id, "verification_state": ver_state, "restart_verification_state": restart_state},
        )

    if provider == "railway" and restart_command_submitted is False:
        return (
            f"No — I cannot confirm Railway restarted **{target}**.\n\n"
            "The approval was recorded, but Railway did not show provider-side restart evidence.\n\n"
            f"Execution job: `{job.id}`. Review diagnostics in **{_runtime_actions_path()}**.",
            "mutation_execution_truth",
            {"job_id": job.id, "restart_command_submitted": "false"},
        )

    if provider == "railway" and restart_state in {"restart_unverified", "service_online_but_restart_unproven"}:
        return (
            f"No — I cannot verify that Railway actually restarted **{target}**.\n\n"
            "Approval was recorded and execution was attempted, but Railway still shows the same active deployment "
            "from before approval. The service is online, but that only proves availability — not that a restart occurred.\n\n"
            "I'm treating the restart as **unverified** rather than confirmed.\n\n"
            f"Execution job: `{job.id}`. Review evidence in **{_runtime_actions_path()}**.",
            "mutation_execution_truth",
            {"job_id": job.id, "restart_verification_state": restart_state},
        )

    if provider == "railway" and verified and restart_state not in {"restart_transition_detected", "log_restart_detected"}:
        return (
            f"No — I cannot verify the restart actually happened for **{target}**.\n\n"
            "The service is online, but Railway still shows the same active deployment from before approval, "
            "so I'm treating the restart as unverified rather than confirmed.\n\n"
            f"Execution job: `{job.id}`.",
            "mutation_execution_truth",
            {"job_id": job.id, "verification_state": ver_state},
        )

    if provider == "railway" and restart_command_submitted is True and restart_state in {"stabilizing", "restart_requested"}:
        return (
            f"Railway accepted the restart command for **{target}**, but I have not yet observed provider-side evidence "
            "that the service restarted. I'm treating this as unverified until logs or runtime activity confirm it.\n\n"
            f"Execution job: `{job.id}`. Review evidence in **{_runtime_actions_path()}**.",
            "mutation_execution_truth",
            {"job_id": job.id, "restart_command_submitted": "true"},
        )

    if provider == "railway" and restart_state in {"stabilizing", "restart_requested"}:
        return (
            f"Railway accepted the restart request for **{target}**, but I have not observed a new deployment/restart "
            "transition yet. I'm treating this as stabilizing, not verified.\n\n"
            f"Execution job: `{job.id}`. Review status in **{_runtime_actions_path()}**.",
            "mutation_execution_truth",
            {"job_id": job.id, "execution_state": exec_state or "stabilizing"},
        )

    if operation == "stop" and job.params.get("executed") is True:
        return (
            f"Yes — the **{provider} stop** for **{target}** was submitted after approval.\n\n"
            f"Execution job: `{job.id}`. Use **restart** or **redeploy** to bring the deployment back.",
            "mutation_execution_truth",
            {"job_id": job.id, "operation": "stop", "executed": "true"},
        )

    if verified:
        if provider == "github" and operation == "workflow_rerun":
            proactive = str(job.params.get("proactive_verification_reply") or job.params.get("chain_summary") or "")
            if proactive:
                return (
                    f"Yes — the **GitHub workflow rerun** for **{target}** completed.\n\n{proactive}\n\n"
                    f"Execution job: `{job.id}`.",
                    "mutation_execution_truth",
                    {"job_id": job.id, "verification_state": ver_state},
                )
        return (
            f"Yes — the **{provider} {operation.replace('_', ' ')}** for **{target}** completed and verification succeeded.\n\n"
            f"Execution job: `{job.id}`.",
            "mutation_execution_truth",
            {"job_id": job.id, "verification_state": ver_state},
        )

    if provider_requested or exec_state in {"provider_mutation_requested", "stabilizing"}:
        if restart_command_submitted is True:
            if ver_state in {"verification_pending", "verification_running"} or job.params.get("verification_job_id"):
                return (
                    f"Railway restart command was submitted for **{target}**. Runtime recovery verification is still in progress.\n\n"
                    f"Execution job: `{job.id}`. Review status in **{_runtime_actions_path()}**.",
                    "mutation_execution_truth",
                    {"job_id": job.id, "execution_state": exec_state or "stabilizing"},
                )
            return (
                f"Railway restart command was submitted for **{target}**. Verification is now monitoring runtime recovery.\n\n"
                f"Execution job: `{job.id}`.",
                "mutation_execution_truth",
                {"job_id": job.id, "execution_state": exec_state or "provider_mutation_requested"},
            )
        if ver_state in {"verification_pending", "verification_running"} or job.params.get("verification_job_id"):
            return (
                f"Railway accepted the restart request for **{target}**. Runtime recovery verification is still in progress.\n\n"
                f"Execution job: `{job.id}`. Review status in **{_runtime_actions_path()}**.",
                "mutation_execution_truth",
                {"job_id": job.id, "execution_state": exec_state or "stabilizing"},
            )
        return (
            f"Railway accepted the restart request for **{target}**. Verification is now monitoring runtime recovery.\n\n"
            f"Execution job: `{job.id}`.",
            "mutation_execution_truth",
            {"job_id": job.id, "execution_state": exec_state or "provider_mutation_requested"},
        )

    if job.status.value == "queued":
        return (
            f"Approval was recorded and execution job `{job.id}` is queued, but the provider mutation has not run yet.\n\n"
            f"Check **{_runtime_actions_path()}** for live execution state.",
            "mutation_execution_truth",
            {"job_id": job.id, "status": job.status.value},
        )

    return (
        f"I found execution job `{job.id}` for **{target}**, but provider execution truth is still inconclusive.\n\n"
        f"Current state: `{exec_state or job.status.value}`. Review **{_runtime_actions_path()}**.",
        "mutation_execution_truth",
        {"job_id": job.id},
    )
