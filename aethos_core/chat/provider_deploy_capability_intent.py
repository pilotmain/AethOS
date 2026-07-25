# SPDX-License-Identifier: Apache-2.0
"""Provider deploy+env natural-language capability routing — audit-backed truth only."""

from __future__ import annotations

import re
from typing import Literal

ProviderDeployKind = Literal["railway", "vercel"]

_DEPLOY_RX = re.compile(r"\b(deploy(?:ment)?|redeploy)\b", re.I)
_ENV_RX = re.compile(
    r"\b("
    r"env(?:ironment)?(?:\s+vars?|\s+variables?)?"
    r"|config(?:ure|uration)?"
    r"|end[\s-]to[\s-]end"
    r"|e2e\b"
    r")\b",
    re.I,
)
_RAILWAY_RX = re.compile(r"\b(?:railway|rail\s*way)\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)


def _normalized(text: str) -> str:
    return (text or "").strip()


def is_railway_deploy_env_capability_intent(text: str) -> bool:
    raw = _normalized(text)
    return bool(raw and _RAILWAY_RX.search(raw) and _DEPLOY_RX.search(raw) and _ENV_RX.search(raw))


def is_vercel_deploy_env_capability_intent(text: str) -> bool:
    raw = _normalized(text)
    return bool(raw and _VERCEL_RX.search(raw) and _DEPLOY_RX.search(raw) and _ENV_RX.search(raw))


def detect_provider_deploy_env_capability(text: str) -> ProviderDeployKind | None:
    raw = _normalized(text)
    if not raw:
        return None
    railway = is_railway_deploy_env_capability_intent(raw)
    vercel = is_vercel_deploy_env_capability_intent(raw)
    if railway and vercel:
        return None
    if railway:
        return "railway"
    if vercel:
        return "vercel"
    return None


def _capability_meta(*, provider: ProviderDeployKind, intent: str) -> dict[str, str]:
    return {
        "route_id": f"{provider}_deploy_capability_truth",
        "matched_module": "chat.provider_deploy_capability_intent",
        "provider": provider,
        "devops_request_kind": intent,
        "suppress_governance_footer": "true",
        "readonly": "true",
        "mutation_performed": "false",
        "execution_enabled": "false",
        "capability_truth_only": "true",
    }


def route_provider_deploy_capability_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Return deploy+env capability answer — E2E orchestration first, truth fallback."""
    from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
        is_railway_greenfield_deployment_intent,
    )

    if is_railway_greenfield_deployment_intent(text):
        return None

    from aethos_core.provider_e2e_execution.provider_e2e_execution_service import route_provider_e2e_execution

    e2e = route_provider_e2e_execution(text, session_id=session_id)
    if e2e is not None:
        return e2e

    provider = detect_provider_deploy_env_capability(text)
    if provider is None:
        return None
    if provider == "railway":
        from aethos_core.chat.handlers import deploy_railway_reply

        return deploy_railway_reply(), "railway_deploy_capability_truth", _capability_meta(
            provider="railway",
            intent="railway_deploy_capability_truth",
        )
    from aethos_core.chat.handlers import deploy_vercel_reply

    return deploy_vercel_reply(), "vercel_deploy_capability_truth", _capability_meta(
        provider="vercel",
        intent="vercel_deploy_capability_truth",
    )
