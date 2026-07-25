# SPDX-License-Identifier: Apache-2.0
"""DevOps request classifier — capability truth vs plan-first end-to-end workflows."""

from __future__ import annotations

import re
from typing import Literal

DevopsRequestKind = Literal[
    "capability_truth",
    "end_to_end_plan",
    "clear_single_mutation",
    "none",
]

_CAPABILITY_TRUTH_RX = re.compile(
    r"\b("
    r"which\s+(?:cloud(?:\s+env|\s+environment)?|provider|providers)"
    r"|what\s+(?:cloud|providers?).*(?:support|implement|work|capable|wired)"
    r"|work\s+(?:end[\s-]to[\s-]end|e2e)\s+today"
    r"|end[\s-]to[\s-]end\s+today"
    r"|most\s+complete\s+(?:provider|cloud)"
    r"|fully\s+(?:wired|implemented|supported|working)"
    r"|honest(?:ly)?\s+about\s+(?:your\s+)?capabilit"
    r")\b",
    re.I,
)

_CAN_YOU_RX = re.compile(r"\b(can you|could you|would you|help me|i need you to)\b", re.I)

_LOCAL_DEVOPS_RX = re.compile(
    r"\b("
    r"push\s+(?:to\s+)?github"
    r"|push\s+(?:the\s+)?(?:changes?|repo)"
    r"|commit\s+(?:and\s+)?push"
    r"|deploy\s+this\s+repo"
    r"|create\s+env(?:ironment)?\s+vars?"
    r"|set\s+env(?:ironment)?\s+vars?"
    r"|check\s+(?:the\s+)?(?:deployment\s+)?e2e"
    r"|end[\s-]to[\s-]end"
    r"|e2e\b"
    r")\b",
    re.I,
)

_UNIMPLEMENTED_PROVIDER_RX = re.compile(r"\b(aws|gcp|azure|kubernetes|k8s)\b", re.I)


def is_capability_truth_question(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _CAPABILITY_TRUTH_RX.search(raw):
        return True
    if re.search(r"\bwhich cloud\b", raw, re.I) and re.search(r"\b(work|support|end|capable|today)\b", raw, re.I):
        return True
    return False


def count_devops_actions(text: str) -> int:
    lower = (text or "").lower()
    count = 0
    if re.search(r"\bpush\b", lower):
        count += 1
    if re.search(r"\bdeploy\b", lower):
        count += 1
    if re.search(r"\b(env(?:ironment)?\s+var|env\s+vars?|set\s+\w+\s+(?:env|variable))\b", lower):
        count += 1
    if re.search(r"\b(end[\s-]to[\s-]end|e2e|check\s+(?:the\s+)?deployment)\b", lower):
        count += 1
    return count


def is_end_to_end_devops_request(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw or is_capability_truth_question(raw):
        return False

    actions = count_devops_actions(raw)
    if actions >= 2:
        return True

    if _LOCAL_DEVOPS_RX.search(raw) and _CAN_YOU_RX.search(raw):
        return not has_clear_devops_mutation_target(raw, session_id=session_id)

    if _CAN_YOU_RX.search(raw) and actions >= 1 and _mentions_unimplemented_provider(raw):
        return True

    if re.search(r"\bpush\b.*\bdeploy\b", raw, re.I):
        return True

    return False


def _mentions_unimplemented_provider(text: str) -> bool:
    if not _UNIMPLEMENTED_PROVIDER_RX.search(text or ""):
        return False
    from aethos_core.capability_truth.adapter_readiness import check_adapter_readiness

    for match in _UNIMPLEMENTED_PROVIDER_RX.finditer(text or ""):
        provider = match.group(1).lower()
        if provider == "k8s":
            provider = "kubernetes"
        status = check_adapter_readiness(provider)
        if not status.operational:
            return True
    return False


def has_clear_devops_mutation_target(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False

    if count_devops_actions(raw) > 1:
        return False

    if _LOCAL_DEVOPS_RX.search(raw):
        return False

    from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent

    intent = detect_explicit_mutation_intent(raw, session_id=session_id)
    if intent is not None and intent.confidence >= 0.75:
        return True

    from aethos_core.operations.intents import infer_operation_preflight_intent

    inferred = infer_operation_preflight_intent(raw, session_id=session_id)
    if inferred is None:
        return False
    params = inferred[2]
    operation_type = str(params.get("operation_type") or "")
    if operation_type.startswith("local_") or operation_type in {"git_deploy_preflight", "provider_ambiguity"}:
        return False
    if operation_type in {"restart", "redeploy", "workflow_rerun", "set_env_var"}:
        # target_hints may arrive as a dict or (defensively) a string — only a dict carries
        # service/project hints; anything else means "no clear target". dict("abc") raises.
        raw_hints = params.get("target_hints")
        hints = raw_hints if isinstance(raw_hints, dict) else {}
        if hints.get("service") or hints.get("service_name") or hints.get("project") or hints.get("project_name"):
            return True
        if str(params.get("target_name") or "").strip():
            return True
    return False


def should_block_mutation_preflight(text: str, *, session_id: str = "default") -> bool:
    if is_capability_truth_question(text):
        return True
    from aethos_core.providers.railway.deployment_plan.creation_preflight_intent import (
        is_railway_service_creation_preflight_intent,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_intent import (
        is_railway_new_service_plan_intent,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_intent import (
        is_railway_service_creation_simulator_intent,
    )

    if is_railway_new_service_plan_intent(text):
        return True
    if is_railway_service_creation_preflight_intent(text):
        return True
    if is_railway_service_creation_simulator_intent(text):
        return True
    if is_end_to_end_devops_request(text, session_id=session_id):
        return True
    return False


def should_defer_to_devops_plan(text: str, *, session_id: str = "default") -> bool:
    return should_block_mutation_preflight(text, session_id=session_id)


def classify_devops_request(text: str, *, session_id: str = "default") -> DevopsRequestKind:
    if is_capability_truth_question(text):
        return "capability_truth"
    if is_end_to_end_devops_request(text, session_id=session_id):
        return "end_to_end_plan"
    if has_clear_devops_mutation_target(text, session_id=session_id):
        return "clear_single_mutation"
    return "none"


def detect_requested_providers(text: str) -> list[str]:
    found: list[str] = []
    for provider in ("railway", "vercel", "github", "aws", "gcp", "azure", "kubernetes"):
        if re.search(rf"\b{re.escape(provider)}\b", text or "", re.I):
            found.append(provider)
    if re.search(r"\bk8s\b", text or "", re.I) and "kubernetes" not in found:
        found.append("kubernetes")
    return found
