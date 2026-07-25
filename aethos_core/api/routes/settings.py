# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter

from aethos_core.api.provider_readiness import build_provider_readiness
from aethos_core.config import get_settings
from aethos_core.provider.completion import provider_configured
from aethos_core.runtime.browser_capability import get_browser_capability_status
from aethos_core.runtime.workspace_diagnostics import get_workspace_diagnostics

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings_summary() -> dict[str, object]:
    """Deployment settings snapshot — observational only."""
    s = get_settings()
    configured = provider_configured()
    workspace = get_workspace_diagnostics()
    browser_capability: dict[str, object]
    try:
        browser_capability = get_browser_capability_status(probe_launch=False)
    except Exception as exc:
        from aethos_core.runtime.browser_profile_store import profile_store_startup_info

        browser_capability = {
            "enabled": s.browser_automation_enabled,
            "execution_ready": False,
            "execution_label": f"Diagnostics unavailable: {exc}",
            "user_message": str(exc),
            "diagnostics": {"launch_probe_error": str(exc), "execution_ready": False},
            **profile_store_startup_info(),
        }
    return {
        "response_mode": "deterministic_first",
        "use_real_llm": s.use_real_llm,
        "active_provider": s.active_provider,
        "model": s.anthropic_model,
        "provider_ready": configured,
        "browser_automation_enabled": s.browser_automation_enabled,
        "host_executor_enabled": s.host_executor_enabled,
        "browser_capability": browser_capability,
        "workspace": workspace,
        "build": {
            "commit": workspace.get("build_commit"),
            "api_process_started_at": workspace.get("api_process_started_at"),
            "web_build_timestamp": None,
        },
    }


@router.get("/settings/provider")
def get_provider_settings() -> dict[str, object]:
    """Provider readiness for Mission Control — does not affect chat."""
    get_settings()
    return build_provider_readiness()
