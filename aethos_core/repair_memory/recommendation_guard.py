# SPDX-License-Identifier: Apache-2.0
"""Guard recommendations after failed repair attempts."""

from __future__ import annotations

import re

from aethos_core.repair_memory.historical_repair_lookup import lookup_latest_failed_restart
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome
from aethos_core.world_model.investigation_state import InvestigationState

_DEEPER_EVIDENCE_ACTION = (
    "Inspect deeper failure evidence:\n"
    "1. fetch full failure-window logs\n"
    "2. inspect Railway service events / exit reason\n"
    "3. check volume/storage state"
)

_RESTART_AGAIN_RX = re.compile(
    r"\b("
    r"should\s+we\s+restart\s+again"
    r"|restart\s+again"
    r"|another\s+restart"
    r"|repeat\s+(?:the\s+)?restart"
    r")\b",
    re.I,
)

_DID_RESTART_HELP_RX = re.compile(
    r"\b("
    r"did\s+(?:the\s+)?restart\s+help"
    r"|did\s+restart\s+help"
    r"|did\s+it\s+help"
    r")\b",
    re.I,
)


def _service_from_state(state: InvestigationState) -> str:
    return state.service or state.target.split("/")[-1].strip() or "the service"


def _target_from_state(state: InvestigationState) -> str:
    if state.project and state.environment and state.service:
        return f"{state.project} / {state.environment} / {state.service}"
    return state.target or state.service or ""


def resolve_failed_restart_for_state(state: InvestigationState) -> RepairAttemptOutcome | None:
    return lookup_latest_failed_restart(
        target_path=_target_from_state(state) or None,
        service=state.service or None,
    )


def should_block_restart_recommendation(state: InvestigationState) -> bool:
    return resolve_failed_restart_for_state(state) is not None


def is_restart_again_question(text: str) -> bool:
    return bool(_RESTART_AGAIN_RX.search(text or ""))


def is_did_restart_help_question(text: str) -> bool:
    return bool(_DID_RESTART_HELP_RX.search(text or ""))


def compose_next_step_with_repair_guard(state: InvestigationState, base_reply: str) -> str:
    failed = resolve_failed_restart_for_state(state)
    if failed is None:
        return base_reply
    service = _service_from_state(state)
    lines = [
        f"The restart did not resolve **{service}** — health is still **{failed.health_after}** after the mutation.",
        "",
        "I would not repeat the restart right now.",
        "",
        "Next best action:",
        _DEEPER_EVIDENCE_ACTION,
    ]
    return "\n".join(lines)


def compose_restart_again_reply(state: InvestigationState) -> str | None:
    failed = resolve_failed_restart_for_state(state)
    if failed is None:
        return None
    service = _service_from_state(state)
    return "\n".join(
        [
            "No — not yet.",
            "",
            f"We already restarted **{service}** and it remained **{failed.health_after}**.",
            "Repeating the restart is unlikely to help without new evidence.",
            "",
            "Next best action:",
            _DEEPER_EVIDENCE_ACTION,
        ]
    )


def compose_did_restart_help_reply(state: InvestigationState) -> str | None:
    failed = resolve_failed_restart_for_state(state)
    if failed is None:
        return None
    log_note = "available but low-signal" if any("low-signal" in item for item in failed.evidence) else "unavailable"
    if any("available" in item and "low-signal" not in item for item in failed.evidence):
        log_note = "available"
    return "\n".join(
        [
            "No — the restart did not appear to help.",
            "",
            "Verification after restart shows:",
            f"- health: **{failed.health_after}**",
            f"- status: **{failed.result.replace('_', ' ')}**",
            f"- logs after restart were {log_note}",
            "",
            "I would avoid another restart until we identify the root cause.",
        ]
    )


def apply_repair_guard_to_planned_action(state: InvestigationState) -> InvestigationState:
    failed = resolve_failed_restart_for_state(state)
    if failed is None:
        return state
    state.next_best_action = _DEEPER_EVIDENCE_ACTION
    state.next_best_action_key = "deeper_evidence_inspection"
    if "restart_did_not_resolve" not in state.evidence:
        state.evidence.append("restart_did_not_resolve")
    if "failed_restart_attempt" not in state.evidence:
        state.evidence.append("failed_restart_attempt")
    return state
