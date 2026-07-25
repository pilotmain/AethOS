# SPDX-License-Identifier: Apache-2.0
"""Enterprise readiness API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["enterprise"])


class DemoAction(BaseModel):
    enabled: bool = True


class RecoveryAction(BaseModel):
    action: str = "telemetry_refresh"


@router.get("/enterprise/doctor")
def enterprise_doctor_api(category: str | None = None) -> dict[str, Any]:
    from aethos_core.enterprise.doctor import run_doctor_checks

    return run_doctor_checks(probe_api=False, probe_web=False, category=category)


@router.get("/enterprise/config")
def enterprise_config_api() -> dict[str, Any]:
    from aethos_core.enterprise.config_center import build_configuration_center

    return build_configuration_center()


@router.get("/enterprise/health")
def enterprise_health_api() -> dict[str, Any]:
    from aethos_core.enterprise.health_dashboard import build_operational_health_dashboard

    return build_operational_health_dashboard()


@router.get("/enterprise/setup-wizard")
def enterprise_setup_wizard_api() -> dict[str, Any]:
    from aethos_core.enterprise.setup_wizard import build_setup_wizard

    return build_setup_wizard()


@router.get("/enterprise/safe-defaults")
def enterprise_safe_defaults_api() -> dict[str, Any]:
    from aethos_core.enterprise.safe_defaults import audit_safe_defaults

    return audit_safe_defaults()


@router.get("/enterprise/demo")
def enterprise_demo_status_api() -> dict[str, Any]:
    from aethos_core.enterprise.demo_mode import demo_status, get_demo_overlay

    return {"ok": True, **demo_status(), "overlay": get_demo_overlay()}


@router.post("/enterprise/demo/enable")
def enterprise_demo_enable_api() -> dict[str, Any]:
    from aethos_core.enterprise.demo_mode import enable_demo_mode

    return enable_demo_mode()


@router.post("/enterprise/demo/disable")
def enterprise_demo_disable_api() -> dict[str, Any]:
    from aethos_core.enterprise.demo_mode import disable_demo_mode

    return disable_demo_mode()
