# SPDX-License-Identifier: Apache-2.0
"""Trigger.dev config and runner mode resolution — Phase 11.8.1."""

from __future__ import annotations

from typing import Any


def trigger_settings() -> dict[str, Any]:
    from aethos_core.config import get_settings

    s = get_settings()
    return {
        "enabled": bool(getattr(s, "trigger_enabled", False)),
        "api_key": str(getattr(s, "trigger_api_key", "") or ""),
        "project_id": str(getattr(s, "trigger_project_id", "") or ""),
        "env": str(getattr(s, "trigger_env", "dev") or "dev"),
        "webhook_secret": str(getattr(s, "trigger_webhook_secret", "") or ""),
        "default_timeout_seconds": int(getattr(s, "trigger_default_timeout_seconds", 900) or 900),
        "max_retries": int(getattr(s, "trigger_max_retries", 3) or 3),
        "retry_backoff_seconds": int(getattr(s, "trigger_retry_backoff_seconds", 15) or 15),
        "stale_callback_minutes": int(getattr(s, "trigger_stale_callback_minutes", 10) or 10),
        "orphaned_job_minutes": int(getattr(s, "trigger_orphaned_job_minutes", 30) or 30),
    }


def resolve_runner_mode(*, api_reachable: bool | None = None) -> str:
    """embedded | external | degraded"""
    settings = trigger_settings()
    if not settings["enabled"]:
        return "embedded"
    if settings["api_key"] and settings["project_id"]:
        if api_reachable is False:
            return "degraded"
        return "external"
    return "degraded"
