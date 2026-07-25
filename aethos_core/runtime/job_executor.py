# SPDX-License-Identifier: Apache-2.0
"""Single-thread job worker — one queued job at a time."""

from __future__ import annotations

import logging
import queue
import threading
import traceback
from time import time
from typing import Any

from aethos_core.config import get_settings
from aethos_core.operations.orchestration.inventory_dispatch import uses_registry_inventory
from aethos_core.runtime.external_jobs import progress_message_for_external, run_external_health_job
from aethos_core.runtime.job_types import (
    uses_agent_coordination,
    uses_browser_evidence,
    uses_external,
    uses_mutation_execution,
    uses_mutation_preflight,
    uses_operation_preflight,
    uses_provider,
    uses_provider_e2e_orchestration,
    uses_readonly_execution,
    uses_supabase_env_completion,
)
from aethos_core.runtime.provider_job_runner import (
    ProviderJobFailure,
    ProviderJobTimeoutError,
    progress_message_for,
    run_provider_job,
)


_log = logging.getLogger(__name__)


class JobExecutor:
    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._busy = False

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="aethos-job-executor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def drain_queue_for_tests(self) -> None:
        """Clear pending ids and stop background thread (pytest isolation)."""
        self.stop()
        while True:
            try:
                self._queue.get_nowait()
                self._queue.task_done()
            except queue.Empty:
                break

    def enqueue(self, job_id: str) -> None:
        self._queue.put(job_id)

    def drain_once_for_tests(self) -> bool:
        """Process at most one queued job synchronously (tests)."""
        try:
            job_id = self._queue.get_nowait()
        except queue.Empty:
            return False
        self._execute_one_scoped(job_id)
        self._queue.task_done()
        return True

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                job_id = self._queue.get(timeout=0.4)
            except queue.Empty:
                continue
            if self._busy:
                self._queue.put(job_id)
                continue
            self._busy = True
            try:
                self._execute_one_scoped(job_id)
            finally:
                self._busy = False
                self._queue.task_done()

    def _execute_one_scoped(self, job_id: str) -> None:
        """Re-enter the job's stamped tenant scope before executing.

        Jobs run on a detached worker thread that does NOT inherit the request/chat
        ContextVars, so owner-scoped credentials (Vercel/Railway/etc.) won't resolve and
        read-only provider diagnostics fall back to the (uninstalled) browser path. Jobs
        stamp tenant_id at creation (jobs.py); restore it here so API-first execution works.
        """
        from aethos_core.runtime.jobs import job_store

        job = job_store.get(job_id)
        tenant_id = str((job.params or {}).get("tenant_id") or "").strip() if job else ""
        if tenant_id:
            from aethos_core.tenancy import tenant_scope

            with tenant_scope(tenant_id):
                self._execute_one(job_id)
        else:
            self._execute_one(job_id)

    def _execute_one(self, job_id: str) -> None:
        from aethos_core.runtime.jobs import job_store

        job = job_store.get(job_id)
        if not job or job.status.value != "queued":
            return

        settings = get_settings()
        max_runtime = float(settings.job_max_runtime_sec)
        provider_timeout = float(settings.job_provider_timeout_sec)
        started = time()

        job_store.begin_running(job_id)
        job = job_store.get(job_id)
        if not job:
            return

        if uses_mutation_preflight(job.job_type):
            job_store.emit_progress(job_id, "Running mutation preflight (design-only)…")
            try:
                if time() - started > max_runtime:
                    raise TimeoutError("Job exceeded maximum runtime.")
                from aethos_core.operations.mutations.preflight import run_mutation_preflight

                preflight_params = dict(job.params or {})
                preflight_params.setdefault("session_id", str(job.session_id or "default"))
                outcome = run_mutation_preflight(job_type=job.job_type, params=preflight_params)
                job = job_store.get(job_id)
                if job:
                    job.params["mutation_preflight"] = outcome.to_dict()
                    job.params["mutation_execution_enabled"] = outcome.mutation_execution_enabled
                    job.params["preflight_status"] = outcome.preflight_status
                    job.params["risk_tier"] = outcome.risk_tier.value
                    job.params["blast_radius"] = outcome.blast_radius
                    job.params["rollback_plan"] = outcome.rollback_plan
                    job.params["target_resolved"] = outcome.target_resolved
                    if outcome.target:
                        job.params["target"] = outcome.target
                    if outcome.target_name and not job.params.get("target_name"):
                        job.params["target_name"] = outcome.target_name
                    is_no_action = outcome.preflight_status == "no_action_available"
                    job.params["read_only"] = is_no_action
                    job.params["mutating"] = not is_no_action
                    job.params["execution_blocked"] = outcome.preflight_status != "ready_for_mutation_approval"
                    job.params["is_current"] = True
                    from aethos_core.jobs.job_approval_guidance import (
                        build_mutation_approval_metadata,
                        build_no_action_preflight_metadata,
                    )

                    if is_no_action:
                        job.params.update(
                            build_no_action_preflight_metadata(
                                reason="no failed workflow run found",
                            )
                        )
                    else:
                        job.params.update(build_mutation_approval_metadata(preflight_status=outcome.preflight_status))
                    if outcome.workflow_resolution:
                        job.params["workflow_resolution"] = outcome.workflow_resolution
                    if outcome.workflow_resolution_debug:
                        job.params["workflow_resolution_debug"] = outcome.workflow_resolution_debug
                    workflow_discovery = None
                    if isinstance(outcome.workflow_resolution_debug, dict):
                        workflow_discovery = outcome.workflow_resolution_debug.get("workflow_discovery")
                    if isinstance(outcome.workflow_resolution, dict) and not workflow_discovery:
                        workflow_discovery = outcome.workflow_resolution.get("workflow_discovery")
                    if workflow_discovery:
                        job.params["workflow_discovery"] = workflow_discovery
                    if outcome.discovery_failure_reason:
                        job.params["discovery_failure_reason"] = outcome.discovery_failure_reason
                    if outcome.credential_guidance:
                        job.params["credential_guidance"] = outcome.credential_guidance
                    if outcome.credential_requirements_reply:
                        job.params["credential_requirements_reply"] = outcome.credential_requirements_reply
                    if (
                        outcome.provider == "github"
                        and outcome.operation_type == "workflow_rerun"
                    ):
                        from aethos_core.providers.github.context.github_context_store import save_github_rerun_context

                        workflow_resolution = dict(outcome.workflow_resolution or {})
                        workflow_discovery = workflow_resolution.get("workflow_discovery")
                        if not workflow_discovery and isinstance(outcome.workflow_resolution_debug, dict):
                            workflow_discovery = outcome.workflow_resolution_debug.get("workflow_discovery")
                        if not workflow_discovery:
                            workflow_discovery = job.params.get("workflow_discovery")
                        rerun_context = {
                            "rerun_target_repo": outcome.target_name or workflow_resolution.get("repository"),
                            "original_run_id": workflow_resolution.get("source_run_id"),
                            "workflow_name": workflow_resolution.get("workflow_name"),
                            "branch": workflow_resolution.get("head_branch"),
                            "commit_sha": workflow_resolution.get("head_sha"),
                            "preflight_job_id": job_id,
                            "verification_status": outcome.preflight_status,
                            "discovery_failure_reason": outcome.discovery_failure_reason
                            or workflow_resolution.get("discovery_failure_reason"),
                        }
                        if workflow_discovery:
                            rerun_context["workflow_discovery"] = workflow_discovery
                        save_github_rerun_context(str(job.session_id or "default"), rerun_context)
                from aethos_core.operations.mutations.preflight_supersede import (
                    supersede_previous_mutation_preflights,
                )

                supersede_previous_mutation_preflights(new_job_id=job_id)
                job_store.complete_with_result(
                    job_id,
                    full_result=outcome.full_result,
                    summary=outcome.summary,
                    preview=outcome.summary[:240],
                    provider="mutation_preflight",
                    model="deterministic",
                    used_llm=False,
                    fallback=False,
                )
                completed_pf = job_store.get(job_id)
                if completed_pf:
                    from aethos_core.operation_lifecycle.operation_state_store import upsert_operation_state_from_job

                    state = upsert_operation_state_from_job(completed_pf)
                    if state:
                        completed_pf.params["operation_lifecycle"] = state.to_dict()
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
        elif uses_provider_e2e_orchestration(job.job_type):
            job_store.emit_progress(job_id, "Running provider E2E orchestration…")
            try:
                from aethos_core.provider_e2e_orchestration.executor import run_provider_e2e_orchestration

                outcome = run_provider_e2e_orchestration(job_id=job_id, params=dict(job.params or {}))
                job = job_store.get(job_id)
                if job:
                    job.params.update(outcome.artifact)
                    job.params["read_only"] = not outcome.executed
                    job.params["mutating"] = outcome.executed
                    job.params["executed"] = outcome.executed
                job_ref = job_store.get(job_id)
                provider_name = str((job_ref.params or {}).get("provider", "provider_e2e")) if job_ref else "provider_e2e"
                if outcome.executed and not outcome.blocked:
                    job_store.complete_with_result(
                        job_id,
                        full_result=outcome.full_result,
                        summary=outcome.summary,
                        preview=outcome.summary[:240],
                        provider=provider_name,
                        model="deterministic",
                        used_llm=False,
                        fallback=False,
                    )
                else:
                    job_store.fail_job(
                        job_id,
                        outcome.summary or "Provider E2E orchestration did not complete successfully.",
                        failure={
                            "execution_status": (outcome.artifact or {}).get("execution_status"),
                            "blocked": outcome.blocked,
                            "failure_state": (outcome.artifact or {}).get("failure_state"),
                        },
                    )
                    if job_ref:
                        job_ref.full_result = outcome.full_result
                        job_ref.result = outcome.full_result
                        job_ref.result_summary = outcome.summary
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
        elif uses_supabase_env_completion(job.job_type):
            job_store.emit_progress(job_id, "Running Supabase env completion…")
            try:
                from aethos_core.provider_e2e_orchestration.env_completion.supabase_executor import (
                    run_supabase_env_completion,
                )

                outcome = run_supabase_env_completion(job_id=job_id, params=dict(job.params or {}))
                job = job_store.get(job_id)
                if job:
                    job.params.update(outcome.artifact)
                    job.params["read_only"] = not outcome.executed
                    job.params["mutating"] = outcome.executed
                    job.params["executed"] = outcome.executed
                job_ref = job_store.get(job_id)
                provider_name = str((job_ref.params or {}).get("provider", "vercel")) if job_ref else "vercel"
                job_store.complete_with_result(
                    job_id,
                    full_result=outcome.full_result,
                    summary=outcome.summary,
                    preview=outcome.summary[:240],
                    provider=provider_name,
                    model="deterministic",
                    used_llm=False,
                    fallback=False,
                )
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
        elif uses_mutation_execution(job.job_type):
            job_store.emit_progress(job_id, "Running governed mutation execution…")
            try:
                from aethos_core.operations.mutations.execution import run_mutation_execution
                from aethos_core.operations.mutations.lifecycle import (
                    EXECUTION_STABILIZING,
                    LIFECYCLE_VERIFICATION_RUNNING,
                    verification_state_after_enqueue,
                )
                from aethos_core.operations.mutations.lifecycle_authority import sync_mutation_job_lifecycle

                job.params["mutation_execution_job_id"] = job_id
                outcome = run_mutation_execution(params=job.params, job_id=job_id)
                job = job_store.get(job_id)
                summary = outcome.summary
                if job:
                    job.params["mutation_execution"] = outcome.artifact
                    job.params["dry_run"] = outcome.dry_run
                    job.params["mutating"] = outcome.executed
                    job.params["executed"] = outcome.executed
                    job.params["provider_mutation_requested"] = outcome.artifact.get("provider_mutation_requested")
                    job.params["verified"] = False
                    job.params["execution_state"] = outcome.artifact.get("execution_state")
                    job.params["lifecycle_state"] = outcome.artifact.get("lifecycle_state")
                    if outcome.executed:
                        job.params["verification_state"] = (
                            job.params.get("verification_state") or verification_state_after_enqueue()
                        )
                        if job.params.get("verification_job_id"):
                            job.params["lifecycle_state"] = LIFECYCLE_VERIFICATION_RUNNING
                            job.params["execution_state"] = EXECUTION_STABILIZING
                    job.params["audit"] = outcome.artifact.get("audit")
                    if outcome.artifact.get("provider_evidence_bundle"):
                        job.params["provider_evidence_bundle"] = outcome.artifact["provider_evidence_bundle"]
                    if outcome.artifact.get("command"):
                        job.params["command"] = outcome.artifact["command"]
                    if outcome.artifact.get("execution_mode"):
                        job.params["execution_mode"] = outcome.artifact["execution_mode"]
                    if outcome.artifact.get("restart_command_submitted") is not None:
                        job.params["restart_command_submitted"] = outcome.artifact.get("restart_command_submitted")
                    sync_mutation_job_lifecycle(job)
                    summary = str(job.params.get("lifecycle_summary") or summary)
                    from aethos_core.operation_lifecycle.operation_state_store import upsert_operation_state_from_job

                    state = upsert_operation_state_from_job(job)
                    if state:
                        job.params["operation_lifecycle"] = state.to_dict()
                    from aethos_core.operational_thread_memory.failure_reason_extractor import extract_failure_reason
                    from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job
                    from aethos_core.provider_topology.failure_truth_expander import expand_failure_truth

                    failure = expand_failure_truth(job) or extract_failure_reason(job)
                    if failure:
                        job.params["failure_reason"] = failure
                        job.params["failure_truth"] = failure
                    sync_thread_from_execution_job(job=job)
                    if failure and job.params.get("provider") == "railway":
                        target = dict(job.params.get("target") or {})
                        from aethos_core.provider_topology.topology_refresh import refresh_topology_on_failure

                        refresh_topology_on_failure(
                            provider="railway",
                            project=str(target.get("project_name") or job.params.get("project_name") or ""),
                            environment=str(target.get("environment") or "production"),
                            service_name=str(job.params.get("target_name") or ""),
                            failure_reason=str(failure.get("failure_reason") or ""),
                        )
                job_store.complete_with_result(
                    job_id,
                    full_result=outcome.full_result,
                    summary=summary,
                    preview=summary[:240],
                    provider="mutation_execution",
                    model="deterministic",
                    used_llm=False,
                    fallback=False,
                )
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
                job = job_store.get(job_id)
                if job and uses_mutation_execution(job.job_type):
                    from aethos_core.operational_thread_memory.failure_reason_extractor import extract_failure_reason
                    from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_execution_job
                    from aethos_core.provider_topology.failure_truth_expander import expand_failure_truth

                    job.params["execution_state"] = job.params.get("execution_state") or "execution_failed"
                    job.params["executed"] = False
                    job.params["error"] = str(exc)
                    failure = expand_failure_truth(job) or extract_failure_reason(job)
                    if failure:
                        job.params["failure_reason"] = failure
                        job.params["failure_truth"] = failure
                    sync_thread_from_execution_job(job=job)
        elif uses_operation_preflight(job.job_type):
            job_store.emit_progress(job_id, "Running read-only operation preflight…")
            try:
                if time() - started > max_runtime:
                    raise TimeoutError("Job exceeded maximum runtime.")
                from aethos_core.operations.preflight import run_operation_preflight

                outcome = run_operation_preflight(job_type=job.job_type, params=job.params)
                job = job_store.get(job_id)
                if job:
                    job.params["operation_preflight"] = outcome.preflight.to_dict()
                    job.params["execution_enabled"] = outcome.preflight.execution_enabled
                    job.params["read_only_execution_enabled"] = outcome.preflight.read_only_execution_enabled
                    job.params["mutation_execution_enabled"] = outcome.preflight.mutation_execution_enabled
                    job.params["phase"] = outcome.preflight.phase
                    job.params["preflight_status"] = outcome.preflight.preflight_status
                    job.params["provider_used"] = "none"
                    job.params["read_only"] = True
                    job.params["is_current"] = True
                from aethos_core.operations.preflight_supersede import supersede_previous_preflights

                supersede_previous_preflights(new_job_id=job_id)
                job_store.complete_with_result(
                    job_id,
                    full_result=outcome.full_result,
                    summary=outcome.summary,
                    preview=outcome.preview,
                    provider="preflight",
                    model="deterministic",
                    used_llm=False,
                    fallback=False,
                )
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
        elif uses_readonly_execution(job.job_type):
            from aethos_core.connections.adapters import auth_method_label, auth_source_phrase
            from aethos_core.operations.execution.execution_progress import emit_step, progress_emitter
            from aethos_core.operations.execution.execution_step_timeouts import (
                ExecutionStepTimeoutError,
                run_with_timeout,
            )

            auth_method = str(job.params.get("auth_method") or "none")
            target = str(job.params.get("target_name") or "")
            op = str(job.params.get("operation_type") or "execution").replace("_", " ")
            progress_fn = progress_emitter(job_id)
            emit_step(progress_fn, "Resolving auth")
            progress = (
                f"Checking {op} for `{target}` using your {auth_source_phrase(auth_method)}…"
                if target
                else "Running approved read-only execution…"
            )
            job_store.emit_progress(job_id, progress)
            readonly_timeout = float(get_settings().readonly_execution_timeout_sec)
            try:
                _log.info("readonly_execution_job_start job_id=%s op=%s target=%s", job_id, op, target)

                def _run() -> Any:
                    from aethos_core.operations.execution.execution_runner import run_readonly_execution

                    return run_readonly_execution(
                        job_type=job.job_type,
                        params=job.params,
                        job_id=job_id,
                    )

                outcome = run_with_timeout(_run, timeout_sec=readonly_timeout, step="readonly_execution")
                job = job_store.get(job_id)
                if job:
                    job.params["readonly_execution"] = outcome.artifact.to_dict()
                    job.params["execution_timeline"] = outcome.artifact.timeline
                    job.params["read_only"] = True
                    job.params["mutating"] = False
                    job.params["auth_method"] = outcome.artifact.auth_method or job.params.get("auth_method")
                    job.params["auth_method_label"] = outcome.artifact.auth_method_label or auth_method_label(
                        str(job.params.get("auth_method") or "")
                    )
                    job.params["data_source"] = outcome.artifact.data_source
                    job.params["browser_used"] = outcome.artifact.data_source == "browser_fallback"
                emit_step(progress_fn, "Completing execution")
                job_store.complete_with_result(
                    job_id,
                    full_result=outcome.full_result,
                    summary=outcome.summary,
                    preview=outcome.preview,
                    provider="readonly_execution",
                    model="sandbox",
                    used_llm=False,
                    fallback=False,
                )
                job = job_store.get(job_id)
                if job and job.params.get("verification_of_mutation_job_id"):
                    from aethos_core.verification.orchestration.resolve import resolve_mutation_verification

                    resolve_mutation_verification(verification_job_id=job_id)
                _log.info("readonly_execution_job_complete job_id=%s", job_id)
            except ExecutionStepTimeoutError:
                job = job_store.get(job_id)
                if job:
                    job.params["status_reason"] = "execution_timed_out"
                job_store.fail_job(
                    job_id,
                    "Read-only execution timed out before completion.",
                    failure={"status_reason": "execution_timed_out"},
                )
                _log.warning("readonly_execution_job_timeout job_id=%s", job_id)
            except Exception as exc:
                reason = str(exc)
                if isinstance(exc, TimeoutError):
                    reason = "execution_timed_out"
                job = job_store.get(job_id)
                if job and reason == "execution_timed_out":
                    job.params["status_reason"] = "execution_timed_out"
                job_store.fail_job(
                    job_id,
                    "Read-only execution timed out before completion."
                    if reason == "execution_timed_out"
                    else reason,
                    failure={"status_reason": reason} if reason == "execution_timed_out" else None,
                )
                _log.exception("readonly_execution_job_failed job_id=%s", job_id)
        elif uses_browser_evidence(job.job_type):
            job_store.emit_progress(job_id, "Running governed browser evidence capture…")
            try:
                if time() - started > max_runtime:
                    raise TimeoutError("Job exceeded maximum runtime.")
                from aethos_core.browser.runtime.browser_evidence_execution import execute_browser_evidence_job

                outcome = execute_browser_evidence_job(job)
                job = job_store.get(job_id)
                if job:
                    job.params["browser_evidence"] = outcome.get("browser_evidence")
                    job.params["read_only"] = True
                    job.params["mutating"] = False
                job_store.complete_with_result(
                    job_id,
                    full_result=str(outcome.get("full_result") or outcome.get("summary") or ""),
                    summary=str(outcome.get("summary") or "Browser evidence job complete."),
                    preview=str(outcome.get("summary") or "")[:240],
                    provider="browser_evidence",
                    model="deterministic",
                    used_llm=False,
                    fallback=False,
                )
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
        elif uses_registry_inventory(job.job_type):
            try:
                from aethos_core.operations.orchestration.inventory_dispatch import execute_inventory_job

                execute_inventory_job(job_id=job_id, job=job, started=started, max_runtime=max_runtime)
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
        elif uses_external(job.job_type):
            job_store.emit_progress(job_id, progress_message_for_external(job))
            try:
                if time() - started > max_runtime:
                    raise TimeoutError("Job exceeded maximum runtime.")
                outcome = run_external_health_job(job)
                if outcome.sources is not None:
                    job = job_store.get(job_id)
                    if job:
                        job.params["sources"] = outcome.sources
                        job.params["tool_used"] = outcome.tool_used
                        job.params["external_mode"] = outcome.mode
                job_store.complete_with_result(
                    job_id,
                    full_result=outcome.full_result,
                    summary=outcome.summary,
                    preview=outcome.preview,
                    provider=outcome.provider,
                    model=outcome.model,
                    used_llm=outcome.used_llm,
                    fallback=outcome.fallback,
                )
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
        elif uses_provider(job.job_type):
            job_store.emit_progress(job_id, progress_message_for(job))
            try:
                if time() - started > max_runtime:
                    raise ProviderJobTimeoutError("Job exceeded maximum runtime.")
                outcome = run_provider_job(job, timeout_sec=provider_timeout)
                if time() - started > max_runtime:
                    raise ProviderJobTimeoutError("Job exceeded maximum runtime.")
                job_store.complete_with_result(
                    job_id,
                    full_result=outcome.full_result,
                    summary=outcome.summary,
                    preview=outcome.preview,
                    provider=outcome.provider,
                    model=outcome.model,
                    used_llm=outcome.used_llm,
                    fallback=outcome.fallback,
                )
            except ProviderJobTimeoutError as exc:
                job_store.fail_job(job_id, str(exc))
            except ProviderJobFailure as exc:
                job_store.fail_job(job_id, exc.message)
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
        elif uses_agent_coordination(job.job_type):
            job_store.emit_progress(job_id, "Running governed multi-agent coordination…")
            try:
                from aethos_core.agents.runtime.coordination import run_agent_coordination

                goal = str(job.params.get("goal") or job.title or "")
                session_id = str(job.params.get("session_id") or "default")
                outcome = run_agent_coordination(
                    goal=goal,
                    session_id=session_id,
                    workspace_hint=job.params.get("workspace_hint"),
                )
                summary = str((outcome.get("merged") or {}).get("status") or "coordination complete")
                job = job_store.get(job_id)
                if job:
                    job.params["agent_coordination"] = outcome
                    job.params["read_only"] = True
                    job.params["execution_enabled"] = False
                    job.params["mutation_execution_enabled"] = False
                job_store.complete_with_result(
                    job_id,
                    full_result=outcome.get("report") or "",
                    summary=f"Multi-agent coordination — {summary}",
                    preview=(outcome.get("report") or "")[:240],
                    provider="agent_coordination",
                    model="deterministic",
                    used_llm=False,
                    fallback=False,
                )
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))
        else:
            try:
                job_store.run_local_job(job_id)
            except Exception as exc:
                job_store.fail_job(job_id, str(exc))


job_executor = JobExecutor()
