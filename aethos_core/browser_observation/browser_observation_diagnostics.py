# SPDX-License-Identifier: Apache-2.0
"""Browser observation runtime diagnostics — verify actual launch path, not .env alone."""

from __future__ import annotations

import os
from typing import Any

_CANONICAL_ENV_VAR = "BROWSER_AUTOMATION_ENABLED"
_IGNORED_ENV_VARS = ("PLAYWRIGHT_ENABLED", "BROWSER_ENABLED")


def inspect_browser_observation_runtime(*, probe_launch: bool = True) -> dict[str, Any]:
    """Probe the active API/runtime process for readonly browser observation readiness."""
    from aethos_core.config import get_settings
    from aethos_core.runtime.browser_capability import get_browser_capability_status
    from aethos_core.runtime.browser_diagnostics import recommended_install_commands
    from aethos_core.runtime.browser_executor import get_browser_executor_status

    settings = get_settings()
    raw_env = os.environ.get(_CANONICAL_ENV_VAR)
    env_loaded = bool(settings.browser_automation_enabled)

    cap = get_browser_capability_status(probe_launch=probe_launch and env_loaded)
    nested = dict(cap.get("diagnostics") or {})
    worker = get_browser_executor_status()

    package_ok = str(cap.get("playwright_package") or nested.get("playwright_package") or "") == "installed"
    chromium_state = str(cap.get("chromium_browser") or nested.get("chromium_browser") or "unknown")
    chromium_ok = chromium_state == "installed"
    worker_ok = bool(worker.get("running"))
    execution_ready = bool(cap.get("execution_ready"))

    launch_test = _format_launch_test(
        env_loaded=env_loaded,
        package_ok=package_ok,
        chromium_ok=chromium_ok,
        execution_ready=execution_ready,
        probe_launch=probe_launch,
        nested=nested,
        cap=cap,
    )

    install_cmds = list(nested.get("recommended_install_commands") or [])
    if not install_cmds and not execution_ready:
        install_cmds = recommended_install_commands()

    return {
        "canonical_env_var": _CANONICAL_ENV_VAR,
        "ignored_env_vars": list(_IGNORED_ENV_VARS),
        "env_flag_loaded": env_loaded,
        "env_raw_process_value": raw_env,
        "settings_value": settings.browser_automation_enabled,
        "playwright_python_package_installed": package_ok,
        "chromium_binary_installed": chromium_ok,
        "browser_launch_test": launch_test,
        "worker_enabled": worker_ok,
        "execution_ready": execution_ready,
        "python_executable": nested.get("python_executable"),
        "playwright_version": nested.get("playwright_version"),
        "chromium_executable_path": nested.get("chromium_executable_path"),
        "failure_kind": cap.get("failure_kind"),
        "failure_layer": nested.get("failure_layer"),
        "runtime_bug": bool(cap.get("runtime_bug")),
        "user_message": cap.get("user_message"),
        "executor_status": worker,
        "recommended_install_commands": install_cmds,
        "remediation_notes": _remediation_notes(
            env_loaded=env_loaded,
            package_ok=package_ok,
            chromium_ok=chromium_ok,
            worker_ok=worker_ok,
            execution_ready=execution_ready,
            install_cmds=install_cmds,
            runtime_bug=bool(cap.get("runtime_bug")),
        ),
    }


def _format_launch_test(
    *,
    env_loaded: bool,
    package_ok: bool,
    chromium_ok: bool,
    execution_ready: bool,
    probe_launch: bool,
    nested: dict[str, Any],
    cap: dict[str, Any],
) -> str:
    if not env_loaded:
        return "skipped (`BROWSER_AUTOMATION_ENABLED` is false in the loaded API settings)"
    if not package_ok:
        err = nested.get("import_error") or "Playwright package not importable"
        return f"fail ({err})"
    if not probe_launch:
        return "not run (import-only probe)"
    if execution_ready:
        return "pass"
    err = (
        nested.get("launch_probe_error")
        or cap.get("user_message")
        or nested.get("chromium_error")
        or "Chromium launch probe failed"
    )
    if not chromium_ok:
        return f"fail (Chromium binary missing — {err})"
    return f"fail ({err})"


def _remediation_notes(
    *,
    env_loaded: bool,
    package_ok: bool,
    chromium_ok: bool,
    worker_ok: bool,
    execution_ready: bool,
    install_cmds: list[str],
    runtime_bug: bool,
) -> list[str]:
    notes: list[str] = []
    if not env_loaded:
        notes.append(
            f"Set `{_CANONICAL_ENV_VAR}=true` in `.env`, then **restart the AethOS API process** "
            "(not only the frontend). `PLAYWRIGHT_ENABLED` and `BROWSER_ENABLED` are not read by AethOS."
        )
    elif execution_ready:
        return notes
    else:
        notes.append(
            "`.env` values are not proof until the **running API process** loads them and passes launch probes."
        )
    if runtime_bug:
        notes.append(
            "This looks like an AethOS Playwright sync/async boundary issue — restart the API after updating; "
            "do not run `playwright install` for that error class."
        )
    if env_loaded and package_ok and not chromium_ok and install_cmds:
        notes.append(f"Install Chromium for this API Python: `{install_cmds[-1]}`")
    elif env_loaded and not package_ok and install_cmds:
        notes.append(f"Install Playwright in this API Python environment: `{install_cmds[0]}`")
    if env_loaded and package_ok and chromium_ok and not worker_ok:
        notes.append("Browser worker thread is not running — restart the AethOS API process.")
    return notes


def format_browser_observation_blocked_reply(diagnostics: dict[str, Any]) -> str:
    """Human-readable blocked reply with explicit sub-checks."""
    yes_no = lambda v: "yes" if v else "no"  # noqa: E731
    env_var = str(diagnostics.get("canonical_env_var") or _CANONICAL_ENV_VAR)
    env_suffix = f" (settings={diagnostics.get('settings_value')!r})"
    raw_env = diagnostics.get("env_raw_process_value")
    if raw_env is not None:
        env_suffix = f" (process env={raw_env!r}, settings={diagnostics.get('settings_value')!r})"
    lines = [
        "Browser observation is available, but execution is currently blocked.",
        "",
        "Runtime checks (this API process):",
        f"- env flag loaded (`{env_var}`): {yes_no(diagnostics.get('env_flag_loaded'))}{env_suffix}",
        f"- playwright python package installed: {yes_no(diagnostics.get('playwright_python_package_installed'))}",
        f"- chromium binary installed: {yes_no(diagnostics.get('chromium_binary_installed'))}",
        f"- browser launch test: {diagnostics.get('browser_launch_test') or 'unknown'}",
        f"- worker enabled: {yes_no(diagnostics.get('worker_enabled'))}",
    ]
    if diagnostics.get("python_executable"):
        lines.append(f"- python executable: `{diagnostics['python_executable']}`")
    if diagnostics.get("playwright_version"):
        lines.append(f"- playwright version: `{diagnostics['playwright_version']}`")
    ignored = diagnostics.get("ignored_env_vars") or []
    if ignored:
        lines.append(f"- ignored env vars (not used by AethOS): {', '.join(ignored)}")

    notes = list(diagnostics.get("remediation_notes") or [])
    if notes:
        lines.extend(["", "What to do:"])
        for note in notes:
            lines.append(f"- {note}")

    cmds = list(diagnostics.get("recommended_install_commands") or [])
    if cmds and not diagnostics.get("execution_ready"):
        lines.extend(["", "Install commands (run in the API Python environment):"])
        for cmd in cmds:
            lines.append(f"- `{cmd}`")

    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)
