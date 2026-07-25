# SPDX-License-Identifier: Apache-2.0
"""Registry-backed inventory job dispatch — Phase 9.3M Slice E."""

from __future__ import annotations

import logging
import threading
import traceback
from time import time
from typing import Any

from aethos_core.connections.auth_labels import auth_method_label, auth_method_label_for_provider
from aethos_core.connections.adapters import (
    github_inspection_progress_message,
    railway_inspection_progress_message,
    vercel_inspection_progress_message,
)
from aethos_core.providers.base.provider_registry import ProviderRegistry

_log = logging.getLogger(__name__)

# Inventory tier = direct readonly · no approval.
INVENTORY_JOB_PROVIDER: dict[str, str] = {
    "railway_services_inventory": "railway",
    "github_repositories_inventory": "github",
    "vercel_projects_inventory": "vercel",
    "vercel_service_health_summary": "vercel",
    "vercel_deployment_status_summary": "vercel",
}


def provider_for_inventory_job(job_type: str) -> str | None:
    return INVENTORY_JOB_PROVIDER.get(job_type)


def uses_registry_inventory(job_type: str) -> bool:
    return job_type in INVENTORY_JOB_PROVIDER


def resolve_inventory_adapter(provider: str) -> Any | None:
    spec = ProviderRegistry.get(provider)
    if not spec or not spec.inventory_adapter_factory:
        return None
    return spec.inventory_adapter_factory()


def inventory_progress_message(provider: str, auth_method: str) -> str:
    if provider == "railway":
        return railway_inspection_progress_message(auth_method)
    if provider == "github":
        return github_inspection_progress_message(auth_method)
    return vercel_inspection_progress_message(auth_method)


def execute_inventory_job(
    *,
    job_id: str,
    job: Any,
    started: float,
    max_runtime: float,
) -> None:
    """Run a provider inventory job via registry dispatch."""
    from aethos_core.runtime.jobs import job_store

    provider = provider_for_inventory_job(job.job_type)
    if not provider:
        raise ValueError(f"No inventory provider for job type: {job.job_type}")

    auth_method = str(job.params.get("auth_method") or ("api_token" if provider != "vercel" else "browser"))
    job_store.emit_progress(job_id, inventory_progress_message(provider, auth_method))

    if time() - started > max_runtime:
        raise TimeoutError("Job exceeded maximum runtime.")

    if provider == "vercel":
        _execute_vercel_inventory_job(job_id=job_id, job=job, started=started, max_runtime=max_runtime)
        return

    _execute_api_inventory_job(
        job_id=job_id,
        job=job,
        provider=provider,
        auth_method=auth_method,
    )


def _execute_api_inventory_job(
    *,
    job_id: str,
    job: Any,
    provider: str,
    auth_method: str,
) -> None:
    from aethos_core.runtime.jobs import job_store

    credential_id = str(job.params.get("credential_id") or "")
    user_request = str(job.params.get("user_request") or "")

    if provider == "railway":
        from aethos_core.runtime.railway_readonly_inspector import (
            RailwayInventoryError,
            run_railway_services_inventory,
        )

        run_fn = run_railway_services_inventory
        error_cls = RailwayInventoryError
        inventory_key = "railway_inventory"
        count_key = "service_count"
        api_provider = "railway_api"
        api_model = "graphql"
    else:
        from aethos_core.runtime.github_readonly_inspector import (
            GitHubInventoryError,
            run_github_repositories_inventory,
        )

        run_fn = run_github_repositories_inventory
        error_cls = GitHubInventoryError
        inventory_key = "github_inventory"
        count_key = "repository_count"
        api_provider = "github_api"
        api_model = "rest"

    try:
        outcome = run_fn(credential_id=credential_id, user_request=user_request)
        job = job_store.get(job_id)
        if job:
            job.params[inventory_key] = {"items": outcome.items, "count": len(outcome.items)}
            job.params["evidence"] = outcome.evidence
            job.params["provider"] = provider
            job.params["data_source"] = "provider_api"
            job.params["auth_method"] = auth_method
            job.params["auth_method_label"] = auth_method_label_for_provider(provider, auth_method)
            job.params[count_key] = len(outcome.items)
            job.params["read_only"] = True
            from aethos_core.runtime.operational_memory import operational_memory

            if provider == "railway":
                operational_memory.record_railway_inventory(
                    outcome.items,
                    last_inventory_job_id=job_id,
                )
            elif provider == "github":
                operational_memory.record_github_inventory(
                    outcome.items,
                    last_inventory_job_id=job_id,
                )
        job_store.complete_with_result(
            job_id,
            full_result=outcome.full_result,
            summary=outcome.summary,
            preview=outcome.preview,
            provider=api_provider,
            model=api_model,
            used_llm=False,
            fallback=False,
        )
    except error_cls as exc:
        job_store.fail_job(job_id, str(exc))
    except Exception as exc:
        job_store.fail_job(job_id, str(exc))


def _execute_vercel_inventory_job(
    *,
    job_id: str,
    job: Any,
    started: float,
    max_runtime: float,
) -> None:
    from aethos_core.runtime.jobs import job_store

    auth_method = str(job.params.get("auth_method") or "browser")
    try:
        if time() - started > max_runtime:
            raise TimeoutError("Job exceeded maximum runtime.")
        from aethos_core.runtime.vercel_readonly_inspector import (
            API_TOOL_USED,
            TOOL_USED,
            run_vercel_readonly_inspection,
        )

        profile_id = str(job.params.get("profile_id") or "")
        credential_id = str(job.params.get("credential_id") or "")
        tool_used = API_TOOL_USED if auth_method == "api_token" else TOOL_USED

        outcome = run_vercel_readonly_inspection(
            job_type=job.job_type,
            title=job.title,
            user_request=str(job.params.get("user_request") or ""),
            auth_method=auth_method,
            profile_id=profile_id,
            credential_id=credential_id,
        )
        job = job_store.get(job_id)
        if job:
            job.params["tool_used"] = tool_used
            job.params["browser_used"] = auth_method == "browser"
            job.params["auth_method"] = auth_method
            job.params["auth_method_label"] = auth_method_label(auth_method)
            if auth_method == "api_token":
                job.params["credential_id"] = credential_id or job.params.get("credential_id")
                job.params["profile_id"] = None
            else:
                job.params["profile_id"] = outcome.profile_id
            job.params["provider_used"] = "none"
            job.params["project_count"] = len(outcome.project_names)
            job.params["login_wall"] = outcome.login_wall
            if outcome.inventory is not None:
                from aethos_core.runtime.operational_memory import operational_memory

                job.params["vercel_inventory"] = outcome.inventory.to_dict()
                job.params["health_summary"] = outcome.inventory.health_summary.to_dict()
                operational_memory.record_vercel_extraction(
                    outcome.inventory,
                    profile_id=outcome.profile_id,
                    last_inventory_job_id=job_id,
                )
            if outcome.debug_excerpt:
                job.params["debug_excerpt"] = outcome.debug_excerpt
        summary_for_chat = outcome.summary
        if outcome.inventory and job.job_type == "vercel_projects_inventory":
            from aethos_core.runtime.vercel_inventory import build_chat_summary_bullets

            summary_for_chat = build_chat_summary_bullets(outcome.inventory)
        job_store.complete_with_result(
            job_id,
            full_result=outcome.full_result,
            summary=summary_for_chat,
            preview=outcome.preview,
            provider=tool_used,
            model="playwright",
            used_llm=False,
            fallback=False,
        )
    except Exception as exc:
        from aethos_core.runtime.browser_diagnostics import (
            classify_playwright_error,
            is_browser_runtime_error,
            runtime_not_ready_message,
        )
        from aethos_core.runtime.browser_executor import browser_executor, reset_browser_executor
        from aethos_core.runtime.browser_profile_store import browser_profile_store
        from aethos_core.runtime.browser_runtime import BrowserRuntimeBoundaryError

        msg = str(exc)
        profile_status = "unknown"
        runtime_status = "ok"
        runtime_ready = True
        inspection_status = "failed"
        pid = str(job.params.get("profile_id") or "")
        prof = browser_profile_store.get(pid) if pid else None
        if prof:
            profile_status = prof.status.value
        if isinstance(exc, BrowserRuntimeBoundaryError) or is_browser_runtime_error(exc):
            runtime_status = "failed"
            runtime_ready = False
            inspection_status = "not_run"
            kind = classify_playwright_error(msg)
            if isinstance(exc, BrowserRuntimeBoundaryError) or kind == "asyncio_sync_api_misuse":
                msg = (
                    "Browser runtime unavailable: Playwright Sync API was called outside the "
                    "browser executor thread. This is an AethOS runtime issue, not a Chromium install issue."
                )
            else:
                try:
                    from aethos_core.runtime.browser_diagnostics import probe_playwright_on_browser_thread

                    msg = runtime_not_ready_message(probe_playwright_on_browser_thread())
                except Exception:
                    pass
            try:
                reset_browser_executor()
            except Exception:
                _log.exception("browser_executor_reset_failed job_id=%s", job_id)
        if prof and profile_status != "unknown":
            msg += f" Saved profile `{pid}` remains `{profile_status}` on disk."
        job = job_store.get(job_id)
        if job:
            job.params["profile_status"] = profile_status
            job.params["runtime_status"] = runtime_status
            job.params["inspection_status"] = inspection_status
        failure = {
            "code": "BROWSER_RUNTIME_FAILED",
            "detail": msg,
            "profile_id": pid,
            "runtime_ready": runtime_ready,
        }
        _log.error(
            "vercel_inventory_job_failed job_id=%s profile_id=%s thread_id=%s "
            "browser_executor_thread_id=%s exc_type=%s last_browser_operation=%s\n%s",
            job_id,
            pid,
            threading.get_ident(),
            browser_executor.thread_id(),
            type(exc).__name__,
            browser_executor.status().active_operation,
            traceback.format_exc(),
        )
        job_store.fail_job(job_id, msg, failure=failure)
