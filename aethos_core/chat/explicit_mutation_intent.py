# SPDX-License-Identifier: Apache-2.0
"""Explicit mutation intent — action verbs must win over memory reconstruction."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_CONFIDENCE_THRESHOLD = 0.75

_READONLY_RX = re.compile(
    r"\b("
    r"check\s+(?:the\s+)?(?:top|latest|recent)?\s*\d*\s*logs?"
    r"|show\s+(?:me\s+)?(?:the\s+)?(?:top|latest|recent)?\s*\d*\s*logs?"
    r"|read\s+(?:the\s+)?logs?"
    r"|top\s+\d+\s+logs?"
    r"|latest\s+\d+\s+logs?"
    r"|what(?:'s| is)\s+the\s+status"
    r"|status\s+of"
    r"|did\s+(?:the\s+)?restart\s+(?:actually\s+)?(?:happen(?:ed|s)?|work(?:ed|s)?)\??"
    r"|did\s+it\s+(?:actually\s+)?(?:happen(?:ed|s)?|work(?:ed|s)?)\??"
    r"|did\s+you\s+stop\b"
    r"|did\s+the\s+(?:projects?|services?)\s+stop\b"
    r"|were\s+(?:the\s+)?(?:projects?|services?)\s+stopped\b"
    r"|was\s+(?:the\s+)?(?:project|service)\s+stopped\b"
    r"|verify\s+(?:the\s+)?restart"
    r"|any\s+proof"
    r"|is restart safe|should (?:i|we) restart|safe to restart|can i restart"
    r"|is redeploy safe|should (?:i|we) redeploy|safe to redeploy|can i redeploy"
    r")\b",
    re.I,
)

_OPERATION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("env_update", re.compile(
        r"\bset\s+[A-Z][A-Z0-9_]+=[^\s]+"
        r"|\b(?:set|update)\s+[A-Z][A-Z0-9_]+\b(?=\s+(?:on|for)\s+)",
        re.I,
    )),
    ("rollback", re.compile(r"\brollback\b", re.I)),
    ("redeploy", re.compile(r"\bre-?deploy(?:ing|ment)?\b|\bre[\s-]?trigger\s+(?:the\s+)?deployment\b", re.I)),
    ("restart", re.compile(r"\b(?:restart|reboot)\b", re.I)),
    ("workflow_rerun", re.compile(r"\brerun\b.*\b(?:failed\s+)?(?:github\s+)?workflow\b|\bworkflow\b.*\brerun\b", re.I)),
    ("deploy", re.compile(
        r"\bdeploy\b(?:\s+latest|\s+now)?"
        r"|\bdeploying\b"
        r"|\bprovision\b"
        r"|\bset\s+up\s+(?:the\s+)?(?:env|environment)\b",
        re.I,
    )),
    ("scale", re.compile(r"\bscale\b", re.I)),
    ("stop", re.compile(r"\bstop\b", re.I)),
    ("start", re.compile(r"\bstart\b", re.I)),
]

_PROVIDER_RX = re.compile(r"\b(railway|vercel|github|docker|kubernetes|aws)\b", re.I)
_BARE_MUTATION_RX = re.compile(
    r"^(?:please\s+)?(?:restart|redeploy|deploy(?:\s+latest)?|rollback|scale|stop|start)\.?$",
    re.I,
)


@dataclass
class MutationIntent:
    provider: str = ""
    operation: str = ""
    target_phrase: str = ""
    confidence: float = 0.0
    requires_approval: bool = True
    source: str = "explicit_text"
    ambiguous_targets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "operation": self.operation,
            "target_phrase": self.target_phrase,
            "confidence": round(self.confidence, 3),
            "requires_approval": self.requires_approval,
            "source": self.source,
            "ambiguous_targets": list(self.ambiguous_targets),
        }


def is_readonly_operational_request(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False

    from aethos_core.repair_memory.repair_outcome_router import is_repair_outcome_question

    if is_repair_outcome_question(raw):
        return True

    from aethos_core.operations.mutations.stop_mutation import is_stop_outcome_question

    if is_stop_outcome_question(raw):
        return True

    if has_explicit_mutation_verb(raw):
        return False

    from aethos_core.conversation.provider_memory.conversational_memory_router import is_provider_followup_request

    if is_provider_followup_request(raw, session_id=session_id):
        return True

    if _READONLY_RX.search(raw):
        return True

    lower = raw.lower()
    if "log" in lower and any(word in lower for word in ("check", "show", "read", "top", "latest", "timestamp")):
        return True
    if "what were we doing" in lower or "do you remember" in lower:
        return True
    return False


def has_explicit_mutation_verb(text: str) -> bool:
    from aethos_core.post_mutation_verification.verification_intent_router import (
        is_post_mutation_verification_intent,
    )

    if is_post_mutation_verification_intent(text):
        return False

    from aethos_core.post_mutation_verification.verification_intent_router import (
        looks_like_verification_target_selection,
    )

    if looks_like_verification_target_selection(text):
        return False

    return bool(_detect_operation((text or "").strip()))


def detect_explicit_mutation_intent(text: str, *, session_id: str = "default") -> MutationIntent | None:
    raw = (text or "").strip()
    if not raw:
        return None
    from aethos_core.chat.informational_turn_classifier import should_block_mutation_routing

    if should_block_mutation_routing(raw, session_id=session_id):
        return None
    from aethos_core.chat.local_system_guidance import is_local_aethos_api_restart_intent

    if is_local_aethos_api_restart_intent(raw):
        return None
    from aethos_core.world_model.safety_question_classifier import is_safety_question

    if is_safety_question(raw):
        return None
    if is_readonly_operational_request(raw, session_id=session_id):
        return None

    operation = _detect_operation(raw)
    if not operation:
        return None

    provider = _detect_provider(raw)
    target_phrase = _detect_target_phrase(raw)
    ambiguous: list[str] = []
    source = "explicit_text"
    confidence = 0.72

    if target_phrase:
        confidence = 0.93 if provider else 0.88
        if provider:
            confidence = 0.96
    elif _BARE_MUTATION_RX.match(raw):
        context = _resolve_context_targets(session_id=session_id)
        if len(context) == 1:
            target_phrase = context[0]["service"]
            provider = provider or context[0].get("provider") or "railway"
            source = "active_context"
            confidence = 0.86
        elif len(context) > 1:
            ambiguous = [row["service"] for row in context if row.get("service")]
            source = "ambiguous_context"
            confidence = 0.58
        else:
            source = "operation_only"
            confidence = 0.70
    elif provider and not target_phrase:
        confidence = 0.78

    # Never silently assume a provider when none was named.
    if not provider and not target_phrase and source == "operation_only":
        return None

    return MutationIntent(
        provider=provider,
        operation=operation,
        target_phrase=target_phrase,
        confidence=confidence,
        source=source,
        ambiguous_targets=ambiguous,
    )


def compose_explicit_mutation_preflight_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.informational_turn_classifier import should_block_mutation_routing

    if should_block_mutation_routing(text, session_id=session_id):
        return None

    from aethos_core.devops_intent_planner.devops_request_classifier import should_defer_to_devops_plan

    if should_defer_to_devops_plan(text, session_id=session_id):
        return None

    intent = detect_explicit_mutation_intent(text, session_id=session_id)
    if intent is None:
        return None

    if intent.confidence < _CONFIDENCE_THRESHOLD:
        if intent.ambiguous_targets:
            return _compose_ambiguous_target_reply(intent)
        if intent.operation and not intent.provider:
            return _compose_missing_provider_reply(intent)
        return None

    if intent.operation and not intent.provider and not intent.target_phrase:
        return _compose_missing_provider_reply(intent)

    from aethos_core.operation_lifecycle.lifecycle_resolver import compose_duplicate_mutation_reply, is_duplicate_mutation_request

    duplicate, dup_state = is_duplicate_mutation_request(
        text,
        session_id=session_id,
        provider=intent.provider or None,
        operation=intent.operation or None,
        service=intent.target_phrase or None,
    )
    if duplicate and dup_state:
        return (
            compose_duplicate_mutation_reply(dup_state),
            "operation_lifecycle_duplicate_blocked",
            {
                "match_key": dup_state.match_key,
                "explicit_mutation_intent": intent.operation,
            },
        )

    from aethos_core.operations.mutations.stop_mutation import compose_stop_mutation_preflight_reply

    stop_reply = compose_stop_mutation_preflight_reply(text, session_id=session_id)
    if stop_reply is not None:
        return stop_reply

    request_text = _enrich_request_text(text, intent, session_id=session_id)
    from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply

    reply = create_mutation_preflight_job_reply(request_text, session_id=session_id)
    if reply is None:
        return None

    body, reply_intent, meta = reply
    if _BARE_MUTATION_RX.match((text or "").strip()):
        prefix = _bare_command_prefix(intent, session_id=session_id)
        if prefix:
            body = f"{prefix}\n\n{body}"
    meta = {**meta, "explicit_mutation_intent": intent.operation, "mutation_intent_source": intent.source}
    return body, reply_intent, meta


def should_skip_readonly_reconstruction(text: str, *, session_id: str = "default") -> bool:
    intent = detect_explicit_mutation_intent(text, session_id=session_id)
    return intent is not None and intent.confidence >= _CONFIDENCE_THRESHOLD


def _detect_operation(text: str) -> str:
    from aethos_core.repair_memory.repair_outcome_router import is_repair_outcome_question

    if is_repair_outcome_question(text):
        return ""
    lower = (text or "").lower()
    if re.search(r"\bdid\s+(?:the\s+)?restart\b", lower) or re.search(r"\bdid\s+it\s+(?:actually\s+)?(?:happen|work)", lower):
        return ""
    from aethos_core.world_model.world_model_followup_router import is_mutation_safety_question

    if is_mutation_safety_question(text):
        return ""
    for operation, pattern in _OPERATION_PATTERNS:
        if pattern.search(text):
            return operation
    return ""


def _detect_provider(text: str) -> str:
    match = _PROVIDER_RX.search(text or "")
    return match.group(1).lower() if match else ""


def _detect_target_phrase(text: str) -> str:
    from aethos_core.aethos_identity.context_reconstructor import extract_operational_resource_phrase

    phrase = extract_operational_resource_phrase(text) or ""
    if phrase.startswith("job-") or phrase.startswith("dj-"):
        return ""
    phrase = re.sub(
        r"\s+on(?:\s+(?:railway|vercel|github))?\s*$",
        "",
        phrase,
        flags=re.I,
    ).strip()
    return phrase


def _resolve_context_targets(*, session_id: str) -> list[dict[str, str]]:
    from aethos_core.continuity_intelligence.continuity_timeline import build_continuity_timeline
    from aethos_core.continuity_intelligence.operational_focus_model import get_operational_focus
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread
    from aethos_core.providers.github.context.github_context_store import get_active_github_context

    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    gh_ctx = get_active_github_context(session_id=session_id)
    if gh_ctx and gh_ctx.get("repo_full_name"):
        key = f"github:{gh_ctx['repo_full_name']}"
        seen.add(key)
        rows.append(
            {
                "provider": "github",
                "service": str(gh_ctx["repo_full_name"]),
                "project": str(gh_ctx.get("owner") or ""),
                "environment": str(gh_ctx.get("active_branch") or "main"),
            }
        )

    thread = get_active_thread(session_id=session_id)
    if thread is not None and thread.service:
        key = f"{thread.provider}:{thread.service}"
        seen.add(key)
        rows.append(
            {
                "provider": str(thread.provider or "railway"),
                "service": str(thread.service or ""),
                "project": str(thread.project or ""),
                "environment": str(thread.environment or "production"),
            }
        )

    focus = get_operational_focus(session_id=session_id)
    if focus.get("service"):
        key = f"{focus.get('provider','railway')}:{focus.get('service')}"
        if key not in seen:
            seen.add(key)
            rows.append(
                {
                    "provider": str(focus.get("provider") or "railway"),
                    "service": str(focus.get("service") or ""),
                    "project": "",
                    "environment": "production",
                }
            )

    for entry in build_continuity_timeline(session_id=session_id, hours=2.0):
        if not entry.service:
            continue
        key = f"{entry.provider}:{entry.service}"
        if key in seen:
            continue
        if thread is not None and str(thread.service or "") == entry.service and str(thread.provider or "") == (entry.provider or "railway"):
            continue
        seen.add(key)
        rows.append(
            {
                "provider": entry.provider or "railway",
                "service": entry.service,
                "project": "",
                "environment": "production",
            }
        )

    return rows[:4]


def _enrich_request_text(text: str, intent: MutationIntent, *, session_id: str) -> str:
    raw = (text or "").strip()
    if intent.target_phrase and intent.provider:
        return raw

    provider = intent.provider
    if intent.target_phrase and provider:
        return f"{intent.operation} {provider} {intent.target_phrase}"

    context = _resolve_context_targets(session_id=session_id)
    if len(context) == 1:
        service = context[0]["service"]
        provider = context[0].get("provider") or provider
        if provider:
            return f"{intent.operation} {provider} {service}"

    return raw


def _compose_missing_provider_reply(intent: MutationIntent) -> tuple[str, str, dict[str, str]]:
    op = intent.operation.replace("_", " ")
    lines = [
        f"I heard a **{op}** request, but I need to know **which provider and service** before I create a governed preflight.",
        "",
        "Tell me the provider (Railway, Vercel, GitHub) and the project/service alias — "
        "for example: `restart aethos-api on railway`.",
        "",
        "No mutation preflight has been created yet.",
    ]
    return (
        "\n".join(lines),
        "mutation_provider_clarification",
        {"operation": intent.operation, "provider": ""},
    )


def _compose_ambiguous_target_reply(intent: MutationIntent) -> tuple[str, str, dict[str, str]]:
    lines = [
        f"I can **{intent.operation.replace('_', ' ')}** the active Railway target, but I found multiple recent services:",
        "",
    ]
    for idx, service in enumerate(intent.ambiguous_targets[:4], start=1):
        lines.append(f"{idx}. **{service}**")
    lines.extend(
        [
            "",
            "Which one should I stop?" if intent.operation == "stop" else "Which one should I restart?",
            "",
            "No preflight has been created yet.",
        ]
    )
    return (
        "\n".join(lines),
        "mutation_target_clarification",
        {"operation": intent.operation, "ambiguous": "true"},
    )


def _bare_command_prefix(intent: MutationIntent, *, session_id: str) -> str:
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread

    thread = get_active_thread(session_id=session_id)
    if thread is None:
        return ""
    op = intent.operation.replace("_", " ")
    return (
        f"You're asking to **{op}** the active **{thread.provider.title()}** target: "
        f"**{thread.service_path()}**."
    )
