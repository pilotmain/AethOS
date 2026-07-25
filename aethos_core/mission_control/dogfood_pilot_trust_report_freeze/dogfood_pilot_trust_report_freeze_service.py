# SPDX-License-Identifier: Apache-2.0
"""FIX 186 — dogfood pilot trust report freeze service (compose-only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_186_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_contract import (
    AUTONOMOUS_TRUST_REPORT_EXECUTION_ENABLED_FIX_186,
    DIRECT_EXECUTION_PERFORMED_FIX_186,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_186,
    DOGFOOD_DOC_TARGET,
    DOGFOOD_PILOT_SESSIONS,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_FIX,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_INVARIANT,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ORIGIN,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_PRINCIPLES,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
    DOGFOOD_REPO_ISSUE,
    EXECUTION_PERFORMED_FIX_186,
    FORBIDDEN_TRUST_REPORT_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_186,
    GOVERNANCE_MUTATION_PERFORMED_FIX_186,
    HIDDEN_PILOT_REEXECUTION_PERFORMED_FIX_186,
    MULTI_REPO_EXPANSION_BLOCKED_BY_DEFAULT_FIX_186,
    PILOT_REEXECUTION_PERFORMED_FIX_186,
    PROPOSED_MULTI_REPO_ORDER,
    TRUST_RECOMMENDATION_FIX_186,
    TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_186,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_183,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
    has_expansion_approval_record,
    has_trust_report_freeze_record,
    list_dogfood_pilot_trust_report_freeze_records,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    list_pilot_run_audits,
)
from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    list_issue_intent_alignment_records,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import replay_link_key, timeline_link_ref
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_service import (
    build_pilot_validation_trust_board,
)
from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline
from aethos_core.software_delivery.github_pr_open_store import load_github_pr_open_for_plan

_FROZEN_TIMELINE: tuple[dict[str, str], ...] = (
    {
        "pilot_id": "dogfood-pilot-1",
        "phase": "1",
        "question": "Can the governed loop run?",
        "answer": "Yes",
        "finding": "Wrong files selected",
        "failure_class": "wrong_file_targeting_drift",
        "fix_applied": "Exposed drift — addressed by FIX 184",
    },
    {
        "pilot_id": "dogfood-pilot-2",
        "phase": "2",
        "question": "Can the system detect drift before patch authority?",
        "answer": "Yes",
        "finding": "Alignment gate blocked execution",
        "failure_class": "patch_target_drift",
        "fix_applied": "FIX 184 — intent alignment gate",
    },
    {
        "pilot_id": "dogfood-pilot-3",
        "phase": "3",
        "question": "Can the system complete the correct change?",
        "answer": "Yes",
        "finding": "Correct file, correct content, PR Open achieved",
        "failure_class": "",
        "fix_applied": "FIX 185 intake scope fidelity + bounded doc patch content",
    },
)


@dataclass(frozen=True)
class DogfoodPilotTrustReportFreezeResult:
    ok: bool
    session_id: str
    dogfood_pilot_trust_report_freeze: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _latest_audit_for_session(session_id: str) -> dict[str, Any] | None:
    audits = list_pilot_run_audits(session_id=session_id, limit=20)
    if not audits:
        return None
    return audits[0]


def _discover_dogfood_audits() -> dict[str, dict[str, Any] | None]:
    discovered: dict[str, dict[str, Any] | None] = {}
    for sid in DOGFOOD_PILOT_SESSIONS:
        discovered[sid] = _latest_audit_for_session(sid)
    return discovered


def _receipt_refs() -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    root = _repo_root()
    for pilot_num, dirname in (
        (2, "dogfood_pilot_2_receipts"),
        (3, "dogfood_pilot_3_receipts"),
    ):
        receipt_dir = root / "data" / dirname
        if not receipt_dir.is_dir():
            continue
        paths = sorted(receipt_dir.glob("dogfood-pilot-*.json"), key=lambda p: p.stat().st_mtime)
        if paths:
            latest = paths[-1]
            refs.append(
                {
                    "pilot_id": f"dogfood-pilot-{pilot_num}",
                    "receipt_path": str(latest.relative_to(root)),
                    "recorded_at": datetime.fromtimestamp(latest.stat().st_mtime, UTC).isoformat(),
                    "read_only": True,
                }
            )
    return refs


def _compose_pilot_evidence(
    *,
    pilot_id: str,
    frozen: dict[str, str],
    audit: dict[str, Any] | None,
) -> dict[str, Any]:
    report = dict(audit.get("pilot_report") or {}) if audit else {}
    stages_satisfied = list(report.get("stages_satisfied") or [])
    if not stages_satisfied and audit:
        stages_satisfied = list(audit.get("stages_completed") or [])
    stages_pending = list(report.get("stages_pending") or [])
    blockers = list(audit.get("blockers") or []) if audit else []

    alignment_records: list[dict[str, Any]] = []
    if pilot_id == "dogfood-pilot-2":
        alignment_records = list_issue_intent_alignment_records(session_id=pilot_id)

    pr_meta: dict[str, Any] = {}
    if pilot_id == "dogfood-pilot-3" and audit:
        timeline = build_software_delivery_timeline(session_id=pilot_id)
        plan_id = str((timeline.get("plan") or {}).get("plan_id") or "")
        if plan_id:
            pr_open = load_github_pr_open_for_plan(plan_id=plan_id) or {}
            pr_meta = {
                "pr_url": pr_open.get("pr_url") or pr_open.get("html_url"),
                "pr_number": pr_open.get("pr_number"),
                "status": pr_open.get("status"),
                "branch_name": pr_open.get("branch_name"),
            }

    verification_status = ""
    if pilot_id == "dogfood-pilot-3":
        timeline = build_software_delivery_timeline(session_id=pilot_id)
        verification = timeline.get("workspace_verification") or {}
        classification = verification.get("classification") or {}
        verification_status = str(classification.get("status") or verification.get("status") or "")

    bundle_ok = False
    if audit:
        bundle = build_evidence_bundle(session_id=pilot_id)
        bundle_ok = bool(bundle.ok)

    return {
        "pilot_id": pilot_id,
        "phase": frozen.get("phase"),
        "question": frozen.get("question"),
        "answer": frozen.get("answer"),
        "finding": frozen.get("finding"),
        "failure_class": frozen.get("failure_class") or None,
        "fix_applied": frozen.get("fix_applied"),
        "audit_id": audit.get("audit_id") if audit else None,
        "pilot_outcome": audit.get("outcome") if audit else None,
        "stages_satisfied": stages_satisfied,
        "stages_pending": stages_pending,
        "stage_stopped_at": stages_pending[0] if stages_pending else ("pr_open" if "pr_open" in stages_satisfied else None),
        "blockers": blockers,
        "alignment_record_count": len(alignment_records),
        "alignment_gate_blocked": pilot_id == "dogfood-pilot-2" and bool(blockers or stages_pending),
        "verification_status": verification_status or None,
        "pr_metadata": pr_meta or None,
        "evidence_bundle_ok": bundle_ok,
        "read_only": True,
    }


def _trust_boundary_matrix() -> list[dict[str, Any]]:
    return [
        {
            "matrix_id": "conditionally-trusted",
            "status": "conditionally_trusted",
            "scope": "AethOS repository only",
            "capabilities": [
                "Bounded documentation changes",
                "Single-file modifications",
                "Low blast-radius repository work",
                "Governed path: Issue → Plan → Alignment → Patch → Verify → Push → PR Open",
            ],
            "read_only": True,
        },
        {
            "matrix_id": "not-yet-trusted",
            "status": "not_yet_trusted",
            "scope": "Requires independent pilot evidence per repository",
            "capabilities": [
                "Multi-file refactors",
                "Cross-subsystem changes",
                "Provider integrations",
                "Workflow modifications",
                "Railway operations",
                "Production-impacting changes",
                "pilotmain/pilot-os-ui",
                "pilotmain/atlas-trader",
                "pilotmain/nexora-monorepo-starter",
            ],
            "read_only": True,
        },
    ]


def _expansion_recommendation(
    *,
    freeze_recorded: bool,
    expansion_approved: bool,
    pilot3_complete: bool,
) -> dict[str, Any]:
    if expansion_approved:
        proceed = True
        reason = "Operator recorded explicit expansion approval — next repo pilot may proceed under independent evidence requirements."
    elif freeze_recorded and pilot3_complete:
        proceed = False
        reason = (
            "AethOS dogfood evidence baseline frozen. Multi-repo expansion remains blocked until "
            "operator reviews trust report and records explicit expansion approval."
        )
    elif pilot3_complete:
        proceed = False
        reason = "Pilot 3 complete — record trust report freeze and operator review before expansion."
    else:
        proceed = False
        reason = "Insufficient dogfood pilot evidence — complete Pilot 3 and freeze report before expansion."

    return {
        "recommendation_id": "multi-repo-expansion",
        "proceed": proceed,
        "multi_repo_expansion_blocked": not expansion_approved,
        "expansion_approved": expansion_approved,
        "trust_report_freeze_recorded": freeze_recorded,
        "proposed_order": list(PROPOSED_MULTI_REPO_ORDER),
        "next_repo_after_approval": PROPOSED_MULTI_REPO_ORDER[1] if expansion_approved else None,
        "reason": reason,
        "read_only": True,
    }


def _evidence_index(
    *,
    audits: dict[str, dict[str, Any] | None],
    pilot_evidence: list[dict[str, Any]],
    receipt_refs: list[dict[str, Any]],
    fix_183_board: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for pilot_id, audit in audits.items():
        if audit:
            entries.append(
                {
                    "ref_id": f"audit-{pilot_id}",
                    "kind": "pilot_run_audit",
                    "pilot_id": pilot_id,
                    "audit_id": audit.get("audit_id"),
                    "recorded_at": audit.get("recorded_at"),
                    "read_only": True,
                }
            )
    for receipt in receipt_refs:
        entries.append({"ref_id": f"receipt-{receipt.get('pilot_id')}", **receipt, "kind": "live_receipt"})
    if fix_183_board:
        entries.append(
            {
                "ref_id": "fix-183-trust-board",
                "kind": "pilot_validation_trust_board",
                "focus_audit_id": fix_183_board.get("focus_audit_id"),
                "trust_recommendation": fix_183_board.get("trust_recommendation"),
                "read_only": True,
            }
        )
    for item in pilot_evidence:
        if item.get("pr_metadata"):
            entries.append(
                {
                    "ref_id": f"pr-{item.get('pilot_id')}",
                    "kind": "github_pr_reference",
                    "pilot_id": item.get("pilot_id"),
                    **(item.get("pr_metadata") or {}),
                    "read_only": True,
                }
            )
    entries.append(
        {
            "ref_id": "dogfood-issue",
            "kind": "github_issue",
            "repo_issue": DOGFOOD_REPO_ISSUE,
            "expected_file": DOGFOOD_DOC_TARGET,
            "read_only": True,
        }
    )
    return entries


def build_dogfood_pilot_trust_report_freeze(*, session_id: str) -> DogfoodPilotTrustReportFreezeResult:
    sid = (session_id or "default").strip()[:64] or "default"
    exported_at = _exported_at()

    audits = _discover_dogfood_audits()
    pilot_evidence = [
        _compose_pilot_evidence(pilot_id=frozen["pilot_id"], frozen=frozen, audit=audits.get(frozen["pilot_id"]))
        for frozen in _FROZEN_TIMELINE
    ]
    receipt_refs = _receipt_refs()

    pilot3_audit = audits.get("dogfood-pilot-3")
    pilot3_report = dict(pilot3_audit.get("pilot_report") or {}) if pilot3_audit else {}
    pilot3_stages = list(pilot3_report.get("stages_satisfied") or pilot3_audit.get("stages_completed") or []) if pilot3_audit else []
    pilot3_complete = (
        pilot3_audit is not None
        and str(pilot3_audit.get("outcome") or "") == "complete"
        and "pr_open" in pilot3_stages
    )

    fix_183_result = build_pilot_validation_trust_board(session_id="dogfood-pilot-3")
    fix_183_board = fix_183_result.pilot_validation_trust_board if fix_183_result.ok else {}

    freeze_records = list_dogfood_pilot_trust_report_freeze_records()
    freeze_recorded = has_trust_report_freeze_record() or bool(freeze_records)
    expansion_approved = has_expansion_approval_record()

    blockers: list[str] = []
    if not any(audits.values()) and not receipt_refs:
        blockers.append("no_dogfood_pilot_artifacts")
    if not pilot3_complete and not receipt_refs:
        blockers.append("pilot_3_evidence_incomplete")

    timeline_ref = timeline_link_ref(
        lane="software_delivery",
        action="dogfood_pilot_trust_report_freeze",
        timestamp=exported_at,
    )
    replay_key = replay_link_key(
        source=DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ORIGIN,
        lane="software_delivery",
        action="dogfood_pilot_trust_report_freeze",
        timestamp=exported_at,
        anchor=DOGFOOD_REPO_ISSUE,
    )

    trust_rationale = (
        "Three-pilot evidence progression demonstrates loop execution, drift detection, intent preservation, "
        "correct patch generation, and governed PR creation without merge, deploy, Railway, or production mutation."
    )

    sections = {
        "frozen_evidence_timeline": pilot_evidence,
        "pilot_artifact_composition": [
            {
                "composition_id": "dogfood-pilot-artifacts",
                "pilot_sessions": list(DOGFOOD_PILOT_SESSIONS),
                "audits_discovered": sum(1 for a in audits.values() if a),
                "receipt_refs": len(receipt_refs),
                "trust_report_composes_artifacts_only": TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_186,
                "pilot_reexecution_performed": False,
                "read_only": True,
            }
        ],
        "fix_183_metrics_composition": [
            {
                "composition_id": "fix-183-trust-board-read",
                "session_id": "dogfood-pilot-3",
                "board_available": fix_183_result.ok,
                "approval_count": fix_183_board.get("approval_count"),
                "re_engagement_count": fix_183_board.get("re_engagement_count"),
                "human_effort_score": fix_183_board.get("human_effort_score"),
                "trust_recommendation_inputs": fix_183_board.get("trust_recommendation"),
                "read_only": True,
            }
        ],
        "trust_boundary_matrix": _trust_boundary_matrix(),
        "dogfood_trust_recommendation": [
            {
                "recommendation_id": "dogfood-trust-status",
                "trust_status": TRUST_RECOMMENDATION_FIX_186,
                "scope": "AethOS repository only",
                "work_types": [
                    "Bounded documentation changes",
                    "Single-file modifications",
                ],
                "trust_rationale": trust_rationale,
                "read_only": True,
            }
        ],
        "expansion_recommendation": [_expansion_recommendation(
            freeze_recorded=freeze_recorded,
            expansion_approved=expansion_approved,
            pilot3_complete=pilot3_complete,
        )],
        "evidence_index": _evidence_index(
            audits=audits,
            pilot_evidence=pilot_evidence,
            receipt_refs=receipt_refs,
            fix_183_board=fix_183_board or None,
        ),
        "scaling_gate": [
            {
                "gate_id": "multi-repo-scaling",
                "multi_repo_expansion_blocked": MULTI_REPO_EXPANSION_BLOCKED_BY_DEFAULT_FIX_186
                and not expansion_approved,
                "requires_trust_report_freeze_record": True,
                "requires_operator_review": True,
                "requires_explicit_expansion_approval": True,
                "no_inherited_trust": True,
                "read_only": True,
            }
        ],
        "audit_replay_linkage_at_trust_freeze": [
            {
                "link_id": "trust-freeze-audit-replay",
                "timeline_link_ref": timeline_ref,
                "replay_link_key": replay_key,
                "focus_pilot_id": "dogfood-pilot-3",
                "focus_audit_id": pilot3_audit.get("audit_id") if pilot3_audit else None,
                "read_only": True,
            }
        ],
        "forbidden_trust_report_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_TRUST_REPORT_ACTIONS
        ],
        "trust_report_integrity_scoring": [
            {
                "score_id": "dogfood-trust-freeze-integrity",
                "integrity_score": min(
                    100,
                    15
                    + (25 if any(audits.values()) else 0)
                    + (25 if pilot3_complete else 10 if receipt_refs else 0)
                    + (15 if fix_183_result.ok else 0)
                    + (10 if freeze_recorded else 5)
                    + (10 if TRUST_RECOMMENDATION_FIX_186 == "CONDITIONALLY_TRUSTED" else 0),
                ),
                "trust_report_composes_artifacts_only": True,
                "pilot_reexecution_performed": False,
                "read_only": True,
            }
        ],
    }

    dogfood_pilot_trust_report_freeze: dict[str, Any] = {
        "schema_version": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        "fix": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": False,
        "execution_performed": EXECUTION_PERFORMED_FIX_186,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_186,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_186,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_186,
        "autonomous_trust_report_execution_enabled": AUTONOMOUS_TRUST_REPORT_EXECUTION_ENABLED_FIX_186,
        "hidden_pilot_reexecution_performed": HIDDEN_PILOT_REEXECUTION_PERFORMED_FIX_186,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_186,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_186,
        "trust_report_composes_artifacts_only": TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_186,
        "multi_repo_expansion_blocked": MULTI_REPO_EXPANSION_BLOCKED_BY_DEFAULT_FIX_186
        and not expansion_approved,
        "invariant": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_INVARIANT,
        "session_id": sid,
        "repo_issue": DOGFOOD_REPO_ISSUE,
        "sections": sections,
        "trust_status": TRUST_RECOMMENDATION_FIX_186,
        "trust_report_freeze_recorded": freeze_recorded,
        "expansion_approved": expansion_approved,
        "pilot_3_complete": pilot3_complete,
        "freeze_record_count": len(freeze_records),
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_181_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_181),
            "fix_183_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_183),
        },
        "fix_186_certification_requirements": list(FIX_186_CERTIFICATION_REQUIREMENTS),
        "dogfood_pilot_trust_report_freeze_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in DOGFOOD_PILOT_TRUST_REPORT_FREEZE_PRINCIPLES
        ],
        "sources": {
            "dogfood_pilot_sessions": list(DOGFOOD_PILOT_SESSIONS),
            "pilot_audits_discovered": sum(1 for a in audits.values() if a),
            "live_receipt_refs": len(receipt_refs),
            "composes_fix_183_trust_board": fix_183_result.ok,
            "freeze_records": len(freeze_records),
        },
    }

    ok = pilot3_complete or bool(receipt_refs)
    if blockers and not ok:
        pass
    elif blockers:
        blockers = [b for b in blockers if b != "pilot_3_evidence_incomplete"]

    return DogfoodPilotTrustReportFreezeResult(
        ok=ok,
        session_id=sid,
        dogfood_pilot_trust_report_freeze=dogfood_pilot_trust_report_freeze,
        blockers=blockers if not ok else [],
        detail="Dogfood pilot trust report freeze composed from Pilots 1–3 artifacts (trust_report_freeze ≠ pilot_execution)."
        if ok
        else "Trust report unavailable — dogfood pilot evidence required.",
    )
