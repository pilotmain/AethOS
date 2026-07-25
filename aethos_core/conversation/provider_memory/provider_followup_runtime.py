# SPDX-License-Identifier: Apache-2.0
"""Shared provider follow-up runtime — classify, collect evidence, compose reply."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.conversation.provider_memory.followup_intent_classifier import FollowupIntent, classify_followup_intent
from aethos_core.conversation.provider_memory.provider_evidence_adapter import (
    ProviderLogEntry,
    load_evidence_adapter,
)


@dataclass
class FollowupResult:
    intent: str
    provider: str
    thread_path: str
    execution_job_id: str = ""
    conclusion: str = ""
    body: str = ""
    logs: list[dict[str, Any]] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    watch_created: bool = False
    meta: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "provider": self.provider,
            "thread_path": self.thread_path,
            "execution_job_id": self.execution_job_id,
            "conclusion": self.conclusion,
            "body": self.body,
            "logs": list(self.logs),
            "evidence": dict(self.evidence),
            "watch_created": self.watch_created,
            "meta": dict(self.meta),
        }


def get_active_operational_thread(session_id: str):
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread, is_thread_expired

    thread = get_active_thread(session_id=session_id)
    if thread is None or is_thread_expired(thread):
        from aethos_core.aethos_identity.context_reconstructor import maybe_reconstruct_active_thread

        reconstructed = maybe_reconstruct_active_thread(session_id=session_id)
        if reconstructed and reconstructed.thread is not None and not is_thread_expired(reconstructed.thread):
            return reconstructed.thread
        return None
    if thread.status in {"completed", "cancelled", "superseded"}:
        return None
    return thread


def handle_provider_followup(*, session_id: str, user_text: str) -> FollowupResult | None:
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
        request_overrides_stale_operational_thread,
    )

    if request_overrides_stale_operational_thread(user_text, session_id=session_id):
        return None

    thread = get_active_operational_thread(session_id)
    if thread is None:
        return None

    intent = classify_followup_intent(user_text, thread)
    if intent is None:
        return None

    if intent.intent == "retry_operation":
        return _handle_retry(intent, thread, session_id=session_id)
    if intent.intent == "reconcile_source_binding":
        return _handle_binding(intent, thread, session_id=session_id)

    provider = str(getattr(thread, "provider", "") or "railway")
    adapter = load_evidence_adapter(provider)
    job = _resolve_execution_job(thread, session_id=session_id)
    path = thread.service_path()
    job_id = str(getattr(job, "id", "") or getattr(thread, "execution_job_id", "") or "unknown")

    if adapter is None:
        return FollowupResult(
            intent=intent.intent,
            provider=provider,
            thread_path=path,
            execution_job_id=job_id,
            body=(
                f"I still have the active operational thread for **{path}**, "
                f"but I do not have a follow-up adapter for provider `{provider}` yet."
            ),
        )

    from aethos_core.conversation.provider_memory.adapters.stub_adapter import StubEvidenceAdapter

    if isinstance(adapter, StubEvidenceAdapter) and intent.intent not in {
        "watch_until_done",
        "explain_failure",
        "what_changed",
    }:
        return FollowupResult(
            intent=intent.intent,
            provider=provider,
            thread_path=path,
            execution_job_id=job_id,
            body=adapter.capability_gap_message(thread, action=intent.intent),
        )

    if intent.intent == "explain_failure":
        body = adapter.explain_failure(thread, job)
        return FollowupResult(
            intent=intent.intent,
            provider=provider,
            thread_path=path,
            execution_job_id=job_id,
            body=body,
        )

    if intent.intent == "watch_until_done":
        adapter.watch_until_done(thread, job, session_id=session_id)
        status = adapter.get_operation_status(thread, job)
        body = (
            f"I'll watch the active **{provider.title()}** **{str(getattr(thread, 'operation', 'operation') or 'operation').replace('_', ' ')}** for **{path}**.\n\n"
            "Current state:\n"
            f"- Execution job: `{job_id}`\n"
            f"- Status: {status.status_label}\n"
            f"- Verification: {status.verification_label}\n\n"
            "I'll report back when the operation is verified, fails, or becomes stale."
        )
        result = FollowupResult(
            intent=intent.intent,
            provider=provider,
            thread_path=path,
            execution_job_id=job_id,
            body=body,
            watch_created=True,
            meta={"watch_created": "true"},
        )
        _persist_followup_memory(thread, result, session_id=session_id)
        return result

    if intent.intent == "what_changed":
        body = (
            f"We were working on a governed **{provider}** **{str(getattr(thread, 'operation', 'operation') or 'operation').replace('_', ' ')}** for **{path}**.\n\n"
            f"Latest result: **{getattr(thread, 'status', 'unknown')}** — {getattr(thread, 'last_system_result', 'execution updated') or 'execution updated'}.\n\n"
            f"Execution job: `{job_id}`."
        )
        return FollowupResult(intent=intent.intent, provider=provider, thread_path=path, execution_job_id=job_id, body=body)

    if intent.intent == "fetch_latest_logs":
        return _compose_timestamp_reply(intent, thread, job, adapter, path=path, job_id=job_id, session_id=session_id)

    if intent.intent in {"fetch_logs", "fetch_top_n_logs"} or intent.include_logs:
        return _compose_logs_reply(intent, thread, job, adapter, path=path, job_id=job_id, session_id=session_id)

    if intent.intent in {"verify_operation", "get_status"} or intent.include_verification:
        return _compose_verify_reply(intent, thread, job, adapter, path=path, job_id=job_id, session_id=session_id)

    if intent.intent == "health_check":
        return _compose_health_reply(intent, thread, job, adapter, path=path, job_id=job_id, session_id=session_id)

    return FollowupResult(
        intent=intent.intent,
        provider=provider,
        thread_path=path,
        execution_job_id=job_id,
        body=f"I have the active **{provider}** thread for **{path}**, but I could not execute follow-up `{intent.intent}`.",
    )


def compose_followup_reply(result: FollowupResult) -> tuple[str, str, dict[str, str]]:
    legacy = {
        "verify_operation": "check_logs",
        "fetch_logs": "check_logs",
        "fetch_top_n_logs": "check_logs",
        "fetch_latest_logs": "get_latest_log_timestamp",
        "get_status": "check_status",
        "watch_until_done": "create_completion_watch",
        "explain_failure": "explain_failure",
        "retry_operation": "retry_operation",
        "reconcile_source_binding": "reconcile_source_binding",
        "what_changed": "thread_recall",
        "health_check": "check_status",
    }
    action = legacy.get(result.intent, result.intent)
    if result.meta.get("intent"):
        intent = str(result.meta["intent"])
    else:
        intent = f"actionable_{action}"
    meta = {k: str(v) for k, v in result.meta.items() if k != "intent"}
    meta.setdefault("execution_job_id", result.execution_job_id)
    meta.setdefault("provider", result.provider)
    meta.setdefault("action_type", result.intent)
    if result.conclusion:
        meta.setdefault("conclusion", result.conclusion)
    if result.watch_created:
        meta.setdefault("watch_created", "true")
    return result.body, intent, meta


def _logs_older_than_approval(verification: Any) -> bool:
    return bool(
        verification.approval_time
        and verification.latest_log_timestamp
        and verification.timestamps_available
        and not verification.timestamp_after_approval
    )


def _restart_verification_label(verification: Any) -> str:
    if verification.conclusion in {"restart_verified", "restart_evidence_detected"}:
        return "verified"
    if _logs_older_than_approval(verification):
        return "still unconfirmed"
    if verification.conclusion == "still_stabilizing":
        return "still stabilizing"
    if verification.conclusion in {"logs_unavailable", "logs_without_timestamps", "inconclusive"}:
        return "unconfirmed"
    return "unconfirmed"


def _stale_log_disclaimer(verification: Any) -> str:
    if not _logs_older_than_approval(verification):
        return ""
    return (
        "\n\nThese logs are older than the restart approval time:\n"
        f"- approval time: `{verification.approval_time}`\n"
        f"- latest log time: `{verification.latest_log_timestamp}`\n\n"
        "Conclusion:\n"
        "These logs do not prove the restart happened. Restart verification remains unconfirmed."
    )


def _compose_health_reply(
    intent: FollowupIntent,
    thread: Any,
    job: Any | None,
    adapter: Any,
    *,
    path: str,
    job_id: str,
    session_id: str,
) -> FollowupResult:
    provider = str(getattr(thread, "provider", "") or adapter.provider)
    verification = adapter.verify_operation(thread, job)
    conclusion_label = _human_conclusion(verification.conclusion)
    verification_label = _restart_verification_label(verification)

    body = (
        f"I checked service health for the active **{provider.title()}** target: **{path}**.\n\n"
        f"Current health: **{verification.service_health}**\n"
        f"Restart verification: **{verification_label}**\n"
    )
    if _logs_older_than_approval(verification):
        body += (
            f"\nReason: latest provider logs are older than the restart approval time "
            f"(`{verification.approval_time}` vs latest `{verification.latest_log_timestamp}`).\n"
            "These logs do not prove the restart happened."
        )
    elif verification.conclusion == "still_stabilizing":
        body += (
            "\nReason: the provider command was submitted and I am still waiting for post-approval evidence."
        )
    elif verification.logs_unavailable or not verification.timestamps_available:
        body += "\nReason: no usable post-approval log evidence is available yet."

    body += f"\n\nConclusion:\n**{conclusion_label}**"

    result = FollowupResult(
        intent=intent.intent,
        provider=provider,
        thread_path=path,
        execution_job_id=job_id,
        conclusion=verification.conclusion,
        body=body,
        evidence=verification.to_dict(),
    )
    _persist_followup_memory(thread, result, session_id=session_id, verification=verification)
    return result


def _compose_verify_reply(
    intent: FollowupIntent,
    thread: Any,
    job: Any | None,
    adapter: Any,
    *,
    path: str,
    job_id: str,
    session_id: str,
) -> FollowupResult:
    provider = str(getattr(thread, "provider", "") or adapter.provider)
    verification = adapter.verify_operation(thread, job)
    status = adapter.get_operation_status(thread, job)
    conclusion_label = _human_conclusion(verification.conclusion)

    if verification.logs_unavailable:
        body = (
            f"I checked the active **{provider.title()}** **{str(getattr(thread, 'operation', 'restart') or 'restart').replace('_', ' ')}** for **{path}**.\n\n"
            "Evidence:\n"
            f"- Execution job: `{job_id}`\n"
            f"- Provider command: **{verification.provider_command}**\n"
            f"- Restart evidence: **{status.restart_evidence}**\n"
            f"- Latest log timestamp: unavailable\n"
            f"- Service health: **{verification.service_health}**\n\n"
            "Conclusion:\n"
            f"**{conclusion_label}** — no post-operation log evidence is stored yet."
        )
    elif not verification.timestamps_available:
        body = (
            f"I checked the active **{provider.title()}** **{str(getattr(thread, 'operation', 'restart') or 'restart').replace('_', ' ')}** for **{path}**.\n\n"
            "Evidence:\n"
            f"- Execution job: `{job_id}`\n"
            f"- Provider command: **{verification.provider_command}**\n"
            f"- Restart evidence: **{status.restart_evidence}**\n"
            "- Latest log timestamp: unavailable\n"
            f"- Service health: **{verification.service_health}**\n\n"
            "Railway returned recent logs, but no timestamp was available in the log payload. "
            "I cannot use these logs as restart proof yet.\n\n"
            "Conclusion:\n"
            f"**{conclusion_label}**"
        )
    else:
        latest_msg = ""
        logs = adapter.get_latest_logs(thread, job, limit=1)
        if logs:
            latest_msg = logs[0].message
        startup = "yes" if verification.startup_after_approval else "no"
        body = (
            f"I checked the active **{provider.title()}** **{str(getattr(thread, 'operation', 'restart') or 'restart').replace('_', ' ')}** for **{path}**.\n\n"
            "Evidence:\n"
            f"- Execution job: `{job_id}`\n"
            f"- Provider command: **{verification.provider_command}**\n"
            f"- Restart evidence: **{status.restart_evidence}**\n"
            f"- Latest log timestamp: `{verification.latest_log_timestamp or 'unknown'}`\n"
            f"- Approval time: `{verification.approval_time or 'unknown'}`\n"
            f"- Startup log observed after approval: **{startup}**\n"
            f"- Service health: **{verification.service_health}**\n"
        )
        if latest_msg:
            body += f"- Recent log: \"{latest_msg}\"\n"
        if verification.conclusion in {"restart_evidence_detected", "restart_verified"} and verification.timestamp_after_approval:
            body += (
                "\nI found runtime logs after the restart approval time.\n"
            )
            if latest_msg:
                body += (
                    f"Latest log:\n`{verification.latest_log_timestamp}` — {latest_msg}\n\n"
                    "This supports restart verification because the service emitted startup logs after approval.\n"
                )
        if _logs_older_than_approval(verification):
            body += (
                "\nLatest logs are older than the restart approval time, so they cannot confirm this restart.\n"
            )
        body += (
            "\nConclusion:\n"
            f"**{conclusion_label}**"
        )
        if _logs_older_than_approval(verification):
            body += (
                " — the latest logs I found are older than the restart approval time, "
                "so they do not prove the restart happened."
            )

    result = FollowupResult(
        intent=intent.intent,
        provider=provider,
        thread_path=path,
        execution_job_id=job_id,
        conclusion=verification.conclusion,
        body=body,
        evidence=verification.to_dict(),
    )
    _persist_followup_memory(thread, result, session_id=session_id, verification=verification)
    return result


def _compose_logs_reply(
    intent: FollowupIntent,
    thread: Any,
    job: Any | None,
    adapter: Any,
    *,
    path: str,
    job_id: str,
    session_id: str,
) -> FollowupResult:
    provider = str(getattr(thread, "provider", "") or adapter.provider)
    verification = adapter.verify_operation(thread, job)
    logs = adapter.get_latest_logs(thread, job, limit=intent.log_limit, level_filter=intent.log_filter)
    conclusion_label = _human_conclusion(verification.conclusion)
    stale = _logs_older_than_approval(verification)

    body = (
        f"I checked the active **{provider.title()}** **{str(getattr(thread, 'operation', 'restart') or 'restart').replace('_', ' ')}** for **{path}**.\n\n"
    )

    if not logs:
        if verification.logs_unavailable or not verification.timestamps_available:
            body += (
                "Latest logs:\n"
                "No usable provider logs are available yet.\n\n"
            )
            if not verification.timestamps_available and not verification.logs_unavailable:
                body += (
                    "Railway returned recent logs, but no timestamp was available in the log payload. "
                    "I cannot use these logs as restart proof yet.\n\n"
                )
        else:
            body += "Latest logs:\n(no log lines returned)\n\n"
    else:
        body += f"Latest {len(logs)} logs:\n"
        for idx, entry in enumerate(logs, start=1):
            ts = entry.timestamp or "no timestamp"
            body += f"{idx}. [{ts}] {entry.level} {entry.message}\n"
        body += "\n"

    body += _stale_log_disclaimer(verification)

    if not stale:
        body += f"Conclusion: **{conclusion_label}**\n\n"

    body += (
        "Evidence:\n"
        f"- Approval time: `{verification.approval_time or 'unknown'}`\n"
        f"- Latest log after approval: **{'yes' if verification.timestamp_after_approval else 'no'}**\n"
        f"- Provider command: **{verification.provider_command}**\n"
        f"- Execution job: `{job_id}`"
    )

    result = FollowupResult(
        intent=intent.intent,
        provider=provider,
        thread_path=path,
        execution_job_id=job_id,
        conclusion=verification.conclusion,
        body=body,
        logs=[entry.to_dict() for entry in logs],
        evidence=verification.to_dict(),
    )
    _persist_followup_memory(thread, result, session_id=session_id, verification=verification)
    return result


def _compose_timestamp_reply(
    intent: FollowupIntent,
    thread: Any,
    job: Any | None,
    adapter: Any,
    *,
    path: str,
    job_id: str,
    session_id: str,
) -> FollowupResult:
    provider = str(getattr(thread, "provider", "") or adapter.provider)
    verification = adapter.verify_operation(thread, job)
    logs = adapter.get_latest_logs(thread, job, limit=1)

    if verification.logs_unavailable:
        body = (
            f"I checked **{provider.title()}** logs for **{path}**, but no post-restart log evidence is stored yet.\n\n"
            f"Execution job: `{job_id}`."
        )
    elif not verification.timestamps_available:
        body = (
            "Railway returned recent logs, but no timestamp was available in the log payload. "
            "I cannot use these logs as restart proof yet.\n\n"
            f"Execution job: `{job_id}`."
        )
    else:
        latest = verification.evidence.get("latest_entry", {}) if isinstance(verification.evidence, dict) else {}
        latest_msg = str(latest.get("message") or "")
        if not latest_msg:
            logs = adapter.get_latest_logs(thread, job, limit=1)
            latest_msg = logs[0].message if logs else "(no message)"
        body = (
            "The latest log timestamp I found after the restart request is:\n\n"
            f"- **{verification.latest_log_timestamp}**\n\n"
            "Recent log:\n"
            f'"{latest_msg}"\n\n'
        )
        if verification.approval_time:
            body += (
                f"Approval time: `{verification.approval_time}`\n\n"
                "This suggests runtime activity after the restart request, but I will only mark the restart verified "
                "if the timestamp is after the approval time."
            )
            if verification.timestamp_after_approval:
                body += "\n\nCurrent assessment: timestamp is after approval."
            else:
                body += "\n\nCurrent assessment: timestamp is not after approval yet."

    result = FollowupResult(
        intent=intent.intent,
        provider=provider,
        thread_path=path,
        execution_job_id=job_id,
        conclusion=verification.conclusion,
        body=body,
        evidence=verification.to_dict(),
    )
    _persist_followup_memory(thread, result, session_id=session_id, verification=verification)
    return result


def _handle_retry(intent: FollowupIntent, thread: Any, *, session_id: str) -> FollowupResult | None:
    from aethos_core.task_frame.retry_active_operation import compose_retry_active_operation_reply

    reply = compose_retry_active_operation_reply(intent.user_text, session_id=session_id)
    if not reply:
        return None
    body, reply_intent, meta = reply
    return FollowupResult(
        intent="retry_operation",
        provider=str(getattr(thread, "provider", "") or "unknown"),
        thread_path=thread.service_path(),
        execution_job_id=str(getattr(thread, "execution_job_id", "") or ""),
        body=body,
        meta={**meta, "intent": reply_intent},
    )


def _handle_binding(intent: FollowupIntent, thread: Any, *, session_id: str) -> FollowupResult | None:
    from aethos_core.provider_topology.source_binding_chat import compose_source_binding_correction_reply

    reply = compose_source_binding_correction_reply(intent.user_text, session_id=session_id)
    if not reply:
        return None
    body, reply_intent, meta = reply
    return FollowupResult(
        intent="reconcile_source_binding",
        provider=str(getattr(thread, "provider", "") or "unknown"),
        thread_path=thread.service_path(),
        execution_job_id=str(getattr(thread, "execution_job_id", "") or ""),
        body=body,
        meta={**meta, "intent": reply_intent},
    )


def _resolve_execution_job(thread: Any, *, session_id: str):
    from aethos_core.runtime.jobs import job_store

    if getattr(thread, "execution_job_id", None):
        job = job_store.get(thread.execution_job_id)
        if job is not None:
            return job
    for row in reversed(job_store.list_all()):
        if row.job_type != "mutation_execution":
            continue
        if str(getattr(row, "session_id", "") or "") != session_id:
            continue
        return row
    return None


def _persist_followup_memory(
    thread: Any,
    result: FollowupResult,
    *,
    session_id: str,
    verification: Any | None = None,
) -> None:
    from aethos_core.operational_thread_memory.thread_persistence import save_thread_state

    thread.last_evidence = dict(result.evidence)
    thread.last_logs = list(result.logs)
    if verification is not None and getattr(verification, "verified", False):
        thread.last_verified_at = datetime.now(UTC).isoformat()
    thread.updated_at = datetime.now(UTC).isoformat()
    save_thread_state(thread)
    if getattr(thread, "execution_job_id", None):
        from aethos_core.runtime.jobs import job_store

        job = job_store.get(thread.execution_job_id)
        if job is not None:
            from aethos_core.operational_skill_runtime.provider_memory_bridge import persist_operation_memory

            log_entries = list(result.logs or [])
            if not log_entries and isinstance(result.evidence, dict):
                log_entries = list(result.evidence.get("entries") or result.evidence.get("logs_excerpt") or [])
            if verification is not None:
                nested = getattr(verification, "evidence", None)
                if isinstance(nested, dict):
                    log_entries = list(nested.get("entries") or nested.get("logs_excerpt") or log_entries)
            from aethos_core.operational_skill_runtime.evidence_collector import build_universal_evidence_from_job

            universal = build_universal_evidence_from_job(job, log_entries=log_entries or None)
            if verification is not None:
                if getattr(verification, "latest_log_timestamp", None):
                    universal.latest_log_timestamp = verification.latest_log_timestamp
                if getattr(verification, "startup_after_approval", False):
                    universal.startup_log_observed_after_approval = True
                if getattr(verification, "conclusion", None):
                    universal.verification_status = str(verification.conclusion)
                if getattr(verification, "provider_command", None) == "submitted":
                    universal.command_submitted = True
            persist_operation_memory(session_id=session_id, job=job, universal=universal)


def _human_conclusion(code: str) -> str:
    mapping = {
        "restart_verified": "Restart verified",
        "restart_evidence_detected": "Restart evidence detected — verification still stabilizing",
        "restart_unverified": "Restart unverified",
        "restart_unconfirmed": "Restart verification unconfirmed",
        "still_stabilizing": "Still stabilizing",
        "execution_failed": "Execution failed",
        "logs_without_timestamps": "Logs present but not usable as restart proof yet",
        "logs_unavailable": "Logs unavailable",
        "inconclusive": "Inconclusive",
        "capability_gap": "Provider follow-up not available yet",
    }
    return mapping.get(code, code.replace("_", " ").title())
