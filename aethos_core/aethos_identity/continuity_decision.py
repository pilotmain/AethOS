# SPDX-License-Identifier: Apache-2.0
"""Decide reconstruct vs clarify vs answer for operational continuity."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.conversation.provider_memory.followup_intent_classifier import (
    classify_followup_intent,
    is_operational_followup_request,
    parse_log_limit,
)


def decide_continuity_action(*, text: str, session_id: str = "default") -> str:
    """Return reconstruct, answer, clarify, or defer."""

    from aethos_core.aethos_identity.context_reconstructor import maybe_reconstruct_active_thread, search_provider_targets
    from aethos_core.aethos_identity.memory_health import assess_memory_health
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread

    if is_operational_followup_request(text, session_id=session_id):
        return "answer"

    health = assess_memory_health(session_id=session_id, user_text=text)
    phrase = health.service_phrase
    if get_active_thread(session_id=session_id) is not None:
        return "answer"

    if health.reconstructable:
        return "reconstruct"

    if phrase:
        topology = search_provider_targets(phrase)
        if topology.resolved:
            return "reconstruct"
        if topology.ambiguous:
            return "clarify"

    return "defer"


def compose_continuity_operational_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    """Answer readonly operational prompts using reconstructed topology/job context."""

    from aethos_core.chat.explicit_mutation_intent import has_explicit_mutation_verb, should_skip_readonly_reconstruction

    if should_skip_readonly_reconstruction(text, session_id=session_id) or has_explicit_mutation_verb(text):
        return None

    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if master_router_has_priority_route(text, session_id=session_id):
        return None

    from aethos_core.aethos_identity.context_reconstructor import (
        extract_operational_resource_phrase,
        maybe_reconstruct_active_thread,
        reconstruct_context_summary,
        search_provider_targets,
    )
    from aethos_core.aethos_identity.self_consistency_guard import is_operational_prompt
    from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply

    if not is_operational_prompt(text):
        return None

    reconstructed = maybe_reconstruct_active_thread(session_id=session_id, user_text=text)
    if reconstructed and reconstructed.source in {"execution_job", "active_thread"}:
        followup = compose_provider_followup_reply(text, session_id=session_id)
        if followup is not None:
            return followup

    phrase = extract_operational_resource_phrase(text) or ""
    if not phrase:
        return None

    if "what were we doing" in text.lower() or "what were we talking about" in text.lower():
        summary = reconstruct_context_summary(session_id=session_id, user_text=text)
        if summary:
            return summary, "continuity_reconstructed", {"source": reconstructed.source if reconstructed else "memory"}

    topology = search_provider_targets(phrase)
    if topology.ambiguous and topology.matches:
        options = ", ".join(f"**{m.provider}**: {m.path or m.service_name}" for m in topology.matches[:4])
        return (
            f"I found **{phrase}** in multiple provider contexts: {options}.\n\n"
            "Which provider should I check?",
            "continuity_provider_clarification",
            {"service": phrase, "ambiguous": "true"},
        )

    target = topology.resolved
    if target is None:
        return None

    intent = _readonly_intent(text)
    if intent == "fetch_logs":
        return _compose_readonly_logs_reply(target, text, session_id=session_id)
    if intent == "fetch_timestamp":
        return _compose_readonly_timestamp_reply(target, text, session_id=session_id)
    if intent == "verify":
        return _compose_readonly_verify_reply(target, text, session_id=session_id, reconstructed=reconstructed)

    if _mentions_logs(text):
        return _compose_readonly_logs_reply(target, text, session_id=session_id)

    return (
        f"I found **{target.service_name}** in **{target.provider.title()}** under **{target.path or target.service_name}**.\n\n"
        f"I can check logs, status, or recent execution evidence for this target without starting a new mutation.",
        "continuity_target_resolved",
        {"provider": target.provider, "service": target.service_name},
    )


def _readonly_intent(text: str) -> str:
    lower = (text or "").lower()
    if parse_log_limit(text) or ("log" in lower and any(w in lower for w in ("check", "show", "read", "top", "latest"))):
        return "fetch_logs"
    if "timestamp" in lower:
        return "fetch_timestamp"
    if any(word in lower for word in ("did restart", "did it happen", "did the restart", "verify restart")):
        return "verify"
    return "status"


def _mentions_logs(text: str) -> bool:
    return bool(parse_log_limit(text) or re.search(r"\blogs?\b", text or "", re.I))


def _log_sources_checked(service_name: str) -> list[str]:
    from aethos_core.providers.railway.operations.logs_multisource import fetch_railway_logs_multisource

    payload = fetch_railway_logs_multisource(service_name=service_name, limit=1)
    return list(payload.get("sources_checked") or [])


def _compose_readonly_logs_reply(target: Any, text: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    limit = parse_log_limit(text) or 5
    logs = _fetch_readonly_logs(provider=target.provider, service_name=target.service_name, limit=limit)
    intro = (
        f"I found **{target.service_name}** in **{target.provider.title()}** under **{target.path}**.\n\n"
        f"I checked the latest Railway logs and returned the **{min(limit, len(logs)) if logs else limit}** most recent entries with timestamps.\n\n"
        if target.provider == "railway"
        else f"I found **{target.service_name}** under **{target.path or target.service_name}**.\n\n"
    )
    if not logs:
        body = (
            intro
            + "I checked deployment, runtime, and service log surfaces, but no log lines were returned yet."
            + (f"\n\nSources checked: {', '.join(_log_sources_checked(target.service_name))}." if target.provider == "railway" else ".")
            + "\n\nThis was a readonly inspection — no mutation was performed."
        )
        return body, "continuity_readonly_logs", {"provider": target.provider, "service": target.service_name}

    body = intro + f"Latest {len(logs)} logs:\n"
    for idx, row in enumerate(logs, start=1):
        ts = row.get("timestamp") or "no timestamp"
        level = row.get("level") or "INFO"
        message = str(row.get("message") or row)[:240]
        body += f"{idx}. [{ts}] {level} {message}\n"

    if not any(row.get("timestamp") for row in logs):
        body += (
            "\nRailway returned recent logs, but no timestamp was available in the log payload. "
            "I cannot use these logs as restart proof yet."
        )
    elif "timestamp" in text.lower():
        latest_ts = next((row.get("timestamp") for row in logs if row.get("timestamp")), None)
        if latest_ts:
            body += f"\n\nLatest log timestamp: **{latest_ts}**"
    body += "\n\nReadonly inspection — no mutation was performed."
    return body, "continuity_readonly_logs", {"provider": target.provider, "service": target.service_name, "log_count": str(len(logs))}


def _compose_readonly_timestamp_reply(target: Any, text: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    logs = _fetch_readonly_logs(provider=target.provider, service_name=target.service_name, limit=1)
    if not logs:
        return (
            f"I found **{target.service_name}** in **{target.provider.title()}** under **{target.path}**, "
            "but no timestamped logs are available yet.",
            "continuity_readonly_timestamp",
            {"provider": target.provider, "service": target.service_name},
        )
    latest = logs[0]
    ts = latest.get("timestamp")
    if not ts:
        return (
            "Railway returned recent logs, but no timestamp was available in the log payload. "
            "I cannot use these logs as restart proof yet.",
            "continuity_readonly_timestamp",
            {"provider": target.provider, "service": target.service_name},
        )
    return (
        f"I found **{target.service_name}** in **{target.provider.title()}** under **{target.path}**.\n\n"
        f"The latest log timestamp is:\n\n- **{ts}**\n\n"
        f'Recent log:\n"{latest.get("message") or ""}"',
        "continuity_readonly_timestamp",
        {"provider": target.provider, "service": target.service_name, "latest_timestamp": str(ts)},
    )


def _compose_readonly_verify_reply(
    target: Any,
    text: str,
    *,
    session_id: str,
    reconstructed: Any | None,
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.operational_thread_memory.mutation_thread_memory import find_execution_job_for_service

    job = find_execution_job_for_service(session_id=session_id, service_phrase=target.service_name)
    if job is not None and reconstructed and reconstructed.thread is not None:
        from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply

        reply = compose_provider_followup_reply(text, session_id=session_id)
        if reply:
            return reply

    return (
        f"I found **{target.service_name}** in **{target.provider.title()}** under **{target.path}**.\n\n"
        "I do not have verified restart evidence for a recent governed execution in this session yet.\n\n"
        "I can inspect latest logs or start a governed restart if you want to verify runtime state.",
        "continuity_readonly_verify",
        {"provider": target.provider, "service": target.service_name},
    )


def _fetch_readonly_logs(*, provider: str, service_name: str, limit: int) -> list[dict[str, Any]]:
    provider = (provider or "").strip().lower()
    if provider != "railway":
        return []

    from aethos_core.providers.railway.operations.logs_multisource import fetch_railway_logs_multisource

    payload = fetch_railway_logs_multisource(service_name=service_name, limit=limit)
    logs = list(payload.get("logs") or [])
    if logs:
        return logs

    return []
