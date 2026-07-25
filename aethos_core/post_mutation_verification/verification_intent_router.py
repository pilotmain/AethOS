# SPDX-License-Identifier: Apache-2.0
"""Post-mutation verification intent routing and target recovery."""

from __future__ import annotations

import re
from dataclasses import dataclass
from time import time
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from aethos_core.operation_lifecycle.operation_state_store import OperationLifecycleState

VerificationIntentType = Literal[
    "verify_health",
    "recovery_check",
    "before_after_change",
    "fetch_post_restart_logs",
    "startup_log_check",
    "hold_check",
    "verification_status",
]

INTENT_WORDS = frozenset({
    "changed",
    "restart",
    "health",
    "logs",
    "started",
    "application",
    "recover",
    "recovered",
    "hold",
    "status",
    "verify",
    "verification",
    "fetch",
    "check",
    "top",
    "latest",
    "recent",
    "after",
    "before",
    "compare",
    "mutation",
    "post",
})

_PATH_TARGET_RX = re.compile(
    r"(?P<project>[a-z0-9][\w-]*)\s*[/\\]\s*(?P<environment>[a-z0-9][\w-]*)\s*[/\\]\s*(?P<service>[\w-]+)",
    re.I,
)

_VERIFY_HEALTH_RX = re.compile(
    r"\b("
    r"verify\s+health"
    r"|check\s+health"
    r"|health\s+check"
    r"|confirm\s+recovery"
    r")\b",
    re.I,
)

_RECOVERY_RX = re.compile(
    r"\b("
    r"did\s+it\s+recover"
    r"|did\s+(?:the\s+)?(?:restart|service|mongodb|mongo)\s+recover"
    r"|did\s+restart\s+help"
    r"|is\s+it\s+healthy\s+now"
    r"|did\s+the\s+restart\s+help"
    r"|did\s+the\s+restart\s+work"
    r")\b",
    re.I,
)

_HOLD_RX = re.compile(
    r"\b("
    r"did\s+it\s+hold"
    r"|is\s+it\s+still\s+healthy"
    r"|did\s+recovery\s+hold"
    r"|is\s+it\s+stable\s+now"
    r")\b",
    re.I,
)

_BEFORE_AFTER_RX = re.compile(
    r"\b("
    r"what\s+changed(?:\s+after)?(?:\s+(?:the\s+)?restart)?"
    r"|what\s+changed\s+after\s+mutation"
    r"|before\s+and\s+after"
    r"|compare\s+before\s+and\s+after"
    r")\b",
    re.I,
)

_FETCH_POST_RESTART_LOGS_RX = re.compile(
    r"\b("
    r"fetch\s+logs\s+after\s+restart"
    r"|logs\s+after\s+restart"
    r"|post[- ]restart\s+logs"
    r"|show\s+logs\s+after\s+restart"
    r")\b",
    re.I,
)

_STARTUP_LOG_RX = re.compile(
    r"\b("
    r"(?:top|latest|last|recent)\s+\d+\s+logs?"
    r"|check\s+(?:the\s+)?(?:top|latest|recent)\s+\d+\s+logs?"
    r"|logs?\s+.*\bapplication\s+started"
    r"|application\s+started"
    r"|see\s+if\s+application\s+started"
    r"|startup\s+markers?"
    r")\b",
    re.I,
)

_POST_MUTATION_CONTEXT_RX = re.compile(
    r"\b("
    r"after\s+restart"
    r"|after\s+mutation"
    r"|post[- ]restart"
    r"|verify"
    r"|recover"
    r"|hold"
    r"|application\s+started"
    r")\b",
    re.I,
)

_PENDING: dict[str, dict[str, Any]] = {}


@dataclass
class VerificationTarget:
    provider: str | None = None
    project: str | None = None
    environment: str | None = None
    service: str | None = None
    target_path: str = ""
    source: str = "lifecycle"


def is_intent_word(value: str | None) -> bool:
    return str(value or "").strip().lower() in INTENT_WORDS


def extract_explicit_path_target(text: str) -> VerificationTarget | None:
    match = _PATH_TARGET_RX.search(text or "")
    if not match:
        return None
    project = match.group("project")
    environment = match.group("environment")
    service = match.group("service")
    if is_intent_word(project) or is_intent_word(service):
        return None
    return VerificationTarget(
        project=project,
        environment=environment,
        service=service,
        target_path=f"{project} / {environment} / {service}",
        source="explicit_path",
    )


def recent_mutation_lifecycle_exists(*, session_id: str = "default") -> bool:
    from aethos_core.post_mutation_verification.verification_context_discovery import (
        discover_verification_lifecycle,
        global_mutation_lifecycle_exists,
    )

    if discover_verification_lifecycle("", session_id=session_id) is not None:
        return True
    return global_mutation_lifecycle_exists()


def list_recent_mutation_lifecycles(*, session_id: str = "default", limit: int = 5):
    from aethos_core.post_mutation_verification.verification_context_discovery import (
        list_discovered_recent_mutations,
    )

    return list_discovered_recent_mutations(session_id=session_id, limit=limit)


def _target_from_state(state: Any) -> VerificationTarget:
    return VerificationTarget(
        provider=state.provider,
        project=state.project,
        environment=state.environment,
        service=state.service,
        target_path=state.target_path(),
        source="global_lifecycle_index",
    )


def _candidates_from_pending(pending: dict[str, Any]) -> list[OperationLifecycleState]:
    from aethos_core.operation_lifecycle.operation_state_store import OperationLifecycleState

    rows: list[OperationLifecycleState] = []
    for raw in pending.get("candidates") or []:
        if isinstance(raw, OperationLifecycleState):
            rows.append(raw)
        elif isinstance(raw, dict):
            rows.append(OperationLifecycleState(**raw))
    if rows:
        return rows

    from aethos_core.operation_lifecycle.global_lifecycle_index import find_latest_logical_mutation

    return find_latest_logical_mutation(limit=5)


def store_pending_verification_disambiguation(
    *,
    session_id: str,
    intent: VerificationIntentType,
    original_text: str,
    candidates: list[Any],
) -> None:
    _PENDING[session_id] = {
        "intent": intent,
        "pending_intent": intent,
        "original_text": original_text,
        "awaiting": "target_selection",
        "candidate_operation_ids": [
            str(getattr(row, "execution_job_id", "") or "")
            for row in candidates
            if getattr(row, "execution_job_id", None)
        ],
        "candidates": [
            row.to_dict() if hasattr(row, "to_dict") else dict(row)
            for row in candidates
        ],
        "created_at": time(),
    }


def compose_verification_disambiguation_reply(
    *,
    intent: VerificationIntentType,
    candidates: list[Any],
) -> tuple[str, str, dict[str, str]]:
    lines = [
        "Which recent operation should I use?",
        "",
    ]
    for idx, state in enumerate(candidates[:5], start=1):
        lines.append(f"{idx}. **{state.target_path()}** — {state.operation.replace('_', ' ')}")
    lines.extend(
        [
            "",
            "Reply with the number, target path, or copied list item.",
        ]
    )
    meta = {
        "route_id": "post_mutation_verification",
        "post_mutation_verification_intent": intent,
        "awaiting": "target_selection",
        "candidate_count": str(len(candidates)),
    }
    return "\n".join(lines), "post_mutation_verification_disambiguation", meta


def resolve_pending_verification_selection(
    text: str,
    pending: dict[str, Any],
) -> tuple[VerificationTarget, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    candidates = _candidates_from_pending(pending)
    from aethos_core.operation_lifecycle.global_lifecycle_index import find_latest_mutation_by_target

    explicit = extract_explicit_path_target(raw)
    if explicit is not None:
        lifecycle = find_latest_mutation_by_target(
            provider=explicit.provider or "railway",
            project=explicit.project,
            environment=explicit.environment,
            service=explicit.service,
        )
        if lifecycle is not None:
            return explicit, lifecycle
        for state in candidates:
            if (
                _norm(state.project) == _norm(explicit.project)
                and _norm(state.environment) == _norm(explicit.environment)
                and _norm(state.service) == _norm(explicit.service)
            ):
                return explicit, state
        return explicit, None

    number_match = re.match(r"^\s*(\d+)\.?(?:\s|$|\*\*)", raw)
    if number_match:
        idx = int(number_match.group(1)) - 1
        if 0 <= idx < len(candidates):
            state = candidates[idx]
            return _target_from_state(state), state

    lowered = raw.lower()
    for state in candidates:
        path = state.target_path().lower()
        slash_path = path.replace(" / ", "/").lower()
        if path in lowered or slash_path in lowered.replace(" ", ""):
            return _target_from_state(state), state

    return None


def _norm(value: str | None) -> str:
    return str(value or "").strip().lower()


def classify_verification_intent(text: str, *, session_id: str = "default") -> VerificationIntentType | None:
    raw = (text or "").strip()
    if not raw:
        return None

    from aethos_core.operational_session.railway_service_hints import (
        is_railway_named_service_health_request,
        is_railway_named_service_log_request,
    )

    if is_railway_named_service_health_request(raw):
        return None
    if is_railway_named_service_log_request(raw, session_id=session_id):
        return None

    if _BEFORE_AFTER_RX.search(raw):
        return "before_after_change"
    if _FETCH_POST_RESTART_LOGS_RX.search(raw):
        return "fetch_post_restart_logs"
    if _STARTUP_LOG_RX.search(raw):
        return "startup_log_check"
    if _HOLD_RX.search(raw):
        return "hold_check"
    if _RECOVERY_RX.search(raw):
        return "recovery_check"
    if _VERIFY_HEALTH_RX.search(raw):
        return "verify_health"
    if re.search(r"\bfetch\s+logs\b", raw, re.I) and _POST_MUTATION_CONTEXT_RX.search(raw):
        return "fetch_post_restart_logs"
    if re.search(r"\b(check|show|read)\b.*\blogs?\b", raw, re.I) and _POST_MUTATION_CONTEXT_RX.search(raw):
        return "fetch_post_restart_logs"
    if re.search(r"\bverification\s+status\b", raw, re.I):
        return "verification_status"
    return None


def classify_verification_intent_with_context(
    text: str,
    *,
    session_id: str = "default",
) -> VerificationIntentType | None:
    intent = classify_verification_intent(text, session_id=session_id)
    if intent is not None:
        return intent
    if not recent_mutation_lifecycle_exists(session_id=session_id):
        return None
    lower = (text or "").strip().lower()
    if "what changed" in lower:
        return "before_after_change"
    if re.search(r"\b(check|show|read|fetch)\b.*\blogs?\b", lower):
        if parse_log_limit(text) is not None or "application started" in lower:
            return "startup_log_check"
        return "fetch_post_restart_logs"
    return None


def is_post_mutation_verification_intent(text: str, *, session_id: str = "default") -> bool:
    return classify_verification_intent_with_context(text, session_id=session_id) is not None


def parse_log_limit(text: str) -> int | None:
    from aethos_core.conversation.provider_memory.followup_intent_classifier import parse_log_limit as _parse

    return _parse(text)


def resolve_verification_target(
    text: str,
    *,
    session_id: str = "default",
) -> VerificationTarget | None:
    explicit = extract_explicit_path_target(text)
    if explicit is not None:
        return explicit

    from aethos_core.post_mutation_verification.verification_context_discovery import (
        discover_verification_lifecycle,
    )

    discovered = discover_verification_lifecycle(text, session_id=session_id)
    if discovered is not None:
        return VerificationTarget(
            provider=discovered.provider,
            project=discovered.project,
            environment=discovered.environment,
            service=discovered.service,
            target_path=discovered.target_path(),
            source="global_lifecycle_index",
        )

    from aethos_core.operation_lifecycle.lifecycle_resolver import _SERVICE_RX, get_latest_operation_state

    service = None
    match = _SERVICE_RX.search(text or "")
    if match:
        candidate = match.group(1)
        if not is_intent_word(candidate):
            service = candidate

    state = get_latest_operation_state(session_id=session_id, service=service, text=None)
    if state is None:
        from aethos_core.operation_lifecycle.lifecycle_resolver import find_latest_mutation_lifecycle_across_sessions

        state = find_latest_mutation_lifecycle_across_sessions(session_id=session_id, service=service)
    if state is None:
        return None
    return VerificationTarget(
        provider=state.provider,
        project=state.project,
        environment=state.environment,
        service=state.service,
        target_path=state.target_path(),
        source="lifecycle",
    )


def store_pending_verification_request(
    *,
    session_id: str,
    intent: VerificationIntentType,
    original_text: str,
) -> None:
    _PENDING[session_id] = {
        "intent": intent,
        "pending_intent": intent,
        "original_text": original_text,
        "awaiting": "target",
        "created_at": time(),
    }


def get_pending_verification_request(session_id: str) -> dict[str, Any] | None:
    return _PENDING.get(session_id)


def looks_like_verification_target_selection(text: str) -> bool:
    """Detect replies to post-mutation verification disambiguation prompts."""
    raw = (text or "").strip()
    if not raw:
        return False
    if re.match(r"^\s*\d+\.", raw):
        return True
    if re.search(
        r"^\s*\d+\.\s+\*\*[\w-]+\s*/\s*[\w-]+\s*/\s*[\w-]+\*\*\s*[—-]\s*(?:redeploy|restart)\b",
        raw,
        re.I | re.M,
    ):
        return True
    return False


def has_pending_verification_disambiguation(*, session_id: str = "default") -> bool:
    pending = get_pending_verification_request(session_id)
    if not pending:
        return False
    return pending.get("awaiting") in {"target_selection", "target"}


def clear_pending_verification_request(session_id: str) -> None:
    _PENDING.pop(session_id, None)


def continue_pending_verification_with_target(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.operational_session.railway_service_hints import (
        is_railway_named_service_health_request,
        is_railway_named_service_log_request,
    )

    if is_railway_named_service_health_request(text):
        clear_pending_verification_request(session_id)
        return None
    if is_railway_named_service_log_request(text, session_id=session_id):
        clear_pending_verification_request(session_id)
        return None

    pending = get_pending_verification_request(session_id)
    if pending is None:
        return None

    resolved = resolve_pending_verification_selection(text, pending)
    if resolved is None:
        return None

    target, lifecycle = resolved
    clear_pending_verification_request(session_id)
    intent = pending.get("pending_intent") or pending.get("intent") or "verify_health"
    return _route_with_target(
        intent,
        pending.get("original_text") or text,
        session_id=session_id,
        target=target,
        log_limit=parse_log_limit(pending.get("original_text") or text),
        lifecycle=lifecycle,
    )


def route_post_mutation_verification(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    continued = continue_pending_verification_with_target(raw, session_id=session_id)
    if continued is not None:
        return continued

    explicit = extract_explicit_path_target(raw)
    pending = get_pending_verification_request(session_id)
    if explicit is not None and pending is not None:
        from aethos_core.operation_lifecycle.global_lifecycle_index import find_latest_mutation_by_target

        lifecycle = find_latest_mutation_by_target(
            provider=explicit.provider or "railway",
            project=explicit.project,
            environment=explicit.environment,
            service=explicit.service,
        )
        clear_pending_verification_request(session_id)
        return _route_with_target(
            pending.get("pending_intent") or pending.get("intent") or "verify_health",
            str(pending.get("original_text") or raw),
            session_id=session_id,
            target=explicit,
            log_limit=parse_log_limit(str(pending.get("original_text") or raw)),
            lifecycle=lifecycle,
        )

    if explicit is not None and pending is None:
        from aethos_core.operation_lifecycle.global_lifecycle_index import find_latest_mutation_by_target
        from aethos_core.post_mutation_verification.verification_reply_composer import (
            compose_path_target_lifecycle_reply,
        )

        lifecycle = find_latest_mutation_by_target(
            provider=explicit.provider or "railway",
            project=explicit.project,
            environment=explicit.environment,
            service=explicit.service,
        )
        if lifecycle is not None and classify_verification_intent_with_context(raw, session_id=session_id) is None:
            return compose_path_target_lifecycle_reply(lifecycle=lifecycle, target_path=explicit.target_path)

    intent = classify_verification_intent_with_context(raw, session_id=session_id)
    if intent is None:
        return None

    if not recent_mutation_lifecycle_exists(session_id=session_id):
        store_pending_verification_request(session_id=session_id, intent=intent, original_text=raw)
        return None

    candidates = list_recent_mutation_lifecycles(session_id=session_id, limit=5)
    if len(candidates) == 1:
        state = candidates[0]
        return _route_with_target(
            intent,
            raw,
            session_id=session_id,
            target=_target_from_state(state),
            log_limit=parse_log_limit(raw),
            lifecycle=state,
        )
    if len(candidates) > 1:
        store_pending_verification_disambiguation(
            session_id=session_id,
            intent=intent,
            original_text=raw,
            candidates=candidates,
        )
        return compose_verification_disambiguation_reply(intent=intent, candidates=candidates)

    target = resolve_verification_target(raw, session_id=session_id)
    if target is None:
        store_pending_verification_request(session_id=session_id, intent=intent, original_text=raw)
        return None

    return _route_with_target(intent, raw, session_id=session_id, target=target, log_limit=parse_log_limit(raw))


def _route_with_target(
    intent: VerificationIntentType,
    text: str,
    *,
    session_id: str,
    target: VerificationTarget,
    log_limit: int | None = None,
    lifecycle: Any | None = None,
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.operation_lifecycle.lifecycle_resolver import get_latest_operation_state
    from aethos_core.operation_lifecycle.operation_state_store import OperationLifecycleState
    from aethos_core.post_mutation_verification.verification_reply_composer import (
        compose_did_hold_reply,
        compose_did_recover_reply,
        compose_fetch_logs_reply,
        compose_startup_log_check_reply,
        compose_verify_health_reply,
        compose_what_changed_reply,
    )

    if lifecycle is None:
        from aethos_core.post_mutation_verification.verification_context_discovery import (
            discover_verification_lifecycle,
        )

        lifecycle = discover_verification_lifecycle(text, session_id=session_id)

    if lifecycle is None:
        lifecycle = get_latest_operation_state(
            session_id=session_id,
            provider=target.provider,
            service=target.service,
            text=None,
        )
    if lifecycle is None:
        from aethos_core.operation_lifecycle.lifecycle_resolver import find_latest_mutation_lifecycle_across_sessions

        lifecycle = find_latest_mutation_lifecycle_across_sessions(
            session_id=session_id,
            provider=target.provider,
            service=target.service,
        )
    if lifecycle is None and target.service:
        lifecycle = OperationLifecycleState(
            provider=target.provider or "railway",
            project=target.project,
            environment=target.environment,
            service=target.service,
            operation="restart",
            session_id=session_id,
            match_key="",
        )

    if intent == "verify_health":
        return compose_verify_health_reply(session_id=session_id, text=text, lifecycle=lifecycle)
    if intent in {"recovery_check", "verification_status"}:
        return compose_did_recover_reply(session_id=session_id, text=text, lifecycle=lifecycle)
    if intent == "hold_check":
        return compose_did_hold_reply(session_id=session_id, text=text, lifecycle=lifecycle)
    if intent == "before_after_change":
        return compose_what_changed_reply(session_id=session_id, text=text, lifecycle=lifecycle)
    if intent == "startup_log_check":
        return compose_startup_log_check_reply(
            session_id=session_id,
            text=text,
            lifecycle=lifecycle,
            log_limit=log_limit or 5,
        )
    if intent == "fetch_post_restart_logs":
        return compose_fetch_logs_reply(
            session_id=session_id,
            text=text,
            lifecycle=lifecycle,
            log_limit=log_limit,
        )
    return None


def reset_pending_verification_for_tests() -> None:
    _PENDING.clear()
