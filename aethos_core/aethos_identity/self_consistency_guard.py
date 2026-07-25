# SPDX-License-Identifier: Apache-2.0
"""Block generic fallback when reconstructable operational evidence exists."""

from __future__ import annotations

import re

_STALE_NO_THREAD_RX = re.compile(
    r"don't have an active operational mutation thread|don't have context|i'm ready to help|"
    r"don't have memory|do not have memory|don't remember|previous conversations|no memory of",
    re.I,
)

_OPERATIONAL_PROMPT_RX = re.compile(
    r"\b("
    r"logs?"
    r"|timestamp"
    r"|status"
    r"|restart"
    r"|redeploy"
    r"|deploy"
    r"|check"
    r"|verify"
    r"|fix"
    r"|why did"
    r"|what were we"
    r"|job-"
    r"|dj-"
    r"|top\s+\d+"
    r"|latest\s+\d+"
    r")\b",
    re.I,
)

_PROVIDER_RX = re.compile(r"\b(railway|vercel|github|docker|kubernetes|aws)\b", re.I)
_SERVICE_LIKE_RX = re.compile(r"\b[a-z0-9][a-z0-9._-]{2,62}\b", re.I)


def is_operational_prompt(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _OPERATIONAL_PROMPT_RX.search(raw):
        return True
    if _PROVIDER_RX.search(raw):
        return True
    from aethos_core.aethos_identity.context_reconstructor import extract_operational_resource_phrase

    phrase = extract_operational_resource_phrase(raw)
    if phrase and (phrase.startswith("job-") or "-" in phrase):
        return True
    return False


def should_block_generic_fallback(*, text: str, session_id: str = "default") -> bool:
    if not is_operational_prompt(text):
        return False

    from aethos_core.aethos_identity.identity_contract_loader import (
        generic_operational_fallback_forbidden,
        load_identity_contracts,
        reconstruct_before_amnesia_required,
    )

    load_identity_contracts()
    contract_enforced = generic_operational_fallback_forbidden() or reconstruct_before_amnesia_required()

    from aethos_core.aethos_identity.memory_health import assess_memory_health

    health = assess_memory_health(session_id=session_id, user_text=text)
    if health.reconstructable or bool(health.provider_matches) or health.recent_execution_job:
        return True

    if contract_enforced:
        from aethos_core.aethos_identity.context_reconstructor import extract_operational_resource_phrase, search_provider_targets

        phrase = extract_operational_resource_phrase(text) or ""
        if phrase and search_provider_targets(phrase).matches:
            return True

    return False


def is_forbidden_no_context_reply(reply: str) -> bool:
    return bool(_STALE_NO_THREAD_RX.search(reply or ""))


def guard_proposed_reply(
    *,
    text: str,
    session_id: str,
    reply: str,
    intent: str,
) -> tuple[str, str, dict[str, str]] | None:
    """Return replacement reply when a stale/no-context response should be suppressed."""

    if intent not in {"operational_thread_stale", "generative_answer", "operational_thread_followup"}:
        if not is_forbidden_no_context_reply(reply):
            return None
    elif intent != "operational_thread_stale" and not is_forbidden_no_context_reply(reply):
        return None

    if not should_block_generic_fallback(text=text, session_id=session_id):
        return None

    from aethos_core.aethos_identity.continuity_decision import compose_continuity_operational_reply

    replacement = compose_continuity_operational_reply(text, session_id=session_id)
    if replacement is not None:
        return replacement
    return None
