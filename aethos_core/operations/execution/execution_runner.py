# SPDX-License-Identifier: Apache-2.0
"""Approved read-only execution runner — sandboxed, no mutations."""

from __future__ import annotations

import json
import logging
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.config import get_settings
from aethos_core.operations.execution.execution_artifacts import ExecutionArtifact, format_execution_report
from aethos_core.operations.execution.execution_evidence import (
    append_evidence,
    derive_diagnostic_assessment,
    enrich_domains_evidence,
    enrich_project_details_evidence,
    evidence_from_deployment,
    evidence_from_inventory_tags,
    evidence_from_log_payload,
    evidence_from_reachability,
    operational_events_from_deployment,
    operational_events_from_log_payload,
    select_failed_deployment,
    sort_operational_events,
)
from aethos_core.operations.execution.execution_permissions import assert_readonly_action
from aethos_core.operations.execution.execution_step_timeouts import ExecutionStepTimeoutError, run_with_timeout
from aethos_core.connections.adapters import auth_source_phrase
from aethos_core.operations.vercel_operation_capabilities import (
    is_api_only_operation,
    resolve_execution_auth,
    should_attempt_browser_fallback,
)
from aethos_core.runtime.latest_inventory_store import merge_project_state
from aethos_core.runtime.operational_memory import operational_memory
from aethos_core.runtime.workspace_diagnostics import resolve_workspace_root

_log = logging.getLogger(__name__)

MAX_OUTPUT = 12_000
DEFAULT_TIMEOUT = 45.0


@dataclass
class ExecutionOutcome:
    artifact: ExecutionArtifact
    summary: str
    preview: str
    full_result: str


def _new_execution_id() -> str:
    return f"rex-{uuid4().hex[:12]}"


def _truncate(text: str, limit: int = MAX_OUTPUT) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[: limit - 40] + "\n\n… (output truncated)"


def _run_git(args: list[str], *, cwd: Path, timeout: float = DEFAULT_TIMEOUT) -> str:
    if args[0] != "git":
        raise ValueError("Only git commands allowed")
    allowed = {"status", "branch", "remote", "log", "rev-parse", "diff"}
    if args[1] not in allowed:
        raise PermissionError(f"Git subcommand not allowed: {args[1]}")
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    if proc.returncode != 0 and not out.strip():
        out = f"exit {proc.returncode}"
    return _truncate(out)


def _run_npm(script: str, *, cwd: Path, timeout: float = DEFAULT_TIMEOUT) -> str:
    if script not in {"test", "typecheck"}:
        raise PermissionError(f"npm script not allowed: {script}")
    proc = subprocess.run(
        ["npm", "run", script],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    return _truncate(out)


def _url_reachability(url: str, *, timeout: float | None = None) -> dict[str, Any]:
    reach_timeout = float(timeout if timeout is not None else get_settings().url_reachability_timeout_sec)
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "AethOS-readonly-exec/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=reach_timeout) as resp:
            return {
                "url": url,
                "reachable": True,
                "status_code": resp.status,
                "summary": f"HTTP {resp.status} from {url}",
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "reachable": exc.code < 500,
            "status_code": exc.code,
            "summary": f"HTTP {exc.code} from {url}",
        }
    except Exception as exc:
        return {"url": url, "reachable": False, "summary": str(exc)}


def _package_scripts(repo: Path) -> dict[str, Any]:
    pkg = repo / "web" / "package.json"
    if not pkg.is_file():
        pkg = repo / "package.json"
    if not pkg.is_file():
        return {"summary": "No package.json found", "scripts": {}}
    data = json.loads(pkg.read_text(encoding="utf-8"))
    scripts = dict(data.get("scripts") or {})
    return {"path": str(pkg), "scripts": scripts, "summary": ", ".join(sorted(scripts.keys())[:12])}


def _append_timeline(artifact: ExecutionArtifact, status: str, message: str) -> None:
    artifact.timeline.append({"at": time(), "status": status, "message": message})


def _step_timeout(step: str) -> float:
    settings = get_settings()
    if step == "url_reachability":
        return float(settings.url_reachability_timeout_sec)
    if step == "browser_fallback":
        return float(settings.browser_fallback_step_timeout_sec)
    return float(settings.vercel_api_step_timeout_sec)


def _run_step(step: str, fn, *, job_id: str | None = None):
    _log.info("readonly_execution_step_start step=%s job_id=%s", step, job_id or "")
    try:
        result = run_with_timeout(fn, timeout_sec=_step_timeout(step), step=step)
        _log.info("readonly_execution_step_done step=%s job_id=%s", step, job_id or "")
        return result
    except ExecutionStepTimeoutError:
        _log.warning("readonly_execution_step_timeout step=%s job_id=%s", step, job_id or "")
        raise


def run_local_readonly_execution(*, params: dict[str, Any], job_id: str | None = None) -> ExecutionOutcome:
    from aethos_core.operations.execution.execution_progress import ACTION_PROGRESS, emit_step, progress_emitter

    progress = progress_emitter(job_id)
    actions = list(params.get("approved_actions") or [])
    artifact = ExecutionArtifact(
        execution_id=_new_execution_id(),
        provider="local",
        operation_type=str(params.get("operation_type") or "local_workspace"),
        target_name=str(params.get("target_name") or resolve_workspace_root()),
        approved_actions=actions,
    )
    root = resolve_workspace_root()
    _append_timeline(artifact, "started", f"Read-only local inspection of {root}")

    for action in actions:
        assert_readonly_action(action)
        emit_step(progress, ACTION_PROGRESS.get(action, action.replace("_", " ")))
        _append_timeline(artifact, "running", action)
        try:
            if action == "git_status":
                out = _run_git(["git", "status", "--porcelain=v1", "-b"], cwd=root)
                artifact.findings.append({"action": action, "output": out})
            elif action == "git_branch":
                out = _run_git(["git", "branch", "--show-current"], cwd=root)
                artifact.findings.append({"action": action, "output": out})
            elif action == "git_remote":
                out = _run_git(["git", "remote", "-v"], cwd=root)
                artifact.findings.append({"action": action, "output": out})
            elif action == "git_log":
                out = _run_git(["git", "log", "-3", "--oneline"], cwd=root)
                artifact.findings.append({"action": action, "output": out})
            elif action == "package_scripts":
                artifact.findings.append({"action": action, **_package_scripts(root)})
            elif action == "npm_typecheck":
                web = root / "web"
                if (web / "package.json").is_file():
                    out = _run_npm("typecheck", cwd=web)
                    artifact.findings.append({"action": action, "output": out})
                else:
                    artifact.findings.append({"action": action, "output": "skipped — no web/package.json"})
            elif action == "npm_test":
                web = root / "web"
                if (web / "package.json").is_file():
                    out = _run_npm("test", cwd=web, timeout=90.0)
                    artifact.findings.append({"action": action, "output": out})
                else:
                    artifact.findings.append({"action": action, "output": "skipped — no web/package.json"})
        except Exception as exc:
            artifact.findings.append({"action": action, "output": f"error: {exc}"})

    _append_timeline(artifact, "completed", "Local read-only inspection finished")
    full = format_execution_report(artifact)
    summary = f"Read-only local inspection completed for `{root}` ({len(artifact.findings)} checks)."
    return ExecutionOutcome(artifact=artifact, summary=summary, preview=summary[:240], full_result=full)


def _resolve_vercel_adapter(params: dict[str, Any], operation_type: str):
    auth = resolve_execution_auth(operation_type, params)
    auth_method = auth["auth_method"]
    auth_label = auth["auth_method_label"]
    credential_id = auth["credential_id"]
    adapter = None
    if auth_method == "api_token" and credential_id:
        from aethos_core.operations.orchestration.registry_runtime import resolve_readonly_execution_adapter

        adapter = resolve_readonly_execution_adapter("vercel", credential_id)
    return adapter, auth_method, auth_label, credential_id


def run_vercel_readonly_execution(*, params: dict[str, Any], job_id: str | None = None) -> ExecutionOutcome:
    from aethos_core.operations.execution.execution_progress import ACTION_PROGRESS, emit_step, progress_emitter

    progress = progress_emitter(job_id)
    emit_step(progress, "Preparing read-only checks")
    _log.info("readonly_execution_start job_id=%s target=%s op=%s", job_id, params.get("target_name"), params.get("operation_type"))
    actions = list(params.get("approved_actions") or [])
    target = str(params.get("target_name") or "")
    operation_type = str(params.get("operation_type") or "check_logs")
    emit_step(progress, "Building adapter")
    adapter, auth_method, auth_label, credential_id = _resolve_vercel_adapter(params, operation_type)
    emit_step(progress, "Loading operational memory")
    mem_map = operational_memory.get_vercel_project_memory()
    mem = mem_map.get(target.strip().lower()) if target else None
    state = merge_project_state(project_name=target, memory=mem)
    from aethos_core.operations.execution.execution_formatting import normalize_production_url

    prod_url = normalize_production_url(
        str(params.get("production_url") or state.get("production_url") or "") or None
    )
    is_failure_diagnostic = operation_type in ("why_down", "inspect_failed_deployment")
    artifact = ExecutionArtifact(
        execution_id=_new_execution_id(),
        provider="vercel",
        operation_type=operation_type,
        target_name=target or None,
        approved_actions=actions,
    )
    artifact.auth_method = auth_method
    artifact.auth_method_label = auth_label
    artifact.data_source = "memory"
    _append_timeline(
        artifact,
        "started",
        f"Read-only Vercel {operation_type.replace('_', ' ')} for `{target}` "
        f"using your {auth_source_phrase(auth_method)}",
    )

    if adapter:
        artifact.data_source = "provider_api"

    deploy_state = str(state.get("latest_deployment_state") or "unknown")
    evidence = list(state.get("evidence") or [])
    api_deployments: dict[str, Any] | None = None
    api_log_payload: dict[str, Any] | None = None
    api_project_id: str | None = None
    api_team_id: str | None = None

    for action in actions:
        assert_readonly_action(action)
        step_label = ACTION_PROGRESS.get(action, action.replace("_", " "))
        emit_step(progress, step_label)
        _append_timeline(artifact, "running", action)
        try:
            if action == "url_reachability":
                if prod_url:
                    result = _run_step(
                        "url_reachability",
                        lambda: _url_reachability(str(prod_url)),
                        job_id=job_id,
                    )
                    artifact.findings.append({"action": action, "source": "local_probe", **result})
                    reach_ev = evidence_from_reachability(result)
                    if reach_ev:
                        append_evidence(artifact, reach_ev)
                else:
                    artifact.findings.append(
                        {
                            "action": action,
                            "source": "memory",
                            "summary": "No production URL available — reachability check skipped.",
                        }
                    )
            elif action == "vercel_api_deployments" and adapter and target:
                payload = _run_step(
                    "vercel_api_deployments",
                    lambda: adapter.get_deployments(project_name=target),
                    job_id=job_id,
                )
                api_deployments = payload
                api_project_id = str(payload.get("project_id") or "") or None
                artifact.data_source = str(payload.get("source") or "provider_api")
                artifact.findings.append(
                    {
                        "action": action,
                        "source": artifact.data_source,
                        "ok": payload.get("ok"),
                        "output": payload.get("output"),
                        "deployments": payload.get("deployments"),
                    }
                )
                if payload.get("ok"):
                    operational_memory.record_vercel_api_execution(
                        project_name=target,
                        operation_type=operation_type if operation_type != "check_logs" else "list_deployments",
                        payload=payload,
                    )
                if not is_failure_diagnostic:
                    for dep in payload.get("deployments") or []:
                        if isinstance(dep, dict):
                            for item in evidence_from_deployment(dep):
                                append_evidence(artifact, item)
            elif action == "vercel_api_domains" and adapter and target:
                payload = _run_step(
                    "vercel_api_domains",
                    lambda: adapter.get_domains(project_name=target),
                    job_id=job_id,
                )
                artifact.data_source = str(payload.get("source") or "provider_api")
                artifact.findings.append(
                    {
                        "action": action,
                        "source": artifact.data_source,
                        "ok": payload.get("ok"),
                        "output": payload.get("output"),
                        "domains": payload.get("domains"),
                    }
                )
                if payload.get("ok"):
                    operational_memory.record_vercel_api_execution(
                        project_name=target,
                        operation_type="list_domains",
                        payload=payload,
                    )
                enrich_domains_evidence(artifact, payload)
            elif action == "vercel_api_project_details" and adapter and target:
                payload = _run_step(
                    "vercel_api_project_details",
                    lambda: adapter.get_project_details(project_name=target),
                    job_id=job_id,
                )
                artifact.data_source = str(payload.get("source") or "provider_api")
                artifact.findings.append(
                    {
                        "action": action,
                        "source": artifact.data_source,
                        "ok": payload.get("ok"),
                        "output": payload.get("output"),
                        "details": payload.get("details"),
                    }
                )
                if payload.get("ok"):
                    operational_memory.record_vercel_api_execution(
                        project_name=target,
                        operation_type="project_details",
                        payload=payload,
                    )
                enrich_project_details_evidence(artifact, payload)
            elif action in ("vercel_deployment_inspect", "vercel_logs_inspect"):
                lines = [
                    f"Target: {target}",
                    f"Latest deployment state (memory): {deploy_state}",
                    f"Operator status: {state.get('operator_status', 'unknown')}",
                    f"Production health: {state.get('production_health', 'unknown')}",
                ]
                if evidence:
                    lines.append("Evidence: " + ", ".join(evidence))
                source = "memory"
                if action == "vercel_logs_inspect" and adapter and target:
                    dep_id = None
                    if api_deployments and api_deployments.get("deployments"):
                        failed = select_failed_deployment(api_deployments["deployments"])
                        if isinstance(failed, dict):
                            dep_id = str(failed.get("id") or "")
                    try:
                        log_payload = _run_step(
                            "vercel_logs_inspect",
                            lambda: adapter.get_deployment_logs(
                                project_name=target,
                                deployment_id=dep_id,
                                project_id=api_project_id,
                                team_id=api_team_id,
                            ),
                            job_id=job_id,
                        )
                    except ExecutionStepTimeoutError as exc:
                        log_payload = {
                            "ok": False,
                            "source": "provider_api",
                            "error": str(exc),
                            "deployment_id": dep_id,
                            "log_lines": [],
                            "api_limited": True,
                            "step_timed_out": True,
                        }
                    api_log_payload = log_payload
                    if log_payload.get("ok") or log_payload.get("log_lines"):
                        source = "provider_api"
                        artifact.data_source = "provider_api"
                        lines.append("")
                        lines.append(log_payload.get("output") or "")
                        operational_memory.record_vercel_api_execution(
                            project_name=target,
                            operation_type=operation_type,
                            payload=log_payload,
                        )
                        if not is_failure_diagnostic:
                            for item in evidence_from_log_payload(log_payload):
                                append_evidence(artifact, item)
                            artifact.operational_events.extend(operational_events_from_log_payload(log_payload))
                    elif log_payload.get("api_limited"):
                        if should_attempt_browser_fallback(operation_type):
                            browser_note = _try_browser_log_excerpt(params, target=target, job_id=job_id)
                            if browser_note:
                                source = "browser_fallback"
                                artifact.data_source = "browser_fallback"
                                lines.append("")
                                lines.append("Browser fallback used for missing provider API data.")
                                lines.append(browser_note)
                            else:
                                lines.append("")
                                lines.append(str(log_payload.get("error") or "Vercel API logs unavailable."))
                                lines.append("Browser log fallback is currently unavailable.")
                        else:
                            lines.append("")
                            lines.append(str(log_payload.get("error") or "Vercel API logs unavailable."))
                            if not is_api_only_operation(operation_type):
                                lines.append(
                                    "Browser log fallback is currently unavailable because Playwright is blocked."
                                )
                    else:
                        lines.append("")
                        lines.append(str(log_payload.get("error") or "No API log lines returned."))
                elif action == "vercel_deployment_inspect" and adapter and target and not api_deployments:
                    payload = _run_step(
                        "vercel_api_deployments",
                        lambda: adapter.get_deployments(project_name=target, limit=10),
                        job_id=job_id,
                    )
                    if payload.get("ok"):
                        source = "provider_api"
                        artifact.data_source = "provider_api"
                        lines.append("")
                        lines.append(payload.get("output") or "")
                elif action == "vercel_logs_inspect" and should_attempt_browser_fallback(operation_type):
                    browser_note = _try_browser_log_excerpt(params, target=target, job_id=job_id)
                    if browser_note:
                        source = "browser_fallback"
                        artifact.data_source = "browser_fallback"
                        lines.append("")
                        lines.append("Browser fallback used for missing provider API data.")
                        lines.append(browser_note)
                    else:
                        lines.append("")
                        lines.append(
                            "(Dashboard log extraction uses saved browser session when runtime is available.)"
                        )
                artifact.findings.append(
                    {
                        "action": action,
                        "source": source,
                        "output": "\n".join(lines),
                        "deployment_id": (api_log_payload or {}).get("deployment_id"),
                        "events": (api_log_payload or {}).get("events"),
                    }
                )
        except ExecutionStepTimeoutError as exc:
            artifact.findings.append(
                {
                    "action": action,
                    "source": "provider_api",
                    "ok": False,
                    "output": f"Step timed out: {exc}",
                    "step_timed_out": True,
                }
            )
            _append_timeline(artifact, "warning", f"{step_label} timed out — continuing with partial evidence")

    if not adapter and auth_method == "api_token":
        artifact.findings.append(
            {
                "action": "auth",
                "source": "memory",
                "output": "Vercel API token configured but adapter unavailable — using memory/browser fallback only.",
            }
        )

    emit_step(progress, "Building evidence artifact")
    _finalize_vercel_diagnostic_artifact(
        artifact,
        operation_type=operation_type,
        deploy_state=deploy_state,
        inventory_evidence=evidence,
        api_deployments=api_deployments,
        api_log_payload=api_log_payload,
        prod_url=prod_url,
    )

    emit_step(progress, "Formatting report")
    _append_timeline(artifact, "completed", "Vercel read-only execution finished — no mutation performed")
    full = format_execution_report(artifact)
    _log.info(
        "readonly_execution_complete job_id=%s execution_id=%s confidence=%s",
        job_id,
        artifact.execution_id,
        artifact.confidence,
    )
    source_label = {
        "provider_api": "Provider API execution",
        "browser_fallback": "Browser fallback used for missing provider API data",
        "memory": "Operational memory",
    }.get(artifact.data_source, artifact.data_source)
    summary = (
        f"Read-only Vercel {operation_type.replace('_', ' ')} for `{target}` "
        f"via {auth_label} · {source_label} · confidence: {artifact.confidence}."
    )
    if artifact.probable_root_cause:
        summary += f" {artifact.diagnostic.get('primary_finding', artifact.probable_root_cause)}"
    return ExecutionOutcome(artifact=artifact, summary=summary[:500], preview=summary[:240], full_result=full)


def _finalize_vercel_diagnostic_artifact(
    artifact: ExecutionArtifact,
    *,
    operation_type: str,
    deploy_state: str,
    inventory_evidence: list[str],
    api_deployments: dict[str, Any] | None,
    api_log_payload: dict[str, Any] | None,
    prod_url: str | None,
) -> None:
    if operation_type in ("why_down", "inspect_failed_deployment"):
        from aethos_core.operations.execution.failure_diagnostic_artifact import enrich_failure_diagnostic_artifact

        reach = next((f for f in artifact.findings if f.get("action") == "url_reachability"), None)
        enrich_failure_diagnostic_artifact(
            artifact,
            inventory_evidence=inventory_evidence,
            api_deployments=api_deployments,
            api_log_payload=api_log_payload,
            prod_url=prod_url,
            reachability=reach if isinstance(reach, dict) else None,
        )
        return

    for item in evidence_from_inventory_tags(inventory_evidence):
        append_evidence(artifact, item)

    failed_dep = None
    if api_deployments:
        failed_dep = select_failed_deployment(list(api_deployments.get("deployments") or []))
        if isinstance(failed_dep, dict):
            artifact.operational_events.extend(operational_events_from_deployment(failed_dep))
    elif api_log_payload and isinstance(api_log_payload.get("deployment"), dict):
        failed_dep = api_log_payload["deployment"]
        artifact.operational_events.extend(operational_events_from_deployment(failed_dep))

    artifact.operational_events = sort_operational_events(artifact.operational_events)


def _try_browser_log_excerpt(params: dict[str, Any], *, target: str, job_id: str | None = None) -> str | None:
    profile_id = str(params.get("profile_id") or "")
    if not profile_id:
        return None
    try:
        from aethos_core.runtime.browser_driver import DriverHandle, get_browser_driver
        from aethos_core.runtime.browser_runtime import run_playwright_on_browser_thread
        from aethos_core.browser.platforms.vercel.vercel_detail_inspector import (
            infer_team_from_page,
            project_deployments_url,
        )
        from aethos_core.runtime.browser_readiness import preflight_readonly_profile

        profile = preflight_readonly_profile(profile_id)
        storage_path = Path(profile.storage_path)

        def _work() -> str:
            driver = get_browser_driver()
            handle: DriverHandle | None = None
            try:
                handle = driver.open_url(
                    "https://vercel.com/dashboard",
                    headless=True,
                    storage_state_path=str(storage_path.resolve()),
                )
                page = handle.page
                team = infer_team_from_page(page)
                if not team:
                    return "Could not infer Vercel team from dashboard."
                url = project_deployments_url(team, target)
                page.goto(url, wait_until="domcontentloaded", timeout=15_000)
                text = page.locator("body").inner_text(timeout=8_000) or ""
                excerpt = _truncate(text, 2500)
                failed = bool(re.search(r"\b(failed|error|errored)\b", excerpt, re.I))
                head = f"Deployments page excerpt ({url}):"
                if failed:
                    head += " failure signals present in visible text."
                return head + "\n\n" + excerpt
            finally:
                if handle is not None:
                    driver.close_handle(handle)

        return _run_step("browser_fallback", lambda: run_playwright_on_browser_thread(_work), job_id=job_id)
    except ExecutionStepTimeoutError as exc:
        return f"Browser log inspect timed out: {exc}"
    except Exception as exc:
        return f"Browser log inspect skipped: {exc}"


def run_readonly_execution(*, job_type: str, params: dict[str, Any], job_id: str | None = None) -> ExecutionOutcome:
    from aethos_core.operations.orchestration.job_taxonomy import resolve_readonly_execution_provider

    provider = resolve_readonly_execution_provider(job_type, params)
    if job_type == "readonly_execution_local" or provider == "local":
        return run_local_readonly_execution(params=params, job_id=job_id)
    if provider == "railway" or job_type == "readonly_execution_railway":
        from aethos_core.operations.execution.railway_execution_runner import run_railway_readonly_execution

        return run_railway_readonly_execution(params=params, job_id=job_id)
    if provider == "github" or job_type == "readonly_execution_github":
        from aethos_core.operations.execution.github_execution_runner import run_github_readonly_execution

        return run_github_readonly_execution(params=params, job_id=job_id)
    return run_vercel_readonly_execution(params=params, job_id=job_id)
