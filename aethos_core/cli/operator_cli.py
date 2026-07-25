# SPDX-License-Identifier: Apache-2.0
"""Operator CLI — gateway, status, logs, and message dispatch parity surface."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

OPERATOR_DEFAULT_SESSION_ID = "operator"


def cmd_onboard() -> int:
    print("AethOS operator onboarding")
    print("")
    print("1. Copy `.env.example` → `.env` and set provider credentials.")
    print("2. Enable solo/greenfield flags if you want one-shot Railway deploy from chat.")
    print("3. Run `aethos doctor` then start the API with `aethos gateway`.")
    print("4. Open Mission Control at http://127.0.0.1:3000/mission-control (after `cd web && npm run dev`).")
    return 0


def cmd_tunnel(*, action: str, api_base: str) -> int:
    action = (action or "status").strip().lower()
    if action not in {"start", "stop", "restart", "status"}:
        print("Usage: aethos tunnel {start|stop|restart|status}")
        return 1
    base = api_base.rstrip("/")
    if action == "status":
        url = f"{base}/api/v1/runtime/tunnel/status"
        payload = _http_get_json(url)
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ok", True) else 1
    url = f"{base}/api/v1/runtime/tunnel/{action}"
    req = urllib.request.Request(url, data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(body)
        return exc.code
    except urllib.error.URLError as exc:
        print(f"Gateway unreachable: {exc}")
        return 1
    try:
        print(json.dumps(json.loads(body), indent=2))
    except json.JSONDecodeError:
        print(body)
    return 0


def cmd_gateway(*, host: str, port: int, reload: bool) -> int:
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "aethos_core.api.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")
    print(f"Starting AethOS gateway on http://{host}:{port}")
    return subprocess.call(cmd)


def cmd_status(*, api_base: str) -> int:
    from aethos_core.operational_skill_runtime.skill_registry import skill_registry_snapshot
    from aethos_core.runtime.operational_environment import resolve_operational_environment

    health_url = f"{api_base.rstrip('/')}/api/v1/health"
    health = _http_get_json(health_url)
    snapshot = skill_registry_snapshot()
    environment = resolve_operational_environment()
    print(environment.banner)
    print("")
    print(json.dumps({"health": health, "operational_environment": environment.to_dict(), "provider_skills": snapshot}, indent=2))
    return 0 if health.get("ok", True) else 1


def cmd_logs(*, category: str | None, lines: int) -> int:
    root = Path(__file__).resolve().parents[2] / "data"
    if not root.is_dir():
        print("(no data/ log directory yet)")
        return 0
    patterns = {
        None: ["*.json", "*.jsonl", "*.log"],
        "runtime": ["operational_threads/*.json", "railway_execution_journal/*.json"],
        "gateway": ["*.log"],
    }
    globs = patterns.get(category, patterns[None])
    collected: list[tuple[float, Path]] = []
    for pattern in globs or patterns[None]:
        for path in root.glob(pattern):
            if path.is_file():
                collected.append((path.stat().st_mtime, path))
    collected.sort(reverse=True)
    shown = 0
    for _, path in collected[:12]:
        print(f"--- {path.relative_to(root.parent)} ---")
        try:
            text = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in text[-lines:]:
            print(line)
        shown += 1
    if not shown:
        print("(no log files matched)")
    return 0


def cmd_message_send(*, api_base: str, message: str, session_id: str) -> int:
    url = f"{api_base.rstrip('/')}/api/v1/chat/deterministic"
    payload = json.dumps({"message": message, "session_id": session_id}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(body)
        return exc.code
    except urllib.error.URLError as exc:
        print(f"Gateway unreachable: {exc}")
        return 1
    try:
        parsed = json.loads(body)
        print(parsed.get("reply") or parsed.get("message") or body)
    except json.JSONDecodeError:
        print(body)
    return 0


def _http_get_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return {"ok": False, "error": str(exc), "url": url}


def cmd_install_service(*, port: int = 8010, host: str = "127.0.0.1") -> int:
    """Print launchd/systemd unit templates for always-on gateway (operator installs manually)."""
    import platform

    system = platform.system().lower()
    python = sys.executable
    cwd = Path.cwd()
    if system == "darwin":
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.aethos.gateway</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python}</string><string>-m</string><string>uvicorn</string>
    <string>aethos_core.api.main:app</string>
    <string>--host</string><string>{host}</string><string>--port</string><string>{port}</string>
  </array>
  <key>WorkingDirectory</key><string>{cwd}</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>"""
        print("Save to ~/Library/LaunchAgents/com.aethos.gateway.plist then:")
        print("  launchctl load ~/Library/LaunchAgents/com.aethos.gateway.plist")
        print(plist)
        return 0
    unit = f"""[Unit]
Description=AethOS API Gateway
After=network.target

[Service]
Type=simple
WorkingDirectory={cwd}
ExecStart={python} -m uvicorn aethos_core.api.main:app --host {host} --port {port}
Restart=always

[Install]
WantedBy=multi-user.target
"""
    print("Save to /etc/systemd/system/aethos-gateway.service then:")
    print("  sudo systemctl daemon-reload && sudo systemctl enable --now aethos-gateway")
    print(unit)
    return 0
