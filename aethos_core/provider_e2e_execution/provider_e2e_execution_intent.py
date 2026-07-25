# SPDX-License-Identifier: Apache-2.0
"""Detect natural-language provider deploy + env + verify execution requests."""

from __future__ import annotations

import re
from typing import Literal

ProviderE2EKind = Literal["railway", "vercel"]

_ENV_RX = re.compile(
    r"\b("
    r"env(?:ironment)?(?:\s+vars?|\s+variables?)?"
    r"|config(?:ure|uration)?"
    r"|end[\s-]to[\s-]end"
    r"|e2e\b"
    r")\b",
    re.I,
)
_VERIFY_RX = re.compile(r"\b(verify|report back|health\s+check|final result)\b", re.I)
_RAILWAY_RX = re.compile(r"\b(?:railway|rail\s*way)\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)
_CAPABILITY_QUESTION_RX = re.compile(
    r"\b(can you|could you|would you|is it possible|do you support)\b.*\b(today|capable|support)\b",
    re.I,
)
_READONLY_LIST_INVENTORY_RX = re.compile(
    r"\b(list|show|all|every|each)\b.*\b(projects?|services?|apps?|inventory)\b",
    re.I,
)
_READONLY_DEPLOYMENT_INSPECT_RX = re.compile(
    r"\bdeployment\s+(health|status)\b"
    r"|\b(health|status)\b.*\b(for\s+)?(each|every|all)\b"
    r"|\b(show|list)\b.*\b(health|status)\b",
    re.I,
)
_MUTATION_DEPLOY_RX = re.compile(
    r"\b("
    r"redeploy"
    r"|deploy(?:ment)?\s+(?:and|then|with|to|on|from)"
    r"|deploy\b"
    r")\b",
    re.I,
)


def _normalized(text: str) -> str:
    return (text or "").strip()


def _is_deployment_inspection_only(raw: str) -> bool:
    return bool(_READONLY_DEPLOYMENT_INSPECT_RX.search(raw))


def _has_mutation_deploy_intent(raw: str) -> bool:
    if _is_deployment_inspection_only(raw):
        return False
    return bool(_MUTATION_DEPLOY_RX.search(raw))


def is_provider_readonly_orchestration_intent(text: str) -> bool:
    """Readonly list/inspect/health across providers — not deploy+env E2E execution."""
    raw = _normalized(text)
    if not raw:
        return False
    if not (_RAILWAY_RX.search(raw) or _VERCEL_RX.search(raw)):
        return False
    if _has_mutation_deploy_intent(raw) and (_ENV_RX.search(raw) or _VERIFY_RX.search(raw)):
        return False
    if _READONLY_LIST_INVENTORY_RX.search(raw):
        return True
    if _is_deployment_inspection_only(raw):
        return True
    return False


def is_provider_e2e_execution_intent(text: str) -> bool:
    """Deploy + provider + (env configuration or verify) — execution, not pure capability Q."""
    raw = _normalized(text)
    if not raw or _CAPABILITY_QUESTION_RX.search(raw):
        return False
    if is_provider_readonly_orchestration_intent(raw):
        return False
    from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
        is_railway_greenfield_deployment_intent,
    )

    if is_railway_greenfield_deployment_intent(raw):
        return False
    provider = detect_provider_e2e_kind(raw)
    if provider is None:
        return False
    has_deploy = _has_mutation_deploy_intent(raw)
    has_env = bool(_ENV_RX.search(raw))
    has_verify = bool(_VERIFY_RX.search(raw))
    return has_deploy and (has_env or has_verify)


def detect_provider_e2e_kind(text: str) -> ProviderE2EKind | None:
    raw = _normalized(text)
    if not raw:
        return None
    if is_provider_readonly_orchestration_intent(raw):
        return None
    railway = bool(_RAILWAY_RX.search(raw) and _has_mutation_deploy_intent(raw))
    vercel = bool(_VERCEL_RX.search(raw) and _has_mutation_deploy_intent(raw))
    if railway and vercel:
        return None
    if railway:
        return "railway"
    if vercel:
        return "vercel"
    return None
