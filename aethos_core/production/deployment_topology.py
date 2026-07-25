# SPDX-License-Identifier: Apache-2.0
"""Production deployment topology and runtime model."""

from __future__ import annotations

import os
import platform
from time import time
from typing import Any

from aethos_core.config import get_settings


DEPLOYMENT_MODES = frozenset({"local", "team", "enterprise", "edge", "hosted"})


def get_deployment_topology() -> dict[str, Any]:
    """Official production deployment topology snapshot."""
    s = get_settings()
    mode = _deployment_mode()
    worker_mode = getattr(s, "worker_mode", "embedded") or "embedded"

    services = {
        "web": {"role": "Mission Control UI", "required": mode != "edge", "port": 3000},
        "api": {"role": "FastAPI orchestration authority", "required": True, "port": s.api_port},
        "workers": {"role": "Async job/browser/validation workers", "required": worker_mode == "standalone", "isolated": True},
        "scheduler": {"role": "Observation + presence cycles", "required": True, "embedded_in": "api" if worker_mode == "embedded" else "worker"},
        "browser_runtime": {"role": "Governed browser evidence", "required": s.browser_automation_enabled, "isolated": True},
        "artifact_storage": {"role": "Persistent evidence/artifacts", "required": True, "path": s.agent_artifacts_dir},
        "vault": {"role": "Encrypted credential vault", "required": True, "path": s.credentials_dir},
        "queue": {"role": "Job/worker queue", "backend": _queue_backend_label()},
        "observability": {"role": "Metrics/traces/logs", "endpoint": "/api/v1/observability/metrics"},
    }

    return {
        "ok": True,
        "deployment_mode": mode,
        "worker_mode": worker_mode,
        "app_env": s.app_env,
        "topology_version": "9.9",
        "services": services,
        "runtime_components": list(services.keys()),
        "ha_ready": mode in ("enterprise", "hosted"),
        "edge_capable": mode == "edge" or getattr(s, "edge_runtime_enabled", False),
        "checked_at": time(),
        "host": platform.node(),
        "pid": os.getpid(),
        "readonly": True,
    }


def validate_production_environment() -> dict[str, Any]:
    """Validate production environment requirements."""
    s = get_settings()
    issues: list[str] = []
    warnings: list[str] = []

    if s.app_env == "production":
        if not s.web_api_token.strip():
            issues.append("WEB_API_TOKEN required in production")
        if s.host_executor_enabled:
            issues.append("HOST_EXECUTOR_ENABLED must be false in production")
        if s.mutation_t3_production_enabled and s.mutation_execution_enabled:
            warnings.append("T3 production mutations enabled — ensure governance review")

    if _deployment_mode() in ("team", "enterprise", "hosted"):
        if not Path_exists(s.agent_artifacts_dir):
            issues.append(f"Artifact directory missing: {s.agent_artifacts_dir}")

    from aethos_core.enterprise.safe_defaults import audit_safe_defaults

    safe = audit_safe_defaults()
    if not safe.get("ok"):
        issues.extend(safe.get("violations") or [])

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "deployment_mode": _deployment_mode(),
        "validated_at": time(),
    }


def _deployment_mode() -> str:
    s = get_settings()
    mode = (getattr(s, "deployment_mode", None) or os.environ.get("DEPLOYMENT_MODE") or "local").lower()
    return mode if mode in DEPLOYMENT_MODES else "local"


def _queue_backend_label() -> str:
    try:
        from aethos_core.runtime.distributed.queue_backend import get_queue_backend

        return get_queue_backend().backend_name
    except Exception:
        return "in_memory"


def Path_exists(path: str) -> bool:
    from pathlib import Path

    return Path(path).is_dir()
