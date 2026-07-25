# SPDX-License-Identifier: Apache-2.0
"""Bridge provider skill evidence into operational thread memory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.operational_skill_runtime.evidence_collector import UniversalEvidenceBundle, build_universal_evidence_from_job


def persist_operation_memory(
    *,
    session_id: str,
    job: Any,
    universal: UniversalEvidenceBundle | None = None,
    user_text: str = "",
) -> dict[str, Any]:
    """Remember active provider context and latest evidence for follow-ups."""
    from aethos_core.continuity_intelligence.operational_focus_model import set_operational_focus
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread, save_thread_state

    bundle = universal or build_universal_evidence_from_job(job)
    params = getattr(job, "params", None) or {}
    target = bundle.target

    focus = {
        "provider": bundle.provider,
        "service": target.get("service_name") or params.get("target_name") or "",
        "project": target.get("project_name") or "",
        "environment": target.get("environment") or "production",
        "operation": bundle.operation,
        "execution_job_id": str(getattr(job, "id", "") or ""),
        "approval_time": bundle.approved_at,
        "latest_log_timestamp": bundle.latest_log_timestamp,
        "verification_status": bundle.verification_status,
        "command_submitted": bundle.command_submitted,
        "command_name": bundle.command_name,
        "next_action": bundle.next_action,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    set_operational_focus(session_id=session_id, focus=focus)

    thread = get_active_thread(session_id=session_id)
    if thread is not None:
        thread.last_evidence = bundle.to_dict()
        thread.execution_job_id = str(getattr(job, "id", "") or thread.execution_job_id or "")
        thread.updated_at = datetime.now(UTC).isoformat()
        if bundle.startup_log_observed_after_approval:
            thread.last_verified_at = datetime.now(UTC).isoformat()
        save_thread_state(thread)

    return {"ok": True, "focus": focus, "thread_updated": thread is not None}


def recall_operation_memory(*, session_id: str) -> dict[str, Any]:
    from aethos_core.continuity_intelligence.operational_focus_model import get_operational_focus
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread

    focus = get_operational_focus(session_id=session_id)
    thread = get_active_thread(session_id=session_id)
    if not focus and thread is None:
        return {"ok": False, "reason": "no_operational_memory"}
    return {
        "ok": True,
        "focus": focus,
        "thread": thread.to_dict() if thread is not None and hasattr(thread, "to_dict") else None,
    }
