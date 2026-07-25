# SPDX-License-Identifier: Apache-2.0
"""Execute one execution-plan step."""

from __future__ import annotations

from typing import Any


def execute_tool_step(step: dict[str, Any]) -> dict[str, Any]:
    tool = step.get("tool")
    name = ""
    if isinstance(tool, dict):
        name = str(tool.get("name") or "").strip()
    if not name:
        name = str(step.get("type") or "noop").strip() or "noop"
    inp: dict[str, Any] = {}
    if isinstance(tool, dict) and isinstance(tool.get("input"), dict):
        inp = dict(tool["input"])

    if name == "noop":
        return {"tool": "noop", "ok": True, "outputs": list(step.get("outputs") or [])}

    if name == "echo":
        return {"tool": "echo", "ok": True, "message": str(inp.get("message") or "")}

    if name == "sleep_ms":
        import time

        ms = int(inp.get("milliseconds") or 0)
        if ms > 0:
            time.sleep(min(ms, 50) / 1000.0)
        return {"tool": "sleep_ms", "ok": True, "milliseconds": ms}

    if name == "shell":
        from aethos_core.runtime.actions import run_governed_shell_command

        return run_governed_shell_command(
            str(inp.get("command") or ""),
            timeout_sec=float(inp.get("timeout_sec") or 120.0),
            cwd=str(inp.get("cwd") or "") or None,
        )

    if name == "file_read":
        from aethos_core.runtime.actions import read_governed_file

        return read_governed_file(str(inp.get("path") or ""))

    if name == "file_write":
        from aethos_core.runtime.actions import write_governed_file

        return write_governed_file(
            str(inp.get("path") or ""),
            str(inp.get("content") or ""),
            append=bool(inp.get("append")),
        )

    if name == "http_request":
        from aethos_core.runtime.actions import run_governed_http_request

        return run_governed_http_request(
            url=str(inp.get("url") or ""),
            method=str(inp.get("method") or "GET"),
            timeout_sec=float(inp.get("timeout_sec") or 30.0),
            headers=inp.get("headers") if isinstance(inp.get("headers"), dict) else None,
        )

    if name == "internal_api":
        path = str(inp.get("path") or "/api/v1/health").strip()
        port = int(inp.get("port") or 8010)
        from aethos_core.runtime.actions import run_governed_http_request

        return run_governed_http_request(url=f"http://127.0.0.1:{port}{path}")

    if name == "provider_discover":
        provider = str(inp.get("provider") or "").strip().lower()
        if not provider:
            return {"tool": name, "ok": False, "error": "provider_required"}
        from aethos_core.provider_skills.runtime import load_provider_skill

        skill = load_provider_skill(provider)
        if skill is None:
            return {"tool": name, "ok": False, "error": f"unknown_provider:{provider}"}
        payload = skill.discover(force=True)
        return {"tool": name, "ok": bool(payload.get("ok")), "provider": provider, "result": payload}

    return {"tool": name, "ok": False, "error": "unknown_tool"}
