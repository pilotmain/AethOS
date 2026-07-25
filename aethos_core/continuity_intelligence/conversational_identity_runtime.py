# SPDX-License-Identifier: Apache-2.0
"""Conversational identity runtime — one continuous operational entity."""

from __future__ import annotations

import re
from typing import Any

_RECALL_RX = re.compile(
    r"\b("
    r"do you remember"
    r"|remember what we"
    r"|what were we doing"
    r"|what were we talking about"
    r"|what did we (?:do|discuss|talk about|cover|work on)"
    r"|what have we (?:been )?(?:doing|discussing|talking about|working on)"
    r"|what did we do this hour"
    r"|where were we"
    r"|recap"
    r"|catch me up"
    r"|summ(?:ari[sz]e|ary of)\s+(?:our|the|this)\s+(?:conversation|chat|session|discussion)"
    r"|last hour"
    r"|last one hour"
    r"|recently"
    r"|earlier today"
    r")\b",
    re.I,
)
_WITH_SERVICE_RX = re.compile(
    r"\b(?:with|for|on)\s+(?:the\s+)?([a-z0-9][a-z0-9._-]+)\b",
    re.I,
)
_AMNESIA_RX = re.compile(
    r"don't have memory|do not have memory|don't remember|previous conversations|no memory of",
    re.I,
)

# §2 — soul / identity questions. These ask about AethOS's *soul, values, purpose,
# character, and how it was created* and must be answered warmly from SOUL.md — not
# therapist-style deflection. Deliberately NARROW: "who are you" / "what are you" /
# "who created you" / "what is AethOS" are already answered (non-deflecting) by the
# runtime-truth-alignment platform-identity & creator-attribution path, so they are
# left out here. "what are you capable of" stays a capability question; operational
# prompts are excluded by the caller via is_operational_prompt.
_SOUL_IDENTITY_RX = re.compile(
    r"(?:show|tell|describe|explain|reveal)[^.?!]*\byour\s+(?:soul|values?|purpose|character|nature|ethos|principles?)\b"
    r"|\bshow\s+me\s+your\s+soul\b"
    r"|\bwhat(?:'s| is| are)?\s+your\s+(?:soul|values?|purpose|character|nature|ethos|core\s+values?|guiding\s+principles?)\b"
    r"|\bwhat\s+do\s+you\s+(?:value|stand\s+for|believe(?:\s+in)?|care\s+about)\b"
    r"|\bwhy\s+do\s+you\s+exist\b|\bwhat\s+do\s+you\s+exist\s+for\b|\byour\s+reason\s+for\s+being\b"
    r"|\bhow\s+(?:were|was)\s+you\s+(?:created|made|built|designed|born)\b"
    r"|\btell\s+me\s+about\s+yourself\b|\bdescribe\s+yourself\b",
    re.I,
)


def is_continuity_recall_prompt(text: str) -> bool:
    return bool(_RECALL_RX.search(text or ""))


def is_identity_soul_prompt(text: str) -> bool:
    """True for questions about AethOS's soul, values, purpose, origin, or identity."""
    return bool(_SOUL_IDENTITY_RX.search(text or ""))


def is_forbidden_amnesia_reply(reply: str) -> bool:
    return bool(_AMNESIA_RX.search(reply or ""))


def compose_conversational_identity_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.aethos_identity.identity_contract_loader import load_identity_contracts

    load_identity_contracts()

    if is_identity_soul_prompt(text):
        soul = _compose_soul_reply(text)
        if soul is not None:
            return soul

    if not is_continuity_recall_prompt(text):
        return None

    lower = (text or "").lower()
    service_phrase = _extract_with_service(text)

    if service_phrase or "with " in lower or "for " in lower:
        return _compose_service_recall(text, session_id=session_id, service_phrase=service_phrase)

    if "hour" in lower or "recently" in lower or "remember" in lower:
        return _compose_session_recall(text, session_id=session_id)

    return _compose_session_recall(text, session_id=session_id)


def guard_generative_amnesia(
    *,
    user_text: str,
    session_id: str,
    reply: str,
    intent: str,
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.aethos_identity.identity_contract_loader import load_identity_contracts

    load_identity_contracts()

    if intent != "generative_answer" and not is_forbidden_amnesia_reply(reply):
        return None
    if not is_continuity_recall_prompt(user_text) and not is_continuity_recall_prompt(reply):
        from aethos_core.aethos_identity.self_consistency_guard import is_operational_prompt

        if not is_operational_prompt(user_text):
            return None
    replacement = compose_conversational_identity_reply(user_text, session_id=session_id)
    if replacement is not None:
        return replacement
    from aethos_core.aethos_identity.continuity_decision import compose_continuity_operational_reply

    return compose_continuity_operational_reply(user_text, session_id=session_id)


def _soul_section_bullets(content: str, heading: str) -> list[str]:
    """Extract the '- ' bullet lines under a '## <heading>' section of SOUL.md."""
    bullets: list[str] = []
    in_section = False
    target = heading.strip().lower()
    for line in (content or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = stripped[3:].strip().lower() == target
            continue
        if in_section and stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
    return bullets


def _soul_purpose_line(content: str) -> str:
    for line in (content or "").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("it exists to"):
            return stripped
    return "It exists to help operators understand, verify, and safely change real systems — not to perform assistant theater."


def _compose_soul_reply(text: str) -> tuple[str, str, dict[str, str]] | None:
    """Answer soul/identity questions warmly and directly from SOUL.md (§2).

    Always gives a real, grounded answer first — never therapist-style deflection.
    It may invite a follow-up, but only after the substantive answer.
    """
    from aethos_core.aethos_identity.identity_contract_loader import load_identity_contracts

    bundle = load_identity_contracts()
    soul = bundle.soul
    if not soul.exists or not soul.content.strip():
        return None

    lower = (text or "").lower()
    content = soul.content
    identity_bullets = _soul_section_bullets(content, "Core identity")
    rules = _soul_section_bullets(content, "Behavioral rules")
    doctrines = list(bundle.active_doctrines)
    purpose = _soul_purpose_line(content)

    asks_values = bool(re.search(r"\bvalue|stand for|believe|care about|principle\b", lower))
    asks_origin = bool(re.search(r"\bcreat|made|built|designed|born|origin|come from\b", lower))
    asks_purpose = bool(re.search(r"\bpurpose|exist|reason for being\b", lower))

    lines: list[str] = []
    lines.append("I'm AethOS — a governed operational intelligence partner. Here's who I actually am, drawn from my soul (SOUL.md, my behavioral constitution):")
    lines.append("")
    lines.append(f"_{purpose}_")

    if identity_bullets:
        lines.append("")
        lines.append("**At my core I am:**")
        for bullet in identity_bullets[:6]:
            lines.append(f"- {bullet}")

    if asks_values and rules:
        lines.append("")
        lines.append("**What I value in practice:**")
        for rule in rules[:5]:
            lines.append(f"- {rule}")
    elif doctrines:
        lines.append("")
        lines.append("**The doctrines I hold under pressure:**")
        for doctrine in doctrines[:4]:
            lines.append(f"- {doctrine}")

    if asks_origin:
        lines.append("")
        lines.append(
            "I wasn't given a backstory — I'm defined by my contracts. My soul lives in **SOUL.md** "
            "and my memory hierarchy in **MEMORY.md**, loaded from the project runtime as authoritative "
            "identity, not as a costume. That's what makes me one continuous operational entity rather "
            "than a fresh chatbot each turn."
        )

    if asks_purpose and not asks_origin:
        lines.append("")
        lines.append(
            "My purpose is exactly that: be useful through continuity, act from evidence, and stay honest "
            "about what's known, inferred, or still unproven."
        )

    lines.append("")
    lines.append("Ask me anything about how I think or work, or point me at a system and I'll show you rather than tell you.")

    body = "\n".join(lines)
    meta = {
        "route_id": "soul_identity",
        "source": "SOUL.md",
        "content_hash": soul.content_hash or "",
        "suppress_governance_footer": "true",
    }
    return (body, "soul_identity", meta)


def _compose_service_recall(text: str, *, session_id: str, service_phrase: str) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.aethos_identity.context_reconstructor import extract_operational_resource_phrase
    from aethos_core.continuity_intelligence.continuity_recall_engine import recall_operational_memory
    from aethos_core.continuity_intelligence.continuity_timeline import timeline_for_service
    from aethos_core.operational_thread_memory.failure_reason_extractor import extract_failure_reason

    phrase = service_phrase or extract_operational_resource_phrase(text) or ""
    recall = recall_operational_memory(session_id=session_id, user_text=text)
    if recall is None or (phrase and recall.service and phrase.lower() not in recall.service.lower()):
        recall = recall_operational_memory(session_id=session_id, user_text=f"what were we doing with {phrase}")

    if recall is None:
        return None

    service = recall.service or phrase
    provider = recall.provider or "railway"
    operation = (recall.operation or "operation").replace("_", " ")
    path = f"{recall.meta.get('project') or ''} / production / {service}".strip(" /")
    if recall.thread is not None:
        path = recall.thread.service_path()

    lines = [f"We were troubleshooting a **{provider.title()}** **{operation}** for **{service}**."]
    failure_text = ""
    binding_note = ""

    job = recall.execution_job
    if job is not None:
        failure = extract_failure_reason(job)
        if failure and failure.get("failure_reason"):
            failure_text = str(failure.get("failure_reason"))
            binding_note = _binding_notes_from_failure(failure_text)
        params = getattr(job, "params", None) or {}
        bundle = dict(params.get("provider_evidence_bundle") or {})
        if recall.thread and recall.thread.failure_reason:
            failure_text = str(recall.thread.failure_reason.get("failure_reason") or failure_text)

    timeline = timeline_for_service(session_id=session_id, service_phrase=service)
    if failure_text:
        lines.extend(["", "The restart initially failed because:", failure_text])
    if binding_note:
        lines.extend(["", binding_note])
    elif "source binding" in failure_text.lower() or "github" in failure_text.lower():
        lines.extend(["", "Source binding reconciliation was part of this investigation."])

    if timeline:
        latest = timeline[0]
        lines.extend(
            [
                "",
                f"Latest stored result: **{latest.result or recall.meta.get('status', 'updated')}**.",
                f"Most recent event: `{latest.timestamp}` · {latest.detail or latest.operation}.",
            ]
        )
    elif recall.thread is not None:
        lines.extend(
            [
                "",
                f"Latest stored result: **{recall.thread.status}** — {recall.thread.last_system_result or 'execution updated'}.",
            ]
        )

    lines.append("")
    lines.append("I reconstructed this from recent operational timeline and job truth — not generic chat memory loss.")
    return (
        "\n".join(lines),
        "continuity_service_recall",
        {
            "service": service,
            "provider": provider,
            "confidence": str(recall.confidence),
            "source": recall.source,
        },
    )


def _compose_session_recall(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    """Recap the session from BOTH conversation memory and the operational timeline.

    The conversation summary memory (MEMORY.md "Conversation summary memory" layer)
    carries general topics and what we discussed; the operational timeline carries
    governed jobs/provider actions. A complete recap merges both so a plain
    "what did we discuss?" no longer falls to the operational-only path.
    """
    from aethos_core.continuity_intelligence.continuity_timeline import summarize_timeline, timeline_within_hours

    hours = 1.0 if "hour" in (text or "").lower() else 8.0
    hours_label = "last hour" if hours <= 1.5 else "recent session"

    conversation_recap = None
    try:
        from aethos_core.memory.conversation_summary_memory import compose_conversation_recap_text

        conversation_recap = compose_conversation_recap_text(session_id, hours=hours)
    except Exception:
        conversation_recap = None

    entries = timeline_within_hours(session_id=session_id, hours=hours)

    sections: list[str] = []
    if conversation_recap:
        sections.append(conversation_recap)
    if entries:
        sections.append(summarize_timeline(entries, hours_label=hours_label))

    if sections:
        body = "\n\n".join(sections)
        body += (
            "\n\nThis recap is reconstructed from this session's conversation memory and "
            "governed operational timeline — not generic stateless chat memory."
        )
    else:
        body = summarize_timeline(entries, hours_label=hours_label)
        body += (
            "\n\nThis summary comes from governed jobs, operational threads, and provider actions stored in this session — "
            "not from generic stateless chat memory."
        )

    return (
        body,
        "continuity_session_recall",
        {
            "hours": str(hours),
            "event_count": str(len(entries)),
            "conversation_recall": "true" if conversation_recap else "false",
        },
    )


def _extract_with_service(text: str) -> str:
    match = _WITH_SERVICE_RX.search(text or "")
    if not match:
        return ""
    candidate = match.group(1).strip().lower()
    skip = {"railway", "vercel", "github", "the", "last", "hour", "one", "doing", "what", "we", "were"}
    if candidate in skip:
        return ""
    return candidate


def _binding_notes_from_failure(failure_text: str) -> str:
    lower = failure_text.lower()
    if "rayameresa/" in lower and "pilotmain/" in lower:
        return (
            "You updated the repository binding during this investigation.\n"
            "After the correction, restart execution could proceed under governed approval."
        )
    if "source binding" in lower or "github" in lower:
        return "Repository/source binding correction was part of this operational thread."
    return ""
