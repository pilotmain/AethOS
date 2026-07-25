# SPDX-License-Identifier: Apache-2.0
"""Engineering preflight store — approvable tracked work."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any

from aethos_core.agents.runtime.paths import agent_artifacts_root


def _store_path() -> Path:
    return agent_artifacts_root() / "engineering_preflights.json"


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"preflights": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"preflights": {}}


def _save(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_engineering_preflight(
    *,
    preflight: dict[str, Any],
    user_request: str,
    workspace_hint: str | None = None,
    session_id: str = "default",
    source: str = "chat",
) -> dict[str, Any]:
    """Persist preflight and create approvable tracked job."""
    preflight_id = str(preflight.get("preflight_id") or "")
    if not preflight_id:
        raise ValueError("preflight_id required")

    task = preflight.get("task") or {}
    patch_plan = preflight.get("patch_plan") or {}
    job = _create_preflight_job(
        preflight=preflight,
        user_request=user_request,
        workspace_hint=workspace_hint,
        session_id=session_id,
        source=source,
    )

    record = {
        **preflight,
        "job_id": job["id"],
        "approval_required": True,
        "approved": False,
        "denied": False,
        "target_workspace": workspace_hint or task.get("title") or "AethOS",
        "user_request": user_request[:500],
        "created_at": time(),
        "updated_at": time(),
    }
    data = _load()
    preflights = dict(data.get("preflights") or {})
    preflights[preflight_id] = record
    data["preflights"] = preflights
    data["updated_at"] = time()
    _save(data)
    return record


def list_pending_preflights(*, limit: int = 20) -> list[dict[str, Any]]:
    data = _load()
    rows = [
        row
        for row in (data.get("preflights") or {}).values()
        if row.get("approval_required") and not row.get("approved") and not row.get("denied")
    ]
    rows.sort(key=lambda r: float(r.get("created_at") or 0), reverse=True)
    return rows[:limit]


def list_all_preflights(*, limit: int = 30) -> list[dict[str, Any]]:
    data = _load()
    rows = list((data.get("preflights") or {}).values())
    rows.sort(key=lambda r: float(r.get("created_at") or 0), reverse=True)
    return rows[:limit]


def get_preflight(preflight_id: str) -> dict[str, Any] | None:
    return (_load().get("preflights") or {}).get(preflight_id)


def approve_preflight(preflight_id: str) -> dict[str, Any]:
    row = get_preflight(preflight_id)
    if not row:
        return {"ok": False, "error": "not_found"}
    if row.get("denied"):
        return {"ok": False, "error": "already_denied"}
    if row.get("approved"):
        return {"ok": False, "error": "already_approved", "execution": row.get("execution")}

    from aethos_core.engineering.governance.engineering_scope import EngineeringRiskTier, execution_allowed
    from aethos_core.local_workspace.readonly.actions import _repo_from_hint

    tier = EngineeringRiskTier(row.get("risk_tier") or EngineeringRiskTier.E1_PROPOSAL.value)
    if not execution_allowed(tier):
        from aethos_core.engineering.pr_drafts import build_governed_pr_draft, store_pr_draft

        pr_draft = build_governed_pr_draft(
            preflight=row,
            execution={"validation": {"validation_status": "validation_pending", "ok": True}},
            diff_intel=(row.get("patch_proposal") or {}).get("diff_intelligence"),
        )
        pr_draft = store_pr_draft(preflight_id=preflight_id, draft=pr_draft)
        execution = {
            "ok": True,
            "status": "proposal_only",
            "execution_id": None,
            "pr_draft": pr_draft,
            "validation": {"validation_status": "validation_pending", "ok": True},
            "proposal_only": True,
        }
    else:
        from aethos_core.engineering.governance.engineering_execution import run_engineering_execution

        repo = _repo_from_hint(row.get("target_workspace") or "aethos", session_id="default")
        execution = run_engineering_execution(preflight=row, repo=repo, approved=True)

    exec_job = _create_execution_job(preflight=row, execution=execution)

    row["approved"] = True
    row["approval_status"] = "approved"
    row["approved_at"] = time()
    row["execution"] = execution
    row["execution_job_id"] = exec_job.get("id")
    row["updated_at"] = time()
    _update_row(preflight_id, row)
    _mark_job_approved(str(row.get("job_id") or ""))
    return {"ok": True, "preflight": row, "execution": execution, "execution_job_id": exec_job.get("id")}


def deny_preflight(preflight_id: str, *, reason: str = "") -> dict[str, Any]:
    row = get_preflight(preflight_id)
    if not row:
        return {"ok": False, "error": "not_found"}
    row["denied"] = True
    row["approval_status"] = "denied"
    row["denial_reason"] = reason[:240]
    row["updated_at"] = time()
    _update_row(preflight_id, row)
    _mark_job_denied(str(row.get("job_id") or ""), reason=reason)
    return {"ok": True, "preflight": row}


def _update_row(preflight_id: str, row: dict[str, Any]) -> None:
    data = _load()
    preflights = dict(data.get("preflights") or {})
    preflights[preflight_id] = row
    data["preflights"] = preflights
    data["updated_at"] = time()
    _save(data)


def _create_preflight_job(
    *,
    preflight: dict[str, Any],
    user_request: str,
    workspace_hint: str | None,
    session_id: str,
    source: str,
) -> dict[str, Any]:
    from aethos_core.runtime.jobs import JobStatus, job_store

    task = preflight.get("task") or {}
    title = str(task.get("title") or "Engineering preflight")
    job = job_store.create(
        title=title[:200],
        job_type="engineering_preflight",
        source=source,
        session_id=session_id,
        auto_run=False,
        params={
            "preflight_id": preflight.get("preflight_id"),
            "approval_required": True,
            "approved": False,
            "risk_tier": preflight.get("risk_tier"),
            "target_workspace": workspace_hint or "AethOS",
            "patch_plan": preflight.get("patch_plan"),
            "patch_proposal": preflight.get("patch_proposal"),
            "user_request": user_request[:500],
        },
    )
    job.status = JobStatus.COMPLETED
    job.full_result = preflight.get("report") or ""
    job.result = job.full_result
    job.result_preview = (job.full_result or "")[:200]
    job.result_summary = f"Engineering preflight — approval required ({preflight.get('risk_tier')})"
    job.params["preflight_status"] = "pending_approval"
    job.updated_at = time()
    return job.to_dict()


def _create_execution_job(*, preflight: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.runtime.jobs import JobStatus, job_store

    title = str((preflight.get("task") or {}).get("title") or "Engineering execution")
    job = job_store.create(
        title=f"Execute: {title}"[:200],
        job_type="engineering_execution",
        source="engineering_approval",
        session_id="default",
        auto_run=False,
        params={
            "preflight_id": preflight.get("preflight_id"),
            "execution_id": execution.get("execution_id"),
            "approved": True,
            "validation": execution.get("validation"),
            "pr_draft": execution.get("pr_draft"),
        },
    )
    job.status = JobStatus.COMPLETED if execution.get("ok") else JobStatus.FAILED
    job.full_result = json.dumps(execution, indent=2)[:8000]
    job.result = job.full_result
    job.result_summary = execution.get("status") or "engineering_execution"
    if not execution.get("ok"):
        job.failure_reason = str(execution.get("error") or execution.get("status") or "execution_failed")
    job.updated_at = time()
    val_job = None
    if execution.get("validation"):
        val_job = job_store.create(
            title=f"Validate: {title}"[:200],
            job_type="engineering_validation",
            source="engineering_approval",
            session_id="default",
            auto_run=False,
            params={"preflight_id": preflight.get("preflight_id"), "validation": execution.get("validation")},
        )
        val_job.status = JobStatus.COMPLETED if execution.get("validation", {}).get("ok") else JobStatus.FAILED
        val_job.result_summary = execution.get("validation", {}).get("validation_status") or "validation"
        val_job.updated_at = time()
    if execution.get("pr_draft"):
        draft = execution["pr_draft"]
        pr_job = job_store.create(
            title=str(draft.get("title") or "PR draft")[:200],
            job_type="engineering_pr_draft",
            source="engineering_approval",
            session_id="default",
            auto_run=False,
            params={"preflight_id": preflight.get("preflight_id"), "pr_draft": draft},
        )
        pr_job.status = JobStatus.COMPLETED
        pr_job.result_summary = "PR draft generated — merge requires separate approval"
        pr_job.full_result = str(draft.get("body") or "")[:8000]
        pr_job.updated_at = time()
    return job.to_dict()


def _mark_job_approved(job_id: str) -> None:
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return
    job.params["approved"] = True
    job.params["preflight_status"] = "approved"
    job.result_summary = "Engineering preflight approved — execution enqueued"
    job.updated_at = time()


def _mark_job_denied(job_id: str, *, reason: str = "") -> None:
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    if not job:
        return
    job.params["approved"] = False
    job.params["denied"] = True
    job.params["preflight_status"] = "denied"
    job.params["denial_reason"] = reason[:240]
    job.result_summary = "Engineering preflight denied"
    job.updated_at = time()


def clear_engineering_preflights_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
