# SPDX-License-Identifier: Apache-2.0
"""ngrok tunnel adapter."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from typing import Any

import httpx

from aethos_core.config import get_settings

_log = logging.getLogger(__name__)

_NGROK_PROC: subprocess.Popen | None = None


def ngrok_available() -> bool:
    return shutil.which("ngrok") is not None


def start_ngrok(*, port: int | None = None) -> dict[str, Any]:
    """Start ngrok tunnel — requires NGROK_AUTHTOKEN when configured."""
    global _NGROK_PROC
    settings = get_settings()
    if not settings.telegram_tunnel_enabled:
        return {"ok": False, "error": "tunnel_disabled", "detail": "TELEGRAM_TUNNEL_ENABLED is false"}
    if not ngrok_available():
        return {"ok": False, "error": "ngrok_missing", "detail": "ngrok binary not found on PATH"}
    token = (settings.ngrok_authtoken or "").strip()
    if not token:
        return {"ok": False, "error": "token_missing", "detail": "NGROK_AUTHTOKEN not configured"}

    stop_ngrok()
    target_port = port or settings.ngrok_target_port or settings.api_port
    cmd = ["ngrok", "http", str(target_port), "--region", settings.ngrok_region or "us", "--log=stdout"]
    if settings.ngrok_domain.strip():
        cmd = ["ngrok", "http", f"--domain={settings.ngrok_domain.strip()}", str(target_port), "--log=stdout"]

    env = os.environ.copy()
    env["NGROK_AUTHTOKEN"] = token
    try:
        _NGROK_PROC = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
    except OSError as exc:
        return {"ok": False, "error": "start_failed", "detail": str(exc)}

    public_url = _wait_for_public_url(timeout_sec=12.0)
    if not public_url:
        stop_ngrok()
        return {"ok": False, "error": "url_timeout", "detail": "ngrok started but public URL not discovered"}
    return {"ok": True, "public_url": public_url, "local_port": target_port, "pid": _NGROK_PROC.pid}


def stop_ngrok() -> dict[str, Any]:
    global _NGROK_PROC
    if _NGROK_PROC and _NGROK_PROC.poll() is None:
        _NGROK_PROC.terminate()
        try:
            _NGROK_PROC.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _NGROK_PROC.kill()
    _NGROK_PROC = None
    return {"ok": True, "stopped": True}


def _wait_for_public_url(*, timeout_sec: float = 12.0) -> str | None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        url = _fetch_ngrok_public_url()
        if url:
            return url
        time.sleep(0.4)
    return None


def _fetch_ngrok_public_url() -> str | None:
    try:
        with httpx.Client(timeout=2.0) as client:
            r = client.get("http://127.0.0.1:4040/api/tunnels")
        if r.status_code >= 400:
            return None
        data = r.json()
        tunnels = data.get("tunnels") if isinstance(data, dict) else []
        for tunnel in tunnels or []:
            if not isinstance(tunnel, dict):
                continue
            public = str(tunnel.get("public_url") or "")
            if public.startswith("https://"):
                return public
        for tunnel in tunnels or []:
            public = str((tunnel or {}).get("public_url") or "")
            if public:
                return public
    except (httpx.HTTPError, ValueError, TypeError):
        return None
    return None


def is_running() -> bool:
    return _NGROK_PROC is not None and _NGROK_PROC.poll() is None
