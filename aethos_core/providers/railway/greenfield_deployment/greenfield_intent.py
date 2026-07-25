# SPDX-License-Identifier: Apache-2.0
"""Deterministic Railway greenfield deployment intent detection."""

from __future__ import annotations

import re

_RAILWAY_RX = re.compile(r"\b(?:railway|rail\s*way)\b", re.I)
_DEPLOY_RX = re.compile(r"\b(deploy(?:ment)?|redeploy)\b", re.I)
_DEPLOY_TO_RAILWAY_RX = re.compile(
    r"\bdeploy\b.+\b(?:to|on)\s+railway\b|\bdeploy\b.+\brailway\b.*\b(?:env|verify)\b",
    re.I,
)
_CREATE_PROJECT_RX = re.compile(
    r"\b(?:create|make|provision)\s+(?:a\s+)?(?:new\s+)?(?:railway\s+)?(?:project|service)\b"
    r"|\bnew\s+(?:railway\s+)?(?:project|service)\b"
    r"|\bcreate\s+(?:a\s+)?new\s+project\s+in\s+railway\b",
    re.I,
)
_LOCAL_WORKSPACE_RX = re.compile(
    r"\b("
    r"local\s+work\s*space"
    r"|local\s+workspace"
    r"|check\s+local"
    r"|this\s+(?:repo|workspace|project)"
    r"|from\s+local"
    r")\b",
    re.I,
)
_GREENFIELD_SIGNAL_RX = re.compile(
    r"\b("
    r"new\s+project"
    r"|greenfield"
    r"|create\s+(?:it\s+)?in\s+railway"
    r"|get\s+(?:its\s+)?(?:remote\s+)?git"
    r"|remote\s+git"
    r"|check\s+local"
    r"|deploy\s+from\s+local"
    r"|set\s+(?:all\s+)?required\s+env"
    r"|report\s+back"
    r"|new\s+railway\s+service"
    r"|no\s+existing\s+railway\s+service"
    r")\b",
    re.I,
)
_STRONG_GREENFIELD_RX = re.compile(
    r"\b("
    r"new\s+project"
    r"|greenfield"
    r"|create\s+(?:a\s+)?new\s+project"
    r"|create\s+(?:it\s+)?in\s+railway"
    r"|get\s+(?:its\s+)?(?:remote\s+)?git"
    r"|remote\s+git"
    r"|check\s+local"
    r"|local\s+work\s*space"
    r"|local\s+workspace"
    r"|deploy\s+from\s+local"
    r"|new\s+railway\s+service"
    r"|no\s+existing\s+railway\s+service"
    r")\b",
    re.I,
)
_EXISTING_SERVICE_RX = re.compile(
    r"\b(?:existing|current)\s+(?:railway\s+)?service\b|\bredeploy\s+(?:the\s+)?(?:existing\s+)?(?:railway\s+)?\w+\s+service\b",
    re.I,
)
_SHOW_PROJECTS_RX = re.compile(r"\bshow\s+railway\s+projects?\b", re.I)
_READINESS_ONLY_RX = re.compile(
    r"\b("
    r"railway\s+deployment\s+readiness"
    r"|check\s+railway\s+(?:deployment\s+)?readiness"
    r"|validate\s+railway\s+(?:connection|credential)"
    r"|is\s+railway\s+ready"
    r")\b",
    re.I,
)
_RECALL_INVESTIGATION_RX = re.compile(
    r"\b("
    r"recall\s+(?:the\s+)?(?:\w+\s+)?investigation"
    r"|remember\s+(?:the\s+)?investigation"
    r"|what\s+do\s+we\s+know\s+about"
    r"|previous\s+(?:railway\s+)?incident"
    r")\b",
    re.I,
)
_LOGS_ONLY_RX = re.compile(
    r"^(?:fetch|show|get|tail)\s+(?:the\s+)?(?:\w+\s+)?(?:logs?|events?)\b",
    re.I,
)


def is_railway_greenfield_deployment_intent(text: str) -> bool:
    """
    Greenfield: create new Railway project/service from local workspace / git remote.

    Must not match pure existing-service redeploy, inventory, readiness-only, or recall prompts.
    """
    raw = (text or "").strip()
    if not raw or not _RAILWAY_RX.search(raw):
        return False

    if _SHOW_PROJECTS_RX.search(raw):
        return False
    if _LOGS_ONLY_RX.search(raw):
        return False

    has_deploy = bool(_DEPLOY_RX.search(raw))
    has_create = bool(_CREATE_PROJECT_RX.search(raw))
    has_local = bool(_LOCAL_WORKSPACE_RX.search(raw))
    has_greenfield_signal = bool(_GREENFIELD_SIGNAL_RX.search(raw))
    has_strong_greenfield = bool(_STRONG_GREENFIELD_RX.search(raw))
    has_git = "git" in raw.lower()
    has_env = bool(re.search(r"\benv(?:ironment)?(?:\s+vars?|\s+variables?)?\b", raw, re.I))
    has_verify = bool(re.search(r"\bverify\b", raw, re.I))

    if _RECALL_INVESTIGATION_RX.search(raw) and not (has_create or has_local or has_greenfield_signal):
        return False
    if _READINESS_ONLY_RX.search(raw) and not (has_create or has_deploy or has_local):
        return False
    if _EXISTING_SERVICE_RX.search(raw) and not (has_create and has_local):
        return False

    if has_create and _RAILWAY_RX.search(raw):
        return True
    if has_local and (has_deploy or has_create or has_git):
        return True
    if has_strong_greenfield and (has_deploy or has_create or has_local or has_git or has_env):
        return True
    if has_greenfield_signal and has_strong_greenfield and (has_deploy or has_env):
        return True
    if "new project" in raw.lower() and _RAILWAY_RX.search(raw) and (
        has_deploy or has_env or has_git or has_local or "workspace" in raw.lower()
    ):
        return True
    if (
        has_deploy
        and _RAILWAY_RX.search(raw)
        and (has_env or has_verify)
        and _DEPLOY_TO_RAILWAY_RX.search(raw)
        and not _EXISTING_SERVICE_RX.search(raw)
    ):
        return True

    from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import (
        is_additional_railway_service_deploy_request,
    )

    if has_deploy and _RAILWAY_RX.search(raw) and is_additional_railway_service_deploy_request(raw):
        return True
    if has_deploy and _RAILWAY_RX.search(raw) and _DEPLOY_TO_RAILWAY_RX.search(raw):
        from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import (
            detect_greenfield_deploy_component,
        )

        if detect_greenfield_deploy_component(raw) == "ui":
            return True
    return False


def greenfield_intent_debug_metadata(text: str, *, debug_enabled: bool = False) -> dict[str, str]:
    """Optional routing diagnostics — regex details only when debug is enabled."""
    meta: dict[str, str] = {
        "intent": "railway_greenfield_deployment_flow",
        "route_precedence": "greenfield_before_operational_recall",
        "matched": "true" if is_railway_greenfield_deployment_intent(text) else "false",
    }
    if debug_enabled:
        meta["railway_token_present"] = "true" if _RAILWAY_RX.search(text or "") else "false"
        meta["create_project_signal"] = "true" if _CREATE_PROJECT_RX.search(text or "") else "false"
        meta["local_workspace_signal"] = "true" if _LOCAL_WORKSPACE_RX.search(text or "") else "false"
    return meta
