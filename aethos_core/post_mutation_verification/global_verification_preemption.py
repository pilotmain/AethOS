# SPDX-License-Identifier: Apache-2.0
"""Global post-mutation verification preemption for live chat paths."""

from __future__ import annotations

from aethos_core.chat.service import ChatTurnResult
from aethos_core.operation_lifecycle.global_lifecycle_index import find_latest_mutation_by_target
from aethos_core.post_mutation_verification.verification_context_discovery import (
    discover_verification_lifecycle,
    global_mutation_lifecycle_exists,
)
from aethos_core.post_mutation_verification.verification_intent_router import (
    extract_explicit_path_target,
    get_pending_verification_request,
    is_post_mutation_verification_intent,
    recent_mutation_lifecycle_exists,
    resolve_pending_verification_selection,
    route_post_mutation_verification,
)

_VERIFICATION_LIKE_RX = __import__("re").compile(
    r"\b("
    r"verify\s+health|check\s+health|health\s+check"
    r"|did\s+it\s+recover|did\s+it\s+hold|did\s+recovery\s+hold"
    r"|what\s+changed"
    r"|fetch\s+logs|post[- ]restart\s+logs|logs\s+after\s+restart"
    r"|top\s+\d+\s+logs|latest\s+logs|startup\s+logs?"
    r"|application\s+started|see\s+if\s+application\s+started"
    r")\b",
    __import__("re").I,
)


def is_global_verification_query(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    from aethos_core.operational_session.railway_service_hints import (
        is_railway_named_service_health_request,
        is_railway_named_service_log_request,
    )

    if is_railway_named_service_health_request(raw):
        return False
    if is_railway_named_service_log_request(raw, session_id=session_id):
        return False
    if is_pending_verification_target_reply(raw, session_id=session_id):
        return True
    if is_post_mutation_verification_intent(raw, session_id=session_id):
        return True
    if _VERIFICATION_LIKE_RX.search(raw) and recent_mutation_lifecycle_exists(session_id=session_id):
        return True
    explicit = extract_explicit_path_target(raw)
    if explicit is not None:
        lifecycle = find_latest_mutation_by_target(
            provider=explicit.provider or "railway",
            project=explicit.project,
            environment=explicit.environment,
            service=explicit.service,
        )
        if lifecycle is not None:
            return True
    return False


def is_pending_verification_target_reply(text: str, *, session_id: str = "default") -> bool:
    pending = get_pending_verification_request(session_id)
    if pending is not None and resolve_pending_verification_selection(text, pending) is not None:
        return True
    explicit = extract_explicit_path_target(text)
    if explicit is None:
        return False
    if pending is not None:
        return True
    lifecycle = find_latest_mutation_by_target(
        provider=explicit.provider or "railway",
        project=explicit.project,
        environment=explicit.environment,
        service=explicit.service,
    )
    return lifecycle is not None


def should_preempt_to_post_mutation_verification(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.operational_target_resolution.explicit_target_resolver import (
        explicit_target_overrides_session_context,
        should_route_explicit_provider_diagnostics,
    )

    if should_route_explicit_provider_diagnostics(text, session_id=session_id):
        return False
    if explicit_target_overrides_session_context(text, session_id=session_id):
        return False

    if is_pending_verification_target_reply(text, session_id=session_id):
        return True
    if not is_global_verification_query(text, session_id=session_id):
        return False
    if get_pending_verification_request(session_id) is not None:
        return True
    if discover_verification_lifecycle(text, session_id=session_id) is not None:
        return True
    return global_mutation_lifecycle_exists()


def route_global_verification_query(
    text: str,
    *,
    session_id: str = "default",
) -> ChatTurnResult | None:
    """Route verification-like prompts through post-mutation verification."""
    raw = (text or "").strip()
    if not raw:
        return None

    if not should_preempt_to_post_mutation_verification(raw, session_id=session_id):
        return None

    explicit = extract_explicit_path_target(raw)
    pending_before = get_pending_verification_request(session_id)

    routed = route_post_mutation_verification(raw, session_id=session_id)
    if routed is None:
        return None

    reply, intent, meta = routed
    merged = dict(meta)
    merged["route_id"] = "post_mutation_verification"
    merged["global_verification_preemption"] = "true"
    if explicit is not None and pending_before is not None:
        merged["pending_verification_continued"] = "true"
        reply = (
            f"Using **{explicit.target_path}** for the pending verification request.\n\n"
            f"{reply}"
        )
    return ChatTurnResult(
        reply=reply,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=merged,
    )


def verification_preemption_blocks_route(text: str, *, session_id: str = "default") -> bool:
    """True when downstream routes must defer to post-mutation verification."""
    return should_preempt_to_post_mutation_verification(text, session_id=session_id)
