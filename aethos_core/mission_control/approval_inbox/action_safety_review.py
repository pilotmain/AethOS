# SPDX-License-Identifier: Apache-2.0
"""FIX 134 — static safety review for Mission Control UI approval path."""

from __future__ import annotations

import inspect
from typing import Any

from aethos_core.mission_control.approval_inbox.action_safety_contract import (
    ACTION_SAFETY_FIX,
    ACTION_SAFETY_SCHEMA_VERSION,
    FORBIDDEN_DIRECT_PROVIDER_CALLS,
    FORBIDDEN_MC_UI_CONTROLS_FIX_134,
    REQUIRED_UI_APPROVAL_ENTRYPOINT,
)


def review_mission_control_ui_action_safety() -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox import approval_execution_service as exec_mod

    source = inspect.getsource(exec_mod.execute_governed_ui_approval)
    violations = [sym for sym in FORBIDDEN_DIRECT_PROVIDER_CALLS if sym in source]
    has_chat = REQUIRED_UI_APPROVAL_ENTRYPOINT in source

    api_source = ""
    try:
        from aethos_core.api.routes import mission_control as mc_routes

        api_source = inspect.getsource(mc_routes.mission_control_approval_inbox_execute_api)
    except (TypeError, OSError):
        api_source = ""

    api_violations = [sym for sym in FORBIDDEN_DIRECT_PROVIDER_CALLS if sym in api_source]

    return {
        "ok": len(violations) == 0 and len(api_violations) == 0 and has_chat,
        "schema_version": ACTION_SAFETY_SCHEMA_VERSION,
        "fix": ACTION_SAFETY_FIX,
        "chat_governance_entrypoint": REQUIRED_UI_APPROVAL_ENTRYPOINT,
        "execution_path_violations": violations,
        "api_route_violations": api_violations,
        "forbidden_ui_controls": list(FORBIDDEN_MC_UI_CONTROLS_FIX_134),
        "invariant": "mission_control_ui_never_calls_provider_mutation_apis_directly",
    }
