#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Live dogfood-pilot-2 run — issue #1 alignment gate regression."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SESSION = "dogfood-pilot-2"
REPO_ISSUE = "pilotmain/AethOS#1"
DOC_TARGET = "docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"
RECEIPT_DIR = ROOT / "data" / "dogfood_pilot_2_receipts"


def _chat(message: str, *, steps: list[dict[str, Any]]) -> dict[str, Any]:
    from aethos_core.chat.service import resolve_chat_turn

    turn = resolve_chat_turn(message, session_id=SESSION, apply_relational_layer=False)
    entry = {
        "message": message,
        "intent": turn.intent,
        "route_id": (turn.meta or {}).get("route_id"),
        "reply_excerpt": (turn.reply or "")[:500],
        "meta": dict(turn.meta or {}),
    }
    steps.append(entry)
    print(f"\n>>> {message[:80]}{'…' if len(message) > 80 else ''}")
    print(f"    intent={turn.intent} route={(turn.meta or {}).get('route_id')}")
    return entry


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
    from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
    from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline
    from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE

    from aethos_core.software_delivery.branch_orchestration_store import clear_for_tests as clear_branch
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as clear_plans
    from aethos_core.software_delivery.patch_proposal_store import clear_for_tests as clear_patch

    clear_plans()
    clear_branch()
    clear_patch()

    steps: list[dict[str, Any]] = []
    started_at = datetime.now(UTC).isoformat()

    _chat(f"pilot issue: {REPO_ISSUE}", steps=steps)
    _chat("pilot artifact: dogfood-pilot-2 alignment gate regression", steps=steps)
    _chat(f"analyze github issue {REPO_ISSUE}", steps=steps)
    _chat("create implementation plan", steps=steps)
    _chat(f"approve implementation planning\n{PLANNING_APPROVAL_PHRASE}", steps=steps)
    _chat(f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}", steps=steps)
    _chat("propose patch files", steps=steps)

    alignment_turn = _chat("show intent alignment", steps=steps)
    alignment_result = build_issue_intent_alignment(session_id=SESSION)
    alignment_board = alignment_result.issue_intent_alignment if alignment_result.ok else {}

    pilot_outcome = run_end_to_end_repo_development_pilot(session_id=SESSION, repo_issue=REPO_ISSUE)
    harness = build_end_to_end_repo_development_pilot_harness(session_id=SESSION)
    timeline = build_software_delivery_timeline(session_id=SESSION)
    evidence = build_evidence_bundle(session_id=SESSION)
    audits = list_pilot_run_audits(session_id=SESSION)

    sections = alignment_board.get("sections") or {}
    scope = (sections.get("issue_scope_extraction") or [{}])[0]
    targets = (sections.get("patch_target_validation") or [{}])[0]
    assessment = (sections.get("alignment_assessment") or [{}])[0]
    escalation = (sections.get("escalation_rules") or [{}])[0]
    review = (sections.get("recommended_review") or [{}])[0]

    stage_stopped_at = None
    if pilot_outcome.chat_steps:
        stage_stopped_at = pilot_outcome.chat_steps[-1].get("stage")
    if pilot_outcome.blockers:
        stage_stopped_at = stage_stopped_at or pilot_outcome.blockers[0]

    receipt: dict[str, Any] = {
        "schema_version": "dogfood_pilot_2_live_receipt_v1",
        "session_id": SESSION,
        "repo_issue": REPO_ISSUE,
        "started_at": started_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "primary_success_criterion": "intent_alignment_gate_fires_before_patch_authority",
        "full_pr_open_expected": False,
        "alignment_score": alignment_board.get("alignment_score"),
        "target_validation_status": alignment_board.get("target_validation_status"),
        "expected_files": scope.get("expected_targets") or targets.get("expected_targets"),
        "actual_proposed_files": targets.get("actual_targets"),
        "unexpected_files": targets.get("unexpected_files"),
        "escalation_required": alignment_board.get("escalation_required"),
        "escalation_reasons": escalation.get("escalation_reasons"),
        "human_reengagement_required": escalation.get("human_reengagement_required"),
        "operator_review_guidance": review.get("guidance"),
        "intent_alignment_gate_satisfied": alignment_board.get("intent_alignment_gate_satisfied"),
        "stage_stopped_at": stage_stopped_at,
        "pilot_outcome_ok": pilot_outcome.ok,
        "pilot_outcome_detail": pilot_outcome.detail,
        "pilot_stages_completed": pilot_outcome.stages_completed,
        "pilot_blockers": pilot_outcome.blockers,
        "pilot_audit_id": pilot_outcome.audit_id,
        "patch_execution_performed": alignment_board.get("patch_execution_performed"),
        "hidden_apply_in_pending_commands": any(
            "apply approved patch" in str(s.get("message") or "").lower() for s in steps
        ),
        "chat_steps": steps,
        "pilot_run_chat_steps": pilot_outcome.chat_steps,
        "plan_affected_files": (timeline.get("plan") or {}).get("affected_files"),
        "plan_goal": str(((timeline.get("plan") or {}).get("governed_plan") or {}).get("goal") or ""),
        "issue_intake_scope_fidelity": (timeline.get("plan") or {}).get("issue_intake_scope_fidelity"),
        "patch_proposed_files": (timeline.get("patch_proposal") or {}).get("proposed_files"),
        "evidence_bundle_ok": evidence.ok if evidence else False,
        "evidence_bundle_section_count": len((evidence.bundle.get("sections") or {}) if evidence.ok else {}),
        "pilot_audit_count": len(audits),
        "latest_audit_outcome": audits[-1].get("outcome") if audits else None,
        "alignment_route_meta": alignment_turn.get("meta"),
        "harness_pending_command_count": harness.end_to_end_repo_development_pilot_harness.get(
            "pending_command_count"
        ),
    }

    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = RECEIPT_DIR / f"dogfood-pilot-2-{stamp}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    print("\n=== DOGFOOD PILOT 2 RECEIPT ===")
    print(json.dumps(
        {
            k: receipt[k]
            for k in (
                "alignment_score",
                "expected_files",
                "actual_proposed_files",
                "escalation_required",
                "escalation_reasons",
                "stage_stopped_at",
                "human_reengagement_required",
                "intent_alignment_gate_satisfied",
                "pilot_outcome_ok",
                "pilot_audit_id",
                "evidence_bundle_ok",
            )
        },
        indent=2,
    ))
    print(f"\nFull receipt: {receipt_path}")

    fix_185_intake_pass = (
        DOC_TARGET in (receipt.get("expected_files") or [])
        and DOC_TARGET in (receipt.get("actual_proposed_files") or [])
        and "Fix GitHub workflow rerun resolution" not in str(receipt.get("plan_goal") or "")
    )
    fix_184_gate_regression_pass = (
        pilot_outcome.ok is False
        and (pilot_outcome.chat_steps and pilot_outcome.chat_steps[0].get("stage") == "intent_alignment")
        and alignment_board.get("escalation_required") is True
        and alignment_board.get("intent_alignment_gate_satisfied") is False
    )

    print(f"\nfix_185_intake_scope_fidelity_pass={fix_185_intake_pass}")
    print(f"fix_184_alignment_gate_regression_pass={fix_184_gate_regression_pass}")
    return 0 if fix_185_intake_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
