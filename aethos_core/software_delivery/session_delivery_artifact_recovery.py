# SPDX-License-Identifier: Apache-2.0
"""Recover software delivery session state from surviving artifact files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_REPO_RX = re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")
_ISSUE_URL_RX = re.compile(r"github\.com/([^/]+/[^/]+)/issues/(\d+)", re.I)


def _data_root() -> Path:
    return Path(__file__).resolve().parents[2] / "data"


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _glob_records(subdir: str, *, session_id: str) -> list[dict[str, Any]]:
    root = _data_root() / subdir
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in root.glob("*.json"):
        payload = _read_json(path)
        if payload and str(payload.get("session_id") or "") == session_id:
            rows.append(payload)
    return rows


def _plan_id_from_receipt_filename(path: Path) -> str:
    name = path.name
    for suffix in (
        "_branch_push_receipts.json",
        "_github_pr_preflight_receipts.json",
        "_patch_receipts.json",
        "_verify_receipts.json",
        "_workspace_apply_receipts.json",
        "_pr_draft_receipts.json",
        "_branch_receipts.json",
    ):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return ""


def _discover_plan_ids_from_receipt_files() -> list[str]:
    plan_ids: set[str] = set()
    for subdir in (
        "software_delivery_branch_push_receipts",
        "software_delivery_github_pr_preflight_receipts",
        "software_delivery_patch_receipts",
        "software_delivery_workspace_verification_receipts",
        "software_delivery_workspace_apply_receipts",
        "software_delivery_pr_draft_receipts",
        "software_delivery_branch_receipts",
    ):
        root = _data_root() / subdir
        if not root.is_dir():
            continue
        for path in root.glob("*.json"):
            plan_id = _plan_id_from_receipt_filename(path)
            if plan_id.startswith("sdplan-"):
                plan_ids.add(plan_id)
    return sorted(plan_ids)


def _latest_receipt_timestamp(*, plan_id: str) -> str:
    latest = ""
    safe = plan_id.replace("/", "_")
    receipt_paths = (
        _data_root() / "software_delivery_branch_push_receipts" / f"{safe}_branch_push_receipts.json",
        _data_root()
        / "software_delivery_github_pr_preflight_receipts"
        / f"{safe}_github_pr_preflight_receipts.json",
    )
    for path in receipt_paths:
        if not path.is_file():
            continue
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict):
                ts = str(row.get("recorded_at") or "")
                if ts > latest:
                    latest = ts
    return latest


def _preflight_approved_from_receipts(*, plan_id: str) -> bool:
    from aethos_core.software_delivery.github_pr_preflight_receipts import list_github_pr_preflight_receipts

    for receipt in list_github_pr_preflight_receipts(plan_id=plan_id):
        if str(receipt.get("phase") or "") == "preflight_approved":
            return True
    return False


def _branch_push_completed_from_receipts(*, plan_id: str) -> bool:
    from aethos_core.software_delivery.branch_push_receipts import list_branch_push_receipts

    for receipt in list_branch_push_receipts(plan_id=plan_id):
        if str(receipt.get("status") or "") != "branch_push_success":
            continue
        if str(receipt.get("phase") or "") in {"push_completed", "feature_branch_pushed"}:
            return True
    return False


def _feature_branch_from_receipts(*, plan_id: str) -> str:
    from aethos_core.software_delivery.branch_push_receipts import list_branch_push_receipts

    for receipt in list_branch_push_receipts(plan_id=plan_id):
        phase = str(receipt.get("phase") or "")
        detail = str(receipt.get("detail") or "")
        if phase in {"feature_branch_created", "feature_branch_pushed"} and detail.startswith("aethos/"):
            return detail
    return ""


def discover_plan_ids_for_session(*, session_id: str) -> dict[str, list[str]]:
    sid = (session_id or "default").strip()[:64] or "default"
    sources: dict[str, list[str]] = {}
    from aethos_core.software_delivery.session_plan_index import load_session_plan_id

    indexed = load_session_plan_id(session_id=sid)
    if indexed:
        sources["software_delivery_session_plan_index"] = [indexed]
    for subdir in (
        "software_delivery_branch_contexts",
        "software_delivery_pr_drafts",
        "software_delivery_patch_proposals",
        "software_delivery_github_pr_preflights",
        "software_delivery_workspace_verifications",
        "software_delivery_workspace_applications",
    ):
        plan_ids = sorted(
            {
                str(row.get("plan_id") or "")
                for row in _glob_records(subdir, session_id=sid)
                if str(row.get("plan_id") or "")
            }
        )
        if plan_ids:
            sources[subdir] = plan_ids
    return sources


def _receipt_delivery_progress_score(*, plan_id: str) -> int:
    if _branch_push_completed_from_receipts(plan_id=plan_id):
        return 900
    if _preflight_approved_from_receipts(plan_id=plan_id):
        return 800
    return 100


def _infer_session_plan_id_from_receipts(*, session_id: str) -> str | None:
    from aethos_core.software_delivery.session_plan_index import persist_session_plan_binding

    sid = (session_id or "default").strip()[:64] or "default"
    candidates: list[tuple[int, str, str]] = []
    for plan_id in _discover_plan_ids_from_receipt_files():
        score = _receipt_delivery_progress_score(plan_id=plan_id)
        if score < 800:
            continue
        branch = _feature_branch_from_receipts(plan_id=plan_id)
        if sid == "operator" and branch and "issue-1-" not in branch:
            continue
        candidates.append((score, _latest_receipt_timestamp(plan_id=plan_id), plan_id))
    if not candidates:
        return None
    _score, _ts, best = max(candidates, key=lambda row: (row[0], row[1], row[2]))
    persist_session_plan_binding(session_id=sid, plan_id=best)
    return best


def _delivery_progress_score(*, plan_id: str) -> int:
    from aethos_core.software_delivery.branch_push_store import branch_push_completed_for_plan
    from aethos_core.software_delivery.github_pr_open_store import _pr_open_completed_local
    from aethos_core.software_delivery.github_pr_preflight_store import github_pr_creation_approved_for_plan
    from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan
    from aethos_core.software_delivery.workspace_verification_store import workspace_verification_passed

    if _pr_open_completed_local(plan_id=plan_id):
        return 1000
    if branch_push_completed_for_plan(plan_id=plan_id) or _branch_push_completed_from_receipts(plan_id=plan_id):
        return 900
    if github_pr_creation_approved_for_plan(plan_id=plan_id) or _preflight_approved_from_receipts(plan_id=plan_id):
        return 800
    if load_pr_draft_for_plan(plan_id=plan_id):
        return 700
    if workspace_verification_passed(plan_id=plan_id):
        return 600
    return 100


def _pick_best_plan_id(*, session_id: str) -> str | None:
    from aethos_core.software_delivery.session_plan_index import load_session_plan_id

    indexed = load_session_plan_id(session_id=session_id)
    if indexed:
        return indexed

    sources = discover_plan_ids_for_session(session_id=session_id)
    plan_ids = sorted({pid for ids in sources.values() for pid in ids})
    if not plan_ids:
        return _infer_session_plan_id_from_receipts(session_id=session_id)
    if len(plan_ids) == 1:
        return plan_ids[0]
    return max(plan_ids, key=lambda pid: (_delivery_progress_score(plan_id=pid), pid))


def _repository_for_plan(*, plan_id: str, session_id: str) -> tuple[str, int | None]:
    for subdir in (
        "software_delivery_patch_proposals",
        "software_delivery_pr_drafts",
        "software_delivery_github_pr_preflights",
    ):
        for row in _glob_records(subdir, session_id=session_id):
            if str(row.get("plan_id") or "") != plan_id:
                continue
            repo = str(row.get("repository") or "")
            if repo:
                return repo, int(row.get("issue_number") or 0) or None
            body = str(row.get("body") or "")
            match = _ISSUE_URL_RX.search(body)
            if match:
                return match.group(1), int(match.group(2))
            match = _REPO_RX.search(body)
            if match:
                return match.group(1), None
    return "pilotmain/AethOS", 1


def _issue_body_for_plan(*, plan_id: str, session_id: str) -> str:
    for row in _glob_records("software_delivery_pr_drafts", session_id=session_id):
        if str(row.get("plan_id") or "") == plan_id:
            body = str(row.get("body") or "")
            if body:
                return body
    for row in _glob_records("software_delivery_patch_proposals", session_id=session_id):
        if str(row.get("plan_id") or "") == plan_id:
            intent = row.get("patch_intent") or {}
            summary = str(intent.get("summary") or "")
            files = row.get("proposed_files") or []
            return (
                f"### Scope (Bounded)\n\n"
                f"{summary}\n\n"
                f"Files:\n"
                + "\n".join(f"- `{f}`" for f in files)
            )
    return ""


def restore_branch_context_for_plan(*, plan_id: str, session_id: str) -> dict[str, Any] | None:
    from aethos_core.software_delivery.branch_orchestration_store import (
        load_branch_context_for_plan,
        save_branch_context,
    )
    from aethos_core.software_delivery.github_pr_open_store import _resolve_feature_branch_for_plan

    existing = load_branch_context_for_plan(plan_id=plan_id)
    resolved_branch = _resolve_feature_branch_for_plan(plan_id=plan_id)
    if existing:
        if resolved_branch and str(existing.get("branch_name") or "") != resolved_branch:
            existing = save_branch_context({**existing, "branch_name": resolved_branch})
        return existing

    proposal = None
    draft = None
    for row in _glob_records("software_delivery_patch_proposals", session_id=session_id):
        if str(row.get("plan_id") or "") == plan_id:
            proposal = row
            break
    for row in _glob_records("software_delivery_pr_drafts", session_id=session_id):
        if str(row.get("plan_id") or "") == plan_id:
            draft = row
            break

    branch_context_id = str((proposal or {}).get("branch_context_id") or (draft or {}).get("branch_context_id") or "")
    if not branch_context_id:
        branch_context_id = f"sdbctx-{plan_id.rsplit('-', 1)[-1][:12]}"

    repository, issue_number = _repository_for_plan(plan_id=plan_id, session_id=session_id)
    branch_name = resolved_branch
    if not branch_name and draft:
        branch_name = str(draft.get("branch_name") or "")
    if not branch_name:
        branch_name = f"aethos/sd-aethos-issue-{issue_number or 1}-{plan_id.rsplit('-', 1)[-1][:8]}"

    ctx = save_branch_context(
        {
            "branch_context_id": branch_context_id,
            "plan_id": plan_id,
            "session_id": session_id,
            "repository": repository,
            "issue_number": issue_number or 1,
            "branch_name": branch_name,
            "workspace_path": str(_data_root() / "software_delivery_workspaces" / plan_id.replace("/", "_")),
            "lifecycle_state": "active",
            "lock_holder": session_id,
            "events": [],
            "reconstructed_from_artifacts": True,
        }
    )
    return ctx


def restore_pilot_run_audit_for_session(*, session_id: str, plan_id: str) -> dict[str, Any] | None:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
        list_pilot_run_audits,
        persist_pilot_run_audit,
    )
    from aethos_core.software_delivery.branch_push_store import branch_push_completed_for_plan
    from aethos_core.software_delivery.github_pr_open_store import _pr_open_completed_local
    from aethos_core.software_delivery.github_pr_preflight_store import github_pr_creation_approved_for_plan
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan
    from aethos_core.software_delivery.pr_draft_store import load_pr_draft_for_plan
    from aethos_core.software_delivery.workspace_verification_store import workspace_verification_passed

    sid = (session_id or "default").strip()[:64] or "default"
    if list_pilot_run_audits(session_id=sid):
        return None

    plan = load_issue_plan(plan_id=plan_id) or {}
    if str(plan.get("session_id") or "") != sid:
        return None

    stages: list[str] = ["issue_intake", "implementation_plan"]
    if restore_branch_context_for_plan(plan_id=plan_id, session_id=sid):
        stages.append("implementation_branch")
    if _glob_records("software_delivery_patch_proposals", session_id=sid):
        stages.append("patch_proposal")
    elif _branch_push_completed_from_receipts(plan_id=plan_id):
        stages.extend(["implementation_branch", "patch_proposal", "workspace_apply", "workspace_verify", "pr_draft"])
    if _glob_records("software_delivery_workspace_applications", session_id=sid):
        stages.append("workspace_apply")
    if workspace_verification_passed(plan_id=plan_id):
        stages.append("workspace_verify")
    if load_pr_draft_for_plan(plan_id=plan_id) or _glob_records("software_delivery_pr_drafts", session_id=sid):
        stages.append("pr_draft")
    if github_pr_creation_approved_for_plan(plan_id=plan_id) or _preflight_approved_from_receipts(plan_id=plan_id):
        stages.append("github_pr_preflight")
    if branch_push_completed_for_plan(plan_id=plan_id) or _branch_push_completed_from_receipts(plan_id=plan_id):
        stages.append("branch_push")
    if _pr_open_completed_local(plan_id=plan_id):
        stages.append("pr_open")

    if len(stages) <= 2:
        return None

    repository = str(plan.get("repository") or "pilotmain/AethOS")
    issue_number = int(plan.get("issue_number") or 1)
    outcome = "complete" if "pr_open" in stages else "partial"
    return persist_pilot_run_audit(
        {
            "session_id": sid,
            "plan_id": plan_id,
            "repo_issue": f"{repository}#{issue_number}",
            "outcome": outcome,
            "stages_completed": stages,
            "blockers": [] if outcome == "complete" else ["recovered_from_delivery_artifacts"],
            "recovered_from_delivery_artifacts": True,
        }
    )


def restore_issue_plan_for_session(*, session_id: str) -> dict[str, Any] | None:
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan, save_issue_plan

    sid = (session_id or "default").strip()[:64] or "default"
    plan_id = _pick_best_plan_id(session_id=sid)
    if not plan_id:
        return None

    existing = load_issue_plan(plan_id=plan_id)
    if existing and str(existing.get("session_id") or "") == sid:
        restore_branch_context_for_plan(plan_id=plan_id, session_id=sid)
        return existing

    repository, issue_number = _repository_for_plan(plan_id=plan_id, session_id=sid)
    issue_body = _issue_body_for_plan(plan_id=plan_id, session_id=sid)
    proposal_rows = [
        row
        for row in _glob_records("software_delivery_patch_proposals", session_id=sid)
        if str(row.get("plan_id") or "") == plan_id
    ]
    proposed_files = list((proposal_rows[0].get("proposed_files") or []) if proposal_rows else [])
    intent = (proposal_rows[0].get("patch_intent") or {}) if proposal_rows else {}

    plan = save_issue_plan(
        {
            "plan_id": plan_id,
            "session_id": sid,
            "repository": repository,
            "issue_number": issue_number or 1,
            "issue_url": f"https://github.com/{repository}/issues/{issue_number or 1}",
            "issue_title": str(intent.get("summary") or "AethOS Dogfood Pilot"),
            "issue_body": issue_body,
            "status": "planning_approved",
            "planning_approved": True,
            "governed_plan": {
                "goal": str(intent.get("summary") or "AethOS Dogfood Pilot"),
                "problem_summary": str(intent.get("summary") or "")[:240],
                "bounded_steps": list(intent.get("validation_steps") or []),
                "out_of_scope": ["workflow files", "provider files", "Railway", "Deploy", "Merge"],
            },
            "issue_intake_scope_fidelity": {
                "expected_files": proposed_files,
                "explicit_bounded_scope": bool(proposed_files),
                "source": "artifact_recovery",
            },
            "reconstructed_from_artifacts": True,
            "artifact_sources": list(discover_plan_ids_for_session(session_id=sid).keys()),
        }
    )
    restore_branch_context_for_plan(plan_id=plan_id, session_id=sid)
    from aethos_core.software_delivery.github_pr_open_store import github_pr_open_completed_for_plan

    github_pr_open_completed_for_plan(plan_id=plan_id, verify_github=True)
    return plan
