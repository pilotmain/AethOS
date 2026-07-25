# SPDX-License-Identifier: Apache-2.0
"""Startup guard — hosted deploys must use a cross-process shared store backend."""

from __future__ import annotations

import logging
import os

_log = logging.getLogger(__name__)

_SURFACE_NAMES = (
    "canvas",
    "workspace documents",
    "notes/tasks",
    "session aliases",
)


def validate_hosted_shared_stores_at_startup() -> None:
    """Warn or fail when hosted mode cannot share state across api/worker/replicas."""
    from aethos_core.production.deployment_mode import is_hosted_deployment

    if not is_hosted_deployment():
        return

    from aethos_core.config import get_settings
    from aethos_core.tenancy.tenant_data_store import shared_store_backend_label

    backend = shared_store_backend_label()
    if backend == "postgres":
        _log.info("hosted shared store backend=postgres (DATABASE_URL)")
        return

    settings = get_settings()
    worker_mode = str(getattr(settings, "worker_mode", "embedded") or "embedded")
    multi_process = (
        bool(getattr(settings, "durable_agent_jobs_enabled", False))
        or worker_mode == "standalone"
    )
    tenant_data_dir = str(os.environ.get("TENANT_DATA_DIR", "") or "").strip()
    if not multi_process and tenant_data_dir:
        _log.info(
            "hosted shared store backend=%s TENANT_DATA_DIR=%s (single-process or shared volume)",
            backend,
            tenant_data_dir,
        )
        return

    surfaces = ", ".join(_SURFACE_NAMES)
    msg = (
        f"DEPLOYMENT_MODE=hosted without DATABASE_URL: {surfaces} use backend={backend!r} "
        "on process-local disk. Writes in the worker (or another API replica) will NOT be visible "
        "to GET handlers in the API process — Canvas will stay empty after a successful render. "
        "Provision Postgres, set DATABASE_URL on every api/worker service, and redeploy."
    )
    strict = str(os.environ.get("HOSTED_SHARED_STORE_STRICT", "") or "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    if strict:
        raise RuntimeError(msg)
    _log.critical(msg)
