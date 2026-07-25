# SPDX-License-Identifier: Apache-2.0
"""Plugins API — governed extension SDK."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["plugins"])


class EnablePluginRequest(BaseModel):
    plugin_id: str


@router.get("/plugins")
def plugins_list_api() -> dict[str, Any]:
    from aethos_sdk.plugin_registry import list_plugins

    return {"ok": True, "plugins": list_plugins(), "autonomous_execution_blocked": True}


@router.post("/plugins/enable")
def plugins_enable_api(body: EnablePluginRequest) -> dict[str, Any]:
    from aethos_sdk.plugin_registry import enable_plugin

    result = enable_plugin(body.plugin_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.get("/upgrade/status")
def upgrade_status_api() -> dict[str, Any]:
    from aethos_core.runtime.resilience.upgrade_manager import check_upgrade_compatibility

    return check_upgrade_compatibility()


@router.post("/upgrade/run")
def upgrade_run_api() -> dict[str, Any]:
    from aethos_core.runtime.resilience.upgrade_manager import run_upgrade

    return run_upgrade()


@router.post("/upgrade/rollback")
def upgrade_rollback_api() -> dict[str, Any]:
    from aethos_core.runtime.resilience.upgrade_manager import rollback_upgrade

    result = rollback_upgrade()
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.get("/upgrade/config-migration")
def config_migration_api() -> dict[str, Any]:
    from aethos_core.runtime.resilience.config_migration import analyze_env_migration

    return analyze_env_migration()
