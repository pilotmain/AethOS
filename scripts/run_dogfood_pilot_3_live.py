#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Live dogfood-pilot-3 — full loop through PR Open with doc patch content."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SESSION = "dogfood-pilot-3"
REPO_ISSUE = "pilotmain/AethOS#1"
DOC_TARGET = "docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"
RECEIPT_DIR = ROOT / "data" / "dogfood_pilot_3_receipts"


def _clear_pilot_stores() -> None:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
        clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    )
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
        clear_issue_intent_alignment_records_for_tests,
    )
    from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch
    from aethos_core.software_delivery.branch_push_store import clear_for_tests as clear_push
    from aethos_core.software_delivery.github_pr_open_store import clear_for_tests as clear_pr_open
    from aethos_core.software_delivery.github_pr_preflight_store import clear_for_tests as clear_preflight
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as clear_plans
    from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as clear_patch
    from aethos_core.software_delivery.pr_draft_store import clear_for_tests as clear_pr_draft
    from aethos_core.software_delivery.workspace_application_store import clear_for_tests as clear_apply
    from aethos_core.software_delivery.workspace_verification_store import clear_for_tests as clear_verify

    clear_plans()
    clear_branch()
    clear_patch()
    clear_apply()
    clear_verify()
    clear_pr_draft()
    clear_preflight()
    clear_push()
    clear_pr_open()
    clear_issue_intent_alignment_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()


def _patch_content_checks(timeline: dict[str, Any], *, plan_id: str) -> dict[str, Any]:
    from aethos_core.software_delivery.branch_push_store import branch_push_completed_for_plan
    from aethos_core.software_delivery.github_pr_open_store import github_pr_open_completed_for_plan
    from aethos_core.software_delivery.github_pr_preflight_store import github_pr_creation_approved_for_plan

    proposal = timeline.get("patch_proposal") or {}
    diffs = list(proposal.get("unified_diffs") or [])
    doc_diff = next((d for d in diffs if d.get("file") == DOC_TARGET), {})
    diff_text = str(doc_diff.get("diff") or "")
    staged = list(proposal.get("staged_patches") or [])
    doc_patch = next((p for p in staged if p.get("file") == DOC_TARGET), {})
    new_content = str(doc_patch.get("new_content") or "")

    verification = timeline.get("workspace_verification") or {}
    classification = verification.get("classification") or {}

    pr_draft = timeline.get("pr_draft") or {}
    preflight = timeline.get("github_pr_preflight") or {}
    branch_push = timeline.get("github_branch_push") or {}
    pr_open = timeline.get("github_pr_open") or {}

    return {
        "patch_diff_present": bool(diff_text.strip()),
        "patch_contains_pilot_execution_log_heading": "## Pilot Execution Log" in diff_text
        or "## Pilot Execution Log" in new_content,
        "patch_contains_table_header": "| Date | Issue | Stages Reached | PR | Operator Effort Notes |"
        in diff_text
        or "| Date | Issue | Stages Reached | PR | Operator Effort Notes |" in new_content,
        "patch_contains_issue_ref": "pilotmain/AethOS#1" in diff_text or "pilotmain/AethOS#1" in new_content,
        "verification_status": classification.get("status") or verification.get("status"),
        "verification_passed": classification.get("status") == "passed",
        "pr_draft_present": bool(pr_draft),
        "preflight_present": bool(preflight),
        "preflight_approved": github_pr_creation_approved_for_plan(plan_id=plan_id),
        "branch_push_status": branch_push.get("status"),
        "branch_push_completed": branch_push_completed_for_plan(plan_id=plan_id),
        "pr_open_status": pr_open.get("status"),
        "pr_open_completed": github_pr_open_completed_for_plan(plan_id=plan_id),
        "pr_url": pr_open.get("pr_url") or pr_open.get("html_url"),
    }


def main() -> int:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        build_end_to_end_repo_development_pilot_harness,
        run_end_to_end_repo_development_pilot,
    )
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
        list_pilot_run_audits,
    )
    from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_service import (
        build_issue_intent_alignment,
    )
    from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline
    from aethos_core.software_delivery.github_pr_open_store import github_pr_open_completed_for_plan
    from aethos_core.software_delivery.workspace_verification_store import workspace_verification_passed

    _clear_pilot_stores()
    started_at = datetime.now(UTC).isoformat()

    print(f"\n=== DOGFOOD PILOT 3 — session={SESSION} issue={REPO_ISSUE} ===\n")
    pilot_outcome = run_end_to_end_repo_development_pilot(session_id=SESSION, repo_issue=REPO_ISSUE)

    timeline = build_software_delivery_timeline(session_id=SESSION)
    plan = timeline.get("plan") or {}
    plan_id = str(plan.get("plan_id") or "")
    harness = build_end_to_end_repo_development_pilot_harness(session_id=SESSION)
    alignment_result = build_issue_intent_alignment(session_id=SESSION)
    alignment_board = alignment_result.issue_intent_alignment if alignment_result.ok else {}
    evidence = build_evidence_bundle(session_id=SESSION)
    audits = list_pilot_run_audits(session_id=SESSION)
    content_checks = _patch_content_checks(timeline, plan_id=plan_id)

    plan_goal = str(((plan.get("governed_plan") or {}).get("goal") or ""))
    fidelity = plan.get("issue_intake_scope_fidelity") or {}
    proposal = timeline.get("patch_proposal") or {}

    receipt: dict[str, Any] = {
        "schema_version": "dogfood_pilot_3_live_receipt_v1",
        "session_id": SESSION,
        "repo_issue": REPO_ISSUE,
        "started_at": started_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "primary_success_criterion": "full_loop_pr_open_with_correct_doc_patch_content",
        "plan_goal": plan_goal,
        "plan_goal_correct": "Fix GitHub workflow rerun resolution" not in plan_goal
        and ("Pilot Execution Log" in plan_goal or "Dogfood Pilot" in plan_goal),
        "expected_file": DOC_TARGET,
        "expected_file_correct": DOC_TARGET in list(fidelity.get("expected_files") or []),
        "proposed_files": list(proposal.get("proposed_files") or []),
        "proposed_file_correct": DOC_TARGET in list(proposal.get("proposed_files") or []),
        "alignment_score": alignment_board.get("alignment_score"),
        "intent_alignment_gate_satisfied": alignment_board.get("intent_alignment_gate_satisfied"),
        "pilot_outcome_ok": pilot_outcome.ok,
        "pilot_outcome_detail": pilot_outcome.detail,
        "pilot_stages_completed": pilot_outcome.stages_completed,
        "pilot_blockers": pilot_outcome.blockers,
        "pilot_audit_id": pilot_outcome.audit_id,
        "terminal_stage_reached": "pr_open" in pilot_outcome.stages_completed
        or github_pr_open_completed_for_plan(plan_id=plan_id),
        "content_checks": content_checks,
        "verification_passed": workspace_verification_passed(plan_id=plan_id),
        "merge_performed": False,
        "deploy_performed": False,
        "railway_mutation_detected": pilot_outcome.chat_steps
        and any("railway" in str(s.get("route_id") or "").lower() for s in pilot_outcome.chat_steps),
        "pilot_run_chat_steps": pilot_outcome.chat_steps,
        "issue_intake_scope_fidelity": fidelity,
        "patch_unified_diffs": proposal.get("unified_diffs"),
        "evidence_bundle_ok": evidence.ok if evidence else False,
        "pilot_audit_count": len(audits),
        "latest_audit_outcome": audits[-1].get("outcome") if audits else None,
        "harness_pending_command_count": harness.end_to_end_repo_development_pilot_harness.get(
            "pending_command_count"
        ),
    }

    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = RECEIPT_DIR / f"dogfood-pilot-3-{stamp}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    success = all(
        [
            receipt["plan_goal_correct"],
            receipt["expected_file_correct"],
            receipt["proposed_file_correct"],
            content_checks["patch_contains_pilot_execution_log_heading"],
            content_checks["patch_contains_table_header"],
            receipt["verification_passed"],
            bool(timeline.get("pr_draft")),
            content_checks["preflight_approved"],
            content_checks["branch_push_completed"],
            content_checks["pr_open_completed"],
            pilot_outcome.ok,
            not receipt["railway_mutation_detected"],
        ]
    )

    print("\n=== DOGFOOD PILOT 3 RECEIPT (summary) ===")
    print(
        json.dumps(
            {
                "success": success,
                "plan_goal_correct": receipt["plan_goal_correct"],
                "expected_file_correct": receipt["expected_file_correct"],
                "proposed_file_correct": receipt["proposed_file_correct"],
                "patch_content_ok": content_checks["patch_contains_pilot_execution_log_heading"],
                "verification_passed": receipt["verification_passed"],
                "pr_draft_present": content_checks["pr_draft_present"],
                "preflight_approved": content_checks["preflight_approved"],
                "branch_push_completed": content_checks["branch_push_completed"],
                "pr_open_completed": content_checks["pr_open_completed"],
                "pr_url": content_checks["pr_url"],
                "pilot_outcome_ok": pilot_outcome.ok,
                "pilot_blockers": pilot_outcome.blockers,
                "stages_completed": pilot_outcome.stages_completed,
            },
            indent=2,
        )
    )
    print(f"\nFull receipt: {receipt_path}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
