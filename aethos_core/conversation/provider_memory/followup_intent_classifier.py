# SPDX-License-Identifier: Apache-2.0
"""Provider-generic follow-up intent classification from natural language."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_LOG_LIMIT_RX = re.compile(
    r"\b(?:top|latest|last|recent)\s+(\d{1,2})\s+(?:latest\s+)?(?:log(?:s)?|entries?|lines?)\b",
    re.I,
)
_LOG_LIMIT_ALT_RX = re.compile(
    r"\b(\d{1,2})\s+(?:latest|recent|most\s+recent)\s+log(?:s)?\b",
    re.I,
)
_LOG_FILTER_RX = re.compile(r"\b(?:latest|recent|last)\s+(\d{1,2})\s+errors?\b", re.I)

_VERIFY_RX = re.compile(
    r"\b("
    r"did\s+(?:the\s+)?(?:restart|redeploy|deploy|mutation|operation)\s+(?:actually\s+)?(?:happen(?:ed|s)?|work(?:ed|s)?|go\s+through|succeed(?:ed|s)?)"
    r"|did\s+it\s+(?:actually\s+)?(?:happen(?:ed|s)?|work(?:ed|s)?|go\s+through|really\s+happen)"
    r"|did\s+(?:the\s+)?restart\s+(?:actually\s+)?(?:happen(?:ed|s)?|work(?:ed|s)?)"
    r"|(?:check|see|confirm|verify)\s+(?:if|whether)\s+(?:it|the\s+restart|restart)\s+(?:actually\s+)?(?:happened|restarted|went\s+through|worked)"
    r"|(?:check|see|confirm|verify)\s+(?:the\s+)?restart\s+(?:actually\s+)?(?:happened|worked|went\s+through)"
    r"|confirm\s+(?:the\s+)?restart"
    r"|verify\s+(?:the\s+)?(?:restart|operation|redeploy)"
    r"|any\s+proof"
    r"|did\s+it\s+really\s+(?:happen|go\s+through|work|restart)"
    r"|restart\s+(?:actually\s+)?(?:happened|happend|worked|went\s+through)"
    r")\b",
    re.I,
)
_LOGS_RX = re.compile(
    r"\b("
    r"(?:read|check|show|get|fetch|give\s+me|list|tail)\s+(?:the\s+)?(?:\d+\s+)?(?:latest|recent|top)?\s*log(?:s|ging)?"
    r"|(?:latest|recent|top)\s+(?:\d+\s+)?log(?:s)?"
    r"|log(?:s)?\s+(?:after|since)\s+(?:restart|approval|redeploy)"
    r"|give\s+me\s+(?:the\s+)?(?:top|latest|recent)\s+\d*\s*log"
    r")\b",
    re.I,
)
_TIMESTAMP_RX = re.compile(
    r"\b("
    r"(?:last|latest).{0,24}timestamp"
    r"|timestamp.{0,24}(?:after|since).{0,24}(?:restart|approval|redeploy)"
    r"|when\s+was\s+the\s+last\s+log"
    r")\b",
    re.I,
)
_STATUS_RX = re.compile(
    r"\b("
    r"can\s+you\s+check(?:\s+and\s+report\s+back)?"
    r"|check\s+and\s+report\s+back"
    r"|what(?:'s| is)\s+the\s+status"
    r"|status update"
    r"|report\s+back"
    r"|what\s+happened(?:\s+after\s+approval)?"
    r"|is\s+it\s+done(?:\s+now)?"
    r"|is\s+it\s+still\s+stabiliz(?:ing|e)"
    r"|what\s+changed"
    r")\b",
    re.I,
)
_WATCH_RX = re.compile(
    r"\b("
    r"update\s+me\s+(?:once|when)"
    r"|notify\s+me\s+when"
    r"|let\s+me\s+know\s+when"
    r"|report\s+back\s+when"
    r"|watch\s+(?:the|this)\s+(?:restart|operation|redeploy)"
    r")\b",
    re.I,
)
_FAILURE_RX = re.compile(r"\bwhy\s+did\s+it\s+fail\b|\bwhy\s+failed\b|\bwhy\s+did\s+(?:the\s+)?(?:restart|operation)\s+fail\b", re.I)
_RETRY_RX = re.compile(r"\b(?:retry|try\s+again|please\s+do)\b", re.I)
_HEALTH_CHECK_RX = re.compile(
    r"\b("
    r"check\s+(?:the\s+)?service\s+health"
    r"|service\s+health"
    r"|check\s+health"
    r"|health\s+check"
    r"|check\s+status"
    r"|check\s+(?:the\s+)?status"
    r"|what(?:'s| is)\s+the\s+status"
    r"|is\s+it\s+(?:healthy|running|up|online)"
    r")\b",
    re.I,
)


@dataclass
class FollowupIntent:
    intent: str
    user_text: str = ""
    log_limit: int = 5
    log_filter: str | None = None
    include_verification: bool = False
    include_logs: bool = False
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "user_text": self.user_text,
            "log_limit": self.log_limit,
            "log_filter": self.log_filter,
            "include_verification": self.include_verification,
            "include_logs": self.include_logs,
            "parameters": dict(self.parameters),
        }


def parse_log_limit(text: str) -> int | None:
    raw = text or ""
    for rx in (_LOG_LIMIT_RX, _LOG_LIMIT_ALT_RX):
        match = rx.search(raw)
        if match:
            return max(1, min(50, int(match.group(1))))
    if _LOG_FILTER_RX.search(raw):
        match = _LOG_FILTER_RX.search(raw)
        if match:
            return max(1, min(50, int(match.group(1))))
    return None


def parse_log_filter(text: str) -> str | None:
    lower = (text or "").lower()
    if re.search(r"\berrors?\b", lower) and "log" in lower:
        return "error"
    if re.search(r"\bwarnings?\b", lower) and "log" in lower:
        return "warn"
    return None


def classify_followup_intent(text: str, active_thread: Any | None = None) -> FollowupIntent | None:
    raw = (text or "").strip()
    if not raw or active_thread is None:
        return None

    from aethos_core.provider_readonly_intent.readonly_intent_classifier import should_yield_active_thread_for_readonly

    if should_yield_active_thread_for_readonly(raw):
        return None

    session_id = str(getattr(active_thread, "session_id", "") or "default")
    from aethos_core.operational_planner.scope_classifier import is_provider_wide_phrase

    if is_provider_wide_phrase(raw):
        return None

    log_limit = parse_log_limit(raw) or 5
    log_filter = parse_log_filter(raw)
    wants_verify = bool(_VERIFY_RX.search(raw))
    wants_logs = bool(_LOGS_RX.search(raw))
    wants_timestamp = bool(_TIMESTAMP_RX.search(raw))

    if _HEALTH_CHECK_RX.search(raw):
        return FollowupIntent("health_check", user_text=raw, include_verification=True)

    if _FAILURE_RX.search(raw):
        return FollowupIntent("explain_failure", user_text=raw)

    if wants_timestamp and not wants_logs:
        return FollowupIntent("fetch_latest_logs", user_text=raw, log_limit=1, include_verification=True)

    if wants_verify and wants_logs:
        return FollowupIntent(
            "fetch_top_n_logs",
            user_text=raw,
            log_limit=log_limit,
            log_filter=log_filter,
            include_verification=True,
            include_logs=True,
        )

    if wants_verify:
        return FollowupIntent("verify_operation", user_text=raw, include_verification=True)

    if wants_logs or parse_log_limit(raw) is not None:
        return FollowupIntent(
            "fetch_top_n_logs" if log_limit != 5 or parse_log_limit(raw) else "fetch_logs",
            user_text=raw,
            log_limit=log_limit,
            log_filter=log_filter,
            include_logs=True,
        )

    if _WATCH_RX.search(raw) or ("update me" in raw.lower() and "status" in raw.lower()):
        return FollowupIntent("watch_until_done", user_text=raw)

    if _STATUS_RX.search(raw):
        return FollowupIntent("get_status", user_text=raw, include_verification=True)

    from aethos_core.task_frame.retry_active_operation import is_retry_intent

    session_id = str(getattr(active_thread, "session_id", "") or "default")
    if is_retry_intent(raw, session_id=session_id) or _RETRY_RX.search(raw):
        return FollowupIntent("retry_operation", user_text=raw)

    from aethos_core.provider_topology.source_binding_correction import should_handle_binding_correction

    if should_handle_binding_correction(raw, session_id=session_id):
        return FollowupIntent("reconcile_source_binding", user_text=raw)

    if "what were we doing" in raw.lower() or "what were we talking about" in raw.lower():
        return None

    return None


def is_operational_followup_request(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

    thread = get_active_operational_thread(session_id)
    if thread is None:
        return False
    return classify_followup_intent(text, thread) is not None
