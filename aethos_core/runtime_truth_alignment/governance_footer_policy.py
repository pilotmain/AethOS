# SPDX-License-Identifier: Apache-2.0
"""FIX 316A — governance footer visibility policy."""

from __future__ import annotations

from typing import Any

_OPERATIONAL_ACTION_RX = __import__("re").compile(
    r"\b("
    r"deploy(?:ment)?|rollback|merge|rerun(?:\s+workflow)?|restart(?:\s+service)?"
    r"|provision|mutate|approve(?:\s+launch)?|execute(?:\s+job)?"
    r")\b",
    __import__("re").I,
)

_MUTATION_PREP_RX = __import__("re").compile(
    r"\b(preflight|approval(?:\s+required)?|mutation|execute(?:\s+this)?|run(?:\s+the)?\s+job)\b",
    __import__("re").I,
)

_GOVERNANCE_REVIEW_RX = __import__("re").compile(
    r"\b(governance\s+review|approval\s+inbox|review\s+decision|mission\s+control)\b",
    __import__("re").I,
)


def operational_action_detected(*, text: str = "", intent: str | None = None) -> bool:
    if intent in {
        "mutation_preflight",
        "operation_preflight",
        "tracked_job",
        "queued_tracked_job",
        "browser_evidence",
        "external_site_task",
        "action_status",
        "provider_job",
        "job_status",
        "mission_control_autonomous_capability_registry",
    }:
        return True
    if intent and intent.startswith("mission_control_"):
        return True
    if intent and intent.startswith("provider_execution"):
        return True
    return bool(_OPERATIONAL_ACTION_RX.search(text or ""))


def mutation_preparation_detected(*, text: str = "", intent: str | None = None) -> bool:
    if intent in {"mutation_preflight", "operation_preflight", "mutation_preflight_job_created"}:
        return True
    return bool(_MUTATION_PREP_RX.search(text or ""))


def governance_review_active(*, text: str = "", intent: str | None = None) -> bool:
    if intent and "governance" in intent:
        return True
    return bool(_GOVERNANCE_REVIEW_RX.search(text or ""))


def should_show_governance_footer(
    *,
    text: str = "",
    intent: str | None = None,
    meta: dict[str, Any] | None = None,
) -> bool:
    if meta and str(meta.get("suppress_governance_footer") or "").lower() == "true":
        return False
    if meta and str(meta.get("show_governance_footer") or "").lower() == "false":
        return False
    return (
        operational_action_detected(text=text, intent=intent)
        or mutation_preparation_detected(text=text, intent=intent)
        or governance_review_active(text=text, intent=intent)
    )
