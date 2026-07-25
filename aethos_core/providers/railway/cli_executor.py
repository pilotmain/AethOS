# SPDX-License-Identifier: Apache-2.0
"""Railway CLI executor — provider-native commands with captured evidence."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from aethos_core.config import get_settings
from aethos_core.security.secret_redaction import redact_text


def railway_cli_path() -> str | None:
    settings = get_settings()
    configured = (settings.railway_cli_path or "railway").strip()
    if configured and shutil.which(configured):
        return configured
    return None


def _run_cli(args: list[str], *, timeout_sec: float = 120.0) -> dict[str, Any]:
    cli = railway_cli_path()
    if not cli:
        return {"ok": False, "error": "Railway CLI not found.", "command": " ".join(args)}
    env = _cli_env()
    command = [cli, *args]
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": f"Railway CLI timed out after {timeout_sec}s.",
            "command": " ".join(command),
        }
    stdout = redact_text(proc.stdout or "")
    stderr = redact_text(proc.stderr or "")
    parsed: dict[str, Any] | list[Any] | None = None
    if stdout.strip():
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = None
    ok = proc.returncode == 0
    return {
        "ok": ok,
        "returncode": proc.returncode,
        "command": " ".join(command),
        "stdout": stdout,
        "stderr": stderr,
        "parsed": parsed,
        "error": None if ok else (stderr.strip() or stdout.strip() or f"exit {proc.returncode}"),
    }


def _cli_env() -> dict[str, str]:
    import os

    settings = get_settings()
    env = dict(os.environ)
    token = (settings.railway_api_token or "").strip()
    if token:
        env["RAILWAY_TOKEN"] = token
    project_id = (settings.railway_project_id or "").strip()
    if project_id:
        env["RAILWAY_PROJECT_ID"] = project_id
    environment_id = (settings.railway_environment_id or "").strip()
    if environment_id:
        env["RAILWAY_ENVIRONMENT_ID"] = environment_id
    return env


def railway_status() -> dict[str, Any]:
    return _run_cli(["status", "--json"])


def railway_restart(*, service_name: str) -> dict[str, Any]:
    return _run_cli(["restart", "--service", service_name, "--yes", "--json"])


def railway_redeploy(*, service_name: str) -> dict[str, Any]:
    return _run_cli(["redeploy", "--service", service_name, "--yes", "--json"])


def railway_up(*, service_name: str) -> dict[str, Any]:
    return _run_cli(["up", "--service", service_name, "--yes", "--json"])


def railway_logs(*, service_name: str, since: str | None = None, limit: int = 200) -> dict[str, Any]:
    args = ["logs", "--service", service_name, "--json"]
    if since:
        args.extend(["--since", since])
    result = _run_cli(args, timeout_sec=90.0)
    logs = _parse_logs(result)
    result["logs"] = logs[:limit]
    return result


def railway_variables(*, service_name: str) -> dict[str, Any]:
    return _run_cli(["variables", "--service", service_name, "--json"])


def cli_command_submitted(result: dict[str, Any]) -> bool:
    if not result.get("ok"):
        return False
    parsed = result.get("parsed")
    if isinstance(parsed, dict):
        if parsed.get("error"):
            return False
        return True
    if isinstance(parsed, list) and parsed:
        return True
    stdout = str(result.get("stdout") or "").strip()
    return bool(stdout) and "error" not in stdout.lower()


def _parse_logs(result: dict[str, Any]) -> list[dict[str, Any]]:
    parsed = result.get("parsed")
    if isinstance(parsed, list):
        return [row for row in parsed if isinstance(row, dict)]
    stdout = str(result.get("stdout") or "")
    rows: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            row = {"message": line, "timestamp": None}
        if isinstance(row, dict):
            rows.append(row)
    return rows
