# SPDX-License-Identifier: Apache-2.0
"""Execution goal detection — what the user is trying to accomplish."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

ProviderGoal = Literal["railway", "vercel"]
GoalAction = Literal["deploy", "configure_env", "verify", "full_e2e"]

_RAILWAY_RX = re.compile(r"\b(?:railway|rail\s*way)\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)
_DEPLOY_RX = re.compile(r"\b(deploy(?:ment)?|redeploy)\b", re.I)
_ENV_RX = re.compile(
    r"\b(env(?:ironment)?(?:\s+vars?|\s+variables?)?|config(?:ure|uration)?|end[\s-]to[\s-]end|e2e\b)\b",
    re.I,
)
_VERIFY_RX = re.compile(r"\b(verify|report back|health(?:\s+check)?|final result)\b", re.I)
_READINESS_ONLY_RX = re.compile(
    r"\b("
    r"ready\s+(?:to\s+)?deploy|ready\s+for\s+\w+\s+deployment|deployment\s+readiness"
    r"|what\s+is\s+blocking|is\s+(?:the\s+)?\w+\s+service\s+configured"
    r"|check\s+(?:if\s+)?(?:aethos\s+is\s+)?ready"
    r")\b",
    re.I,
)
_CAPABILITY_QUESTION_RX = re.compile(
    r"\b(can you|could you|would you|is it possible|do you support)\b.*\b(today|capable|support)\b",
    re.I,
)


@dataclass(frozen=True)
class ExecutionGoal:
    provider: ProviderGoal
    action: GoalAction
    user_text: str
    requires_env: bool
    requires_verify: bool
    target_hint: str = "aethos"


def _normalized(text: str) -> str:
    return (text or "").strip()


def detect_execution_goal(text: str) -> ExecutionGoal | None:
    """Detect provider execution goals — not pure readiness inspection."""
    raw = _normalized(text)
    if not raw or _CAPABILITY_QUESTION_RX.search(raw):
        return None

    from aethos_core.chat.provider_deploy_capability_intent import detect_provider_deploy_env_capability

    if detect_provider_deploy_env_capability(raw) and re.match(
        r"^(?:can you|could you|would you|is it possible|do you support)\b",
        raw,
        re.I,
    ):
        return None

    if _READINESS_ONLY_RX.search(raw) and not _DEPLOY_RX.search(raw):
        return None

    from aethos_core.provider_e2e_readiness.readiness_intent import is_provider_e2e_readiness_intent

    if is_provider_e2e_readiness_intent(raw):
        return None

    from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
        is_railway_greenfield_deployment_intent,
    )

    if is_railway_greenfield_deployment_intent(raw):
        return None

    from aethos_core.provider_e2e_execution.provider_e2e_execution_intent import (
        is_provider_readonly_orchestration_intent,
    )

    if is_provider_readonly_orchestration_intent(raw):
        return None

    railway = bool(_RAILWAY_RX.search(raw))
    vercel = bool(_VERCEL_RX.search(raw))
    if railway and vercel:
        return None
    if not railway and not vercel:
        return None

    provider: ProviderGoal = "railway" if railway else "vercel"
    has_deploy = bool(_DEPLOY_RX.search(raw))
    has_env = bool(_ENV_RX.search(raw))
    has_verify = bool(_VERIFY_RX.search(raw))

    if not has_deploy and not has_env:
        return None

    if has_deploy and (has_env or has_verify):
        action: GoalAction = "full_e2e"
    elif has_deploy:
        action = "deploy"
    elif has_env:
        action = "configure_env"
    else:
        action = "verify"

    return ExecutionGoal(
        provider=provider,
        action=action,
        user_text=raw,
        requires_env=has_env,
        requires_verify=has_verify,
    )


def is_execution_brain_goal(text: str) -> bool:
    from aethos_core.providers.railway.greenfield_deployment.deployment_status_followup_router import (
        is_railway_deployment_status_followup,
    )
    from aethos_core.providers.railway.greenfield_deployment.greenfield_deploy_component import (
        is_additional_railway_service_deploy_request,
    )
    from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
        is_railway_greenfield_deployment_intent,
    )

    if is_railway_deployment_status_followup(text):
        return False
    if is_railway_greenfield_deployment_intent(text):
        return False
    if is_additional_railway_service_deploy_request(text) and re.search(r"\brailway\b", text or "", re.I):
        return False
    return detect_execution_goal(text) is not None
