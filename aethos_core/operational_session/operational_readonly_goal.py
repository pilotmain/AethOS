# SPDX-License-Identifier: Apache-2.0
"""Readonly operational goal classification."""

from __future__ import annotations

import re
from dataclasses import dataclass

from aethos_core.operational_session.operational_session import OperationalSession
from aethos_core.operational_session.session_subject import SessionSubject

_LOG_RX = re.compile(
    r"\b("
    r"(?:give\s+me|show\s+me|show|get|fetch|check|tail|read|list)(?:\s+\w+){0,4}\s+(?:the\s+)?(?:\d+\s+)?(?:top|latest|recent)?\s*\d*\s*logs?"
    r"|(?:top|latest|recent)\s+\d+\s+logs?"
    r"|logs?\s+for\s+(?:each|[a-z0-9][\w.-]+)"
    r"|(?:can you|please)\s+give\s+me\s+(?:that|those)"
    r"|(?:vercel|railway)\s+logs?"
    r"|(?:vercel|railway)\s+\w+\s+logs?"
    r")\b",
    re.I,
)
_FOLLOWUP_REPEAT_RX = re.compile(
    r"\b("
    r"give me that|can you give me that|that's what i asked|top \d+ only|just the logs|same thing"
    r")\b",
    re.I,
)
_INVENTORY_RX = re.compile(
    r"\b(show|list|what are)\b.*\b(projects?|services?|inventory|apps?)\b"
    r"|\b(projects?|services?)\b.*\b(list|inventory)\b"
    r"|\bproject\s+list\b",
    re.I,
)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)
_DEPLOYMENTS_LIST_RX = re.compile(r"\b(deployments?|deployment list)\b", re.I)
_HEALTH_RX = re.compile(r"\bhealth\b|\bhealthy\b|\b(is it up|running|online)\b", re.I)
_DEPLOYMENT_RX = re.compile(
    r"\b(deployment status|show deployment|latest deployment|deployment state|deploy status)\b",
    re.I,
)
_MUTATION_RX = re.compile(
    r"\b(redeploy|restart|deploy(?:ment)?|approve|set env|configure env|rollback|mutation)\b",
    re.I,
)
_VALIDATE_CONNECTION_RX = re.compile(
    r"\b(validate|check|test)\b.*\b(vercel|railway)\b.*\b(connection|token|credential)s?\b"
    r"|\b(validate|check|test)\b.*\b(connection|token|credential)s?\b.*\b(vercel|railway)\b"
    r"|\b(show|check)\b.*\b(vercel|railway)\b.*\bconnection\b",
    re.I,
)


@dataclass(frozen=True)
class ReadonlyGoal:
    operation: str
    log_limit: int = 5
    user_text: str = ""
    is_followup: bool = False


def classify_readonly_goal(text: str, *, subject: SessionSubject, session: OperationalSession) -> ReadonlyGoal | None:
    raw = (text or "").strip()
    if not raw:
        return None
    readonly_deploy_query = bool(
        _DEPLOYMENT_RX.search(raw)
        or (
            _DEPLOYMENTS_LIST_RX.search(raw)
            and (_VERCEL_RX.search(raw) or subject.provider == "vercel")
        )
        or (
            re.search(r"\brailway\b", raw, re.I)
            and re.search(r"\b(deployment|deployments?|env|environment|config)\b", raw, re.I)
        )
    )
    if _MUTATION_RX.search(raw) and not _LOG_RX.search(raw) and not readonly_deploy_query:
        return None

    if _VALIDATE_CONNECTION_RX.search(raw):
        return ReadonlyGoal(operation="validate_connection", user_text=raw)

    limit = _parse_log_limit(raw) or session.context.last_log_limit or 5

    if _FOLLOWUP_REPEAT_RX.search(raw) and session.context.last_operation:
        op = session.context.last_operation
        if op == "list_inventory" and (_parse_log_limit(raw) or "only" in raw.lower()):
            op = "fetch_logs"
        return ReadonlyGoal(
            operation=op,
            log_limit=limit,
            user_text=raw,
            is_followup=True,
        )

    if _parse_log_limit(raw) and not _LOG_RX.search(raw) and session.subject.provider:
        return ReadonlyGoal(operation="fetch_logs", log_limit=limit, user_text=raw, is_followup=True)

    if _LOG_RX.search(raw):
        return ReadonlyGoal(operation="fetch_logs", log_limit=limit, user_text=raw)

    if _INVENTORY_RX.search(raw):
        from aethos_core.operational_session.router_retirement import vercel_reference_lane_enabled

        if _VERCEL_RX.search(raw) and vercel_reference_lane_enabled():
            return ReadonlyGoal(operation="list_inventory", user_text=raw)
        if re.search(r"\bservices?\b", raw, re.I) and not re.search(r"\bprojects?\b", raw, re.I):
            return ReadonlyGoal(operation="list_services", user_text=raw)
        return ReadonlyGoal(operation="list_inventory", user_text=raw)

    if _DEPLOYMENTS_LIST_RX.search(raw) and (_VERCEL_RX.search(raw) or subject.provider == "vercel"):
        from aethos_core.operational_session.router_retirement import vercel_reference_lane_enabled

        if vercel_reference_lane_enabled():
            return ReadonlyGoal(operation="list_deployments", log_limit=limit, user_text=raw)

    if _HEALTH_RX.search(raw):
        return ReadonlyGoal(operation="health_check", user_text=raw)

    if _DEPLOYMENT_RX.search(raw):
        return ReadonlyGoal(operation="deployment_status", user_text=raw)

    if re.search(r"\bwhat about\b", raw, re.I) and subject.provider and (subject.service or subject.services):
        op = session.context.last_operation or "fetch_logs"
        if op == "list_inventory":
            op = "fetch_logs"
        return ReadonlyGoal(operation=op, log_limit=limit, user_text=raw, is_followup=True)

    if session.context.last_operation and subject.provider:
        if re.search(r"\b(status|update|report back|what about)\b", raw, re.I):
            op = session.context.last_operation
            if op == "fetch_logs":
                return ReadonlyGoal(operation="fetch_logs", log_limit=limit, user_text=raw, is_followup=True)
            return ReadonlyGoal(operation="deployment_status", user_text=raw, is_followup=True)

    return None


def _parse_log_limit(text: str) -> int | None:
    from aethos_core.conversation.provider_memory.followup_intent_classifier import parse_log_limit

    return parse_log_limit(text)


def is_operational_kernel_candidate(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.execution_brain.goal_planner import _is_mutation_execute_only, plan_operational_goal
    from aethos_core.operational_session.active_subject_resolver import resolve_active_subject
    from aethos_core.operational_session.operational_session import load_operational_session

    raw = (text or "").strip()
    if not raw:
        return False

    session = load_operational_session(session_id=session_id)
    resolved = resolve_active_subject(raw, session_id=session_id)
    planned = plan_operational_goal(raw, subject=resolved.subject, session=session)
    if planned is not None and planned.kind in {"deploy_planning", "continue_plan", "readonly_execute"}:
        if planned.kind == "deploy_planning" and _is_mutation_execute_only(raw):
            pass
        else:
            return True

    if _MUTATION_RX.search(raw) and not _LOG_RX.search(raw):
        return False

    goal = classify_readonly_goal(raw, subject=resolved.subject, session=session)
    if goal is not None and (resolved.subject.provider or session.has_active_subject()):
        return True
    if goal is not None and resolved.source in {"explicit", "registry"}:
        return True
    if goal is not None and re.search(r"\b(vercel|railway)\b", raw, re.I):
        return True
    return False
