# SPDX-License-Identifier: Apache-2.0
"""Tracked work jobs — create → run → report."""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.runtime.job_types import (
    EXTERNAL_JOB_TYPES,
    JOB_TYPES,
    OPERATION_PREFLIGHT_JOB_TYPES,
    PROVIDER_JOB_TYPES,
    READONLY_EXECUTION_JOB_TYPES,
    VERCEL_READONLY_JOB_TYPES,
    uses_external,
    uses_mutation_execution,
    uses_mutation_preflight,
    uses_operation_preflight,
    uses_provider,
    uses_readonly_execution,
    uses_vercel_readonly,
)

__all__ = [
    "JOB_TYPES",
    "PROVIDER_JOB_TYPES",
    "EXTERNAL_JOB_TYPES",
    "JobStatus",
    "TrackedJob",
    "JobStore",
    "job_store",
    "infer_job_from_text",
    "infer_provider_job_from_text",
    "uses_provider",
    "uses_external",
    "VERCEL_READONLY_JOB_TYPES",
    "uses_vercel_readonly",
    "OPERATION_PREFLIGHT_JOB_TYPES",
    "uses_operation_preflight",
    "READONLY_EXECUTION_JOB_TYPES",
    "uses_readonly_execution",
]


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _new_job_id() -> str:
    return f"job-{uuid4().hex[:12]}"


def _event_id(job_id: str, event_type: str, suffix: str = "") -> str:
    if suffix:
        return f"{job_id}:{event_type}:{suffix}"
    return f"{job_id}:{event_type}"


def _first_line(text: str | None, max_len: int = 120) -> str:
    if not text:
        return ""
    line = (text.strip().splitlines() or [""])[0]
    return line[:max_len]


def _preview_and_summary(text: str) -> tuple[str, str]:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    preview = _first_line(text, 200)
    summary = lines[0] if lines else preview
    if len(lines) > 1:
        summary = f"{summary} (+{len(lines) - 1} more lines)"
    return preview, summary[:240]


@dataclass
class JobEvent:
    id: str
    job_id: str
    event_type: str
    message: str
    status: str
    job_type: str
    session_id: str
    at: float = field(default_factory=time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "event_type": self.event_type,
            "message": self.message,
            "status": self.status,
            "job_type": self.job_type,
            "session_id": self.session_id,
            "at": self.at,
        }


@dataclass
class TrackedJob:
    id: str
    title: str
    job_type: str
    status: JobStatus
    source: str
    session_id: str
    created_at: float = field(default_factory=time)
    updated_at: float = field(default_factory=time)
    result: str | None = None
    full_result: str | None = None
    result_preview: str | None = None
    result_summary: str | None = None
    failure_reason: str | None = None
    provider_used: str | None = None
    model_used: str | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "job_type": self.job_type,
            "status": self.status.value,
            "source": self.source,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.full_result or self.result,
            "full_result": self.full_result or self.result,
            "result_preview": self.result_preview,
            "result_summary": self.result_summary,
            "failure_reason": self.failure_reason,
            "provider_used": self.provider_used,
            "model_used": self.model_used,
            "params": self.params,
        }


def message_for_job_event(job: TrackedJob, event_type: str, *, custom_message: str | None = None) -> str:
    if custom_message:
        return custom_message
    title = job.title
    if event_type == "job_created":
        return f"⏳ Job queued — {title}. Visible in Mission Control → Jobs."
    if event_type == "job_started":
        from aethos_core.runtime.job_artifacts import started_event_message

        return started_event_message(job.job_type, title)
    if event_type == "job_progress":
        return f"🧠 Working on {title}…"
    if event_type == "job_completed" and job.job_type == "agent_coordination":
        # The consolidated multi-agent plan belongs in chat (it used to render
        # inline before the run was made durable). Surface the full report rather
        # than a one-line summary pointer.
        return job.full_result or job.result_summary or "Multi-agent coordination complete."
    if event_type == "job_completed":
        from aethos_core.runtime.job_artifacts import chat_completion_event_message

        return chat_completion_event_message(
            job.job_type,
            title,
            job.result_summary or "",
            fallback=bool(job.params.get("provider_fallback")),
            preflight_status=str(job.params.get("preflight_status") or ""),
            auth_method=str(job.params.get("auth_method") or "") or None,
            operation_type=str(job.params.get("operation_type") or ""),
            target_name=str(job.params.get("target_name") or ""),
            readonly_execution=job.params.get("readonly_execution")
            if isinstance(job.params.get("readonly_execution"), dict)
            else None,
        )
    if event_type == "job_failed":
        reason = job.failure_reason or "unknown error"
        if job.params.get("status_reason") == "execution_timed_out":
            return f"⚠️ Read-only execution timed out — {title}. Open Mission Control → Jobs for details."
        if "timed out" in reason.lower():
            return f"⚠️ Job failed — {title}: Provider request timed out."
        return f"⚠️ Job failed — {title}: {reason}"
    if event_type == "job_cancelled":
        return f"🚫 Job cancelled — {title}"
    return f"Job update — {title}"


def _execute_checklist(job: TrackedJob) -> str:
    topic = str(job.params.get("topic") or job.title)
    items = [
        "Confirm API + chat health checks",
        "Verify Mission Control Jobs panel",
        "Run one approved runtime action (e.g. Vercel CLI probe)",
        "Validate chat lifecycle feedback for actions and jobs",
        "Document operator setup (.env, provider keys)",
    ]
    lines = [f"# Checklist: {topic}", ""]
    for item in items:
        lines.append(f"- [ ] {item}")
    return "\n".join(lines)


def _execute_manual_note(job: TrackedJob) -> str:
    note = str(job.params.get("note") or job.title)
    return f"Tracked note recorded:\n\n{note}"


def _execute_runtime_action_followup(job: TrackedJob) -> str:
    action_id = job.params.get("action_id", "")
    if action_id:
        return f"Follow-up recorded for runtime action `{action_id}`."
    return "Follow-up placeholder — link a runtime action id when available."


def _execute_local_job_body(job: TrackedJob) -> str:
    if job.job_type == "checklist_generation":
        return _execute_checklist(job)
    if job.job_type == "runtime_action_followup":
        return _execute_runtime_action_followup(job)
    return _execute_manual_note(job)


class JobStore:
    """In-memory tracked jobs and lifecycle events."""

    def __init__(self) -> None:
        self._jobs: dict[str, TrackedJob] = {}
        self._events: list[JobEvent] = []
        self._lock = threading.Lock()

    def _touch(self, job: TrackedJob) -> None:
        job.updated_at = time()

    def _emit(
        self,
        job: TrackedJob,
        event_type: str,
        *,
        custom_message: str | None = None,
        event_suffix: str = "",
    ) -> JobEvent:
        event = JobEvent(
            id=_event_id(job.id, event_type, event_suffix),
            job_id=job.id,
            event_type=event_type,
            message=message_for_job_event(job, event_type, custom_message=custom_message),
            status=job.status.value,
            job_type=job.job_type,
            session_id=job.session_id,
        )
        self._events.append(event)
        if event_type in ("job_completed", "job_failed", "job_progress"):
            try:
                from aethos_core.channels.dispatch import dispatch_job_lifecycle

                dispatch_job_lifecycle(job, event_type=event_type, message=event.message)
            except Exception:
                pass
        return event

    def create(
        self,
        *,
        title: str,
        job_type: str,
        source: str = "chat",
        session_id: str = "default",
        params: dict[str, Any] | None = None,
        auto_run: bool = True,
    ) -> TrackedJob:
        if job_type not in JOB_TYPES:
            raise ValueError(f"Unknown job_type: {job_type}")
        clean_title = (title or "Untitled work").strip()[:200] or "Untitled work"
        job_params = dict(params or {})
        from aethos_core.tenancy import get_current_tenant

        job_params.setdefault("tenant_id", get_current_tenant())
        with self._lock:
            job = TrackedJob(
                id=_new_job_id(),
                title=clean_title,
                job_type=job_type,
                status=JobStatus.QUEUED,
                source=source[:32],
                session_id=(session_id or "default")[:64],
                params=job_params,
            )
            self._jobs[job.id] = job
            self._emit(job, "job_created")

        if auto_run:
            from aethos_core.runtime.job_types import (
                uses_agent_coordination,
                uses_browser_evidence,
                uses_github_readonly,
                uses_railway_readonly,
            )

            if (
                uses_provider(job_type)
                or uses_external(job_type)
                or uses_vercel_readonly(job_type)
                or uses_railway_readonly(job_type)
                or uses_github_readonly(job_type)
                or uses_operation_preflight(job_type)
                or uses_mutation_preflight(job_type)
                or uses_mutation_execution(job_type)
                or uses_readonly_execution(job_type)
                or uses_browser_evidence(job_type)
                or uses_agent_coordination(job_type)
            ):
                from aethos_core.runtime.job_executor import job_executor

                job_executor.enqueue(job.id)
            else:
                self.run_local_job(job.id)
        return job

    def begin_running(self, job_id: str) -> TrackedJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status != JobStatus.QUEUED:
                return job
            job.status = JobStatus.RUNNING
            now = time()
            if uses_readonly_execution(job.job_type):
                from aethos_core.config import get_settings

                settings = get_settings()
                job.params["started_at"] = now
                job.params["last_progress_at"] = now
                job.params["timeout_sec"] = float(settings.readonly_execution_timeout_sec)
                job.params.setdefault("execution_timeline", [])
            self._touch(job)
            self._emit(job, "job_started")
            return job

    def emit_progress(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            now = time()
            job.params["last_progress_at"] = now
            if uses_readonly_execution(job.job_type):
                timeline = job.params.get("execution_timeline")
                if not isinstance(timeline, list):
                    timeline = []
                timeline.append({"at": now, "status": "progress", "message": message})
                job.params["execution_timeline"] = timeline
            self._touch(job)
            self._emit(job, "job_progress", custom_message=message, event_suffix="main")

    def complete_with_result(
        self,
        job_id: str,
        *,
        full_result: str,
        summary: str,
        preview: str,
        provider: str,
        model: str,
        used_llm: bool,
        fallback: bool,
    ) -> TrackedJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.full_result = full_result
            job.result = full_result
            job.result_preview = preview
            job.result_summary = summary
            job.provider_used = provider
            job.model_used = model
            job.params["used_llm"] = used_llm
            job.params["provider_fallback"] = fallback
            job.status = JobStatus.COMPLETED
            self._touch(job)
            self._emit(job, "job_completed")
            return job

    def fail_job(
        self,
        job_id: str,
        reason: str,
        *,
        failure: dict[str, Any] | None = None,
    ) -> TrackedJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            job.status = JobStatus.FAILED
            job.failure_reason = reason
            if failure:
                job.params["failure"] = failure
            self._touch(job)
            self._emit(job, "job_failed")
            return job

    def run_local_job(self, job_id: str) -> TrackedJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status != JobStatus.QUEUED:
                return job
            job.status = JobStatus.RUNNING
            self._touch(job)
            self._emit(job, "job_started")
        try:
            from aethos_core.runtime.job_artifacts import build_artifact_bundle

            text = _execute_local_job_body(job)
            bundle = build_artifact_bundle(text, job_type=job.job_type, title=job.title)
            return self.complete_with_result(
                job_id,
                full_result=bundle.full_result,
                summary=bundle.summary,
                preview=bundle.preview,
                provider="local",
                model="template",
                used_llm=False,
                fallback=False,
            )
        except Exception as exc:
            return self.fail_job(job_id, str(exc))

    def get(self, job_id: str) -> TrackedJob | None:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> TrackedJob:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise KeyError(job_id)
            if job.status != JobStatus.QUEUED:
                raise ValueError(f"Job {job_id} is not queued (status={job.status.value})")
            job.status = JobStatus.CANCELLED
            self._touch(job)
            self._emit(job, "job_cancelled")
            return job

    def list_all(self) -> list[TrackedJob]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def list_grouped(self) -> dict[str, list[dict[str, Any]]]:
        self.reap_stale_running_jobs()
        grouped: dict[str, list[dict[str, Any]]] = {
            "queued": [],
            "running": [],
            "completed": [],
            "failed": [],
            "cancelled": [],
        }
        for job in self.list_all():
            grouped[job.status.value].append(job.to_dict())
        return grouped

    def reap_stale_running_jobs(self) -> list[str]:
        """Fail stale read-only execution jobs that exceeded timeout_sec without progress."""
        from aethos_core.config import get_settings
        from aethos_core.runtime.job_types import uses_readonly_execution

        default_timeout = float(get_settings().readonly_execution_timeout_sec)
        now = time()
        reaped: list[str] = []
        with self._lock:
            for job in self.list_all():
                if job.status != JobStatus.RUNNING:
                    continue
                if not uses_readonly_execution(job.job_type):
                    continue
                started = float(job.params.get("started_at") or job.updated_at or job.created_at)
                last = float(job.params.get("last_progress_at") or started)
                timeout = float(job.params.get("timeout_sec") or default_timeout)
                if now - last <= timeout and now - started <= timeout * 1.5:
                    continue
                job.status = JobStatus.FAILED
                job.failure_reason = (
                    "Read-only execution timed out before completion."
                )
                job.params["status_reason"] = "execution_timed_out"
                timeline = job.params.get("execution_timeline")
                if isinstance(timeline, list) and timeline:
                    last_msg = str(timeline[-1].get("message") or "unknown step")
                else:
                    last_msg = "unknown step"
                job.params["timeout_last_progress"] = last_msg
                self._touch(job)
                self._emit(job, "job_failed")
                reaped.append(job.id)
        return reaped

    def list_events(
        self,
        *,
        job_ids: list[str] | None = None,
        session_id: str | None = None,
        since: float = 0.0,
    ) -> list[dict[str, Any]]:
        out: list[JobEvent] = []
        id_set = set(job_ids) if job_ids else None
        for event in self._events:
            if event.at < since:
                continue
            if id_set is not None and event.job_id not in id_set:
                continue
            if id_set is None and session_id and event.session_id != session_id:
                continue
            out.append(event)
        out.sort(key=lambda e: e.at)
        return [e.to_dict() for e in out]

    def clear_for_tests(self) -> None:
        with self._lock:
            self._jobs.clear()
            self._events.clear()


def infer_provider_job_from_text(text: str) -> tuple[str, str, dict[str, Any]] | None:
    raw = (text or "").strip()
    lower = raw.lower()
    topic = raw[:200]

    if re.search(r"\bresearch\b.*\b(competitor|competition|competing)\b", lower):
        title = "Research AethOS competitors"
        return title, "comparison_brief", {"topic": topic, "user_request": raw}
    if re.search(r"\b(generate|draft|create)\b.*\b(mvp\s+)?roadmap\b", lower):
        return "MVP roadmap", "roadmap_generation", {"topic": topic, "user_request": raw}
    if re.search(r"\b(summarize|summarise|explain|describe)\b.*\barchitecture\b", lower):
        return "Architecture summary", "architecture_summary", {"topic": topic, "user_request": raw}
    if re.search(r"\b(draft|create|write)\b.*\bplanning\s+document\b", lower):
        return "Planning document", "planning_document", {"topic": topic, "user_request": raw}
    if re.search(r"\bresearch\b", lower) and not re.search(r"\btracked\b", lower):
        return topic[:200] or "Research plan", "research_plan", {"topic": topic, "user_request": raw}
    return None


def infer_job_from_text(text: str) -> tuple[str, str, dict[str, Any]]:
    """Return (title, job_type, params) from user message."""
    provider = infer_provider_job_from_text(text)
    if provider is not None:
        return provider

    raw = (text or "").strip()
    lower = raw.lower()
    topic = raw
    for prefix in (
        r"^(?:make|create)\s+(?:a\s+)?tracked\s+(?:task|job)\s+(?:to\s+)?",
        r"^(?:make|create)\s+(?:a\s+)?tracked\s+(?:task|job)\s*:\s*",
        r"^(?:make|create)\s+(?:a\s+)?checklist\s+(?:for\s+)?",
        r"^create\s+a\s+checklist\s+(?:for\s+)?",
        r"^(?:make|create)\s+(?:a\s+)?queued\s+tracked\s+(?:task|job)\s+(?:to\s+)?",
    ):
        topic = re.sub(prefix, "", topic, flags=re.I).strip() or topic
    if re.search(r"\bchecklist\b", lower):
        return topic[:200] or "Checklist", "checklist_generation", {"topic": topic}
    if re.search(r"\bruntime\s+action\b|\bact-[a-f0-9]+\b", lower):
        m = re.search(r"\b(act-[a-f0-9]+)\b", raw, re.I)
        params: dict[str, Any] = {"action_id": m.group(1)} if m else {}
        return topic[:200] or "Runtime follow-up", "runtime_action_followup", params
    return topic[:200] or "Tracked work", "manual_note", {"note": topic}


job_store = JobStore()
