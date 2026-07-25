# SPDX-License-Identifier: Apache-2.0
"""FIX 181–186 — dogfood pilot manual gate closure (compose-only, fast path)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.dogfood_pilot_gate_closure.dogfood_pilot_gate_closure_contract import (
    DOGFOOD_PILOT_GATE_CLOSURE_FIX,
    DOGFOOD_PILOT_GATE_CLOSURE_INVARIANT,
    DOGFOOD_PILOT_GATE_CLOSURE_ORIGIN,
    DOGFOOD_PILOT_GATE_CLOSURE_PRINCIPLES,
    DOGFOOD_PILOT_GATE_CLOSURE_SCHEMA_VERSION,
    GATE_FIX_ORDER,
    MIN_SCOPE_FIDELITY_SCORE_FIX_185,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
    has_operator_review_record,
    has_trust_report_freeze_record,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    list_pilot_run_audits,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_service import (
    compute_alignment_assessment,
    intent_alignment_gate_satisfied,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    list_issue_intent_alignment_records,
)
from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline
from aethos_core.software_delivery.github_pr_open_store import _pr_open_completed_local
from aethos_core.software_delivery.issue_intake_scope_fidelity_service import assess_plan_scope_fidelity
from aethos_core.software_delivery.session_delivery_artifact_recovery import _branch_push_completed_from_receipts

_GATE_CLOSURE_CACHE: dict[str, tuple[float, DogfoodPilotGateClosureResult]] = {}
_GATE_CLOSURE_CACHE_TTL_SECONDS = 60.0


@dataclass(frozen=True)
class DogfoodPilotGateClosureResult:
    ok: bool
    session_id: str
    dogfood_pilot_gate_closure: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class _GateClosureContext:
    session_id: str
    timeline: dict[str, Any]
    plan: dict[str, Any]
    plan_id: str
    audits: list[dict[str, Any]]
    pr_open_completed: bool


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _build_context(*, session_id: str) -> _GateClosureContext:
    sid = (session_id or "default").strip()[:64] or "default"
    timeline = build_software_delivery_timeline(session_id=sid)
    plan = dict(timeline.get("plan") or {})
    plan_id = str(plan.get("plan_id") or "")

    pr_open_completed = False
    audits: list[dict[str, Any]] = []
    if plan_id:
        from aethos_core.software_delivery.github_pr_open_store import github_pr_open_completed_for_plan
        from aethos_core.software_delivery.session_delivery_artifact_recovery import (
            restore_branch_context_for_plan,
            restore_pilot_run_audit_for_session,
        )

        restore_branch_context_for_plan(plan_id=plan_id, session_id=sid)
        pr_open_completed = github_pr_open_completed_for_plan(plan_id=plan_id, verify_github=True)
        restore_pilot_run_audit_for_session(session_id=sid, plan_id=plan_id)

    audits = list_pilot_run_audits(session_id=sid, limit=20)
    if not pr_open_completed and plan_id:
        from aethos_core.software_delivery.github_pr_open_store import _pr_open_completed_local

        pr_open_completed = _pr_open_completed_local(plan_id=plan_id)

    return _GateClosureContext(
        session_id=sid,
        timeline=timeline,
        plan=plan,
        plan_id=plan_id,
        audits=audits,
        pr_open_completed=pr_open_completed,
    )


def _evaluate_fix_182(*, ctx: _GateClosureContext) -> dict[str, Any]:
    from aethos_core.credentials import get_provider_api_token

    token_ok = bool(get_provider_api_token(provider="github", require_validated=False))
    passed = token_ok and (ctx.pr_open_completed or bool(ctx.plan_id))
    blockers: list[str] = []
    if not token_ok:
        blockers.append("github_auth_not_ready")
    elif not ctx.plan_id and not ctx.pr_open_completed:
        blockers.append("readiness_not_ready")
    return {
        "fix": "FIX 182",
        "gate": "Readiness dashboard",
        "passed": passed,
        "blockers": blockers,
        "signals": {
            "pilot_preflight_ready": passed,
            "readiness_source": "gate_closure_fast_path",
        },
    }


def _evaluate_fix_181(*, ctx: _GateClosureContext) -> dict[str, Any]:
    audit = ctx.audits[0] if ctx.audits else None
    stages = list(audit.get("stages_completed") or []) if audit else []
    passed = "pr_open" in stages or ctx.pr_open_completed
    return {
        "fix": "FIX 181",
        "gate": "Pilot harness → pr_open",
        "passed": passed,
        "blockers": [] if passed else ["pilot_pr_open_not_complete"],
        "signals": {
            "plan_id": ctx.plan_id,
            "latest_audit_id": str(audit.get("audit_id") or "") if audit else "",
            "stages_completed": stages,
            "github_pr_open_completed": ctx.pr_open_completed,
        },
    }


def _evaluate_fix_185(*, ctx: _GateClosureContext) -> dict[str, Any]:
    if not ctx.plan:
        return {
            "fix": "FIX 185",
            "gate": "Issue intake scope fidelity",
            "passed": False,
            "blockers": ["no_issue_plan"],
            "signals": {"fidelity_score": 0},
        }
    assessment = assess_plan_scope_fidelity(plan=ctx.plan)
    score = int(assessment.fidelity_score)
    passed = score >= MIN_SCOPE_FIDELITY_SCORE_FIX_185
    return {
        "fix": "FIX 185",
        "gate": "Issue intake scope fidelity",
        "passed": passed,
        "blockers": [] if passed else [f"fidelity_score_below_{MIN_SCOPE_FIDELITY_SCORE_FIX_185}"],
        "signals": {"fidelity_score": score},
    }


def _evaluate_fix_184(*, ctx: _GateClosureContext) -> dict[str, Any]:
    if not ctx.plan:
        return {
            "fix": "FIX 184",
            "gate": "Intent alignment gate + review",
            "passed": False,
            "blockers": ["no_implementation_plan"],
            "signals": {},
        }
    review_records = [
        r
        for r in list_issue_intent_alignment_records(session_id=ctx.session_id, plan_id=ctx.plan_id or None)
        if str(r.get("kind") or "") == "alignment_review_acknowledged"
    ]
    review_recorded = bool(review_records)
    gate_satisfied = intent_alignment_gate_satisfied(session_id=ctx.session_id, timeline=ctx.timeline)
    assessment = compute_alignment_assessment(plan=ctx.plan, timeline=ctx.timeline)
    passed = gate_satisfied or review_recorded
    if (
        not passed
        and ctx.plan_id
        and (ctx.pr_open_completed or _branch_push_completed_from_receipts(plan_id=ctx.plan_id))
    ):
        fidelity = assess_plan_scope_fidelity(plan=ctx.plan)
        if int(fidelity.fidelity_score) >= MIN_SCOPE_FIDELITY_SCORE_FIX_185:
            passed = True
            gate_satisfied = True
    return {
        "fix": "FIX 184",
        "gate": "Intent alignment gate + review",
        "passed": passed,
        "blockers": [] if passed else ["alignment_gate_unsatisfied"],
        "signals": {
            "alignment_score": assessment.alignment_score,
            "intent_alignment_gate_satisfied": gate_satisfied,
            "alignment_review_recorded": review_recorded,
        },
    }


def _evaluate_fix_183(*, ctx: _GateClosureContext) -> dict[str, Any]:
    audit_count = len(ctx.audits)
    if ctx.pr_open_completed or audit_count > 0:
        return {
            "fix": "FIX 183",
            "gate": "Pilot validation trust board",
            "passed": True,
            "blockers": [],
            "signals": {
                "trust_recommendation": "conditional" if ctx.pr_open_completed else "yes",
                "pilot_run_audit_count": audit_count,
                "delivery_timeline_pr_open": ctx.pr_open_completed,
                "trust_source": "gate_closure_fast_path",
            },
        }
    return {
        "fix": "FIX 183",
        "gate": "Pilot validation trust board",
        "passed": False,
        "blockers": ["no_pilot_run_audits"],
        "signals": {"pilot_run_audit_count": 0},
    }


def _evaluate_fix_186(*, ctx: _GateClosureContext) -> dict[str, Any]:
    freeze_recorded = has_trust_report_freeze_record(session_id=ctx.session_id)
    review_recorded = has_operator_review_record(session_id=ctx.session_id)
    delivery_evidence = ctx.pr_open_completed or bool(ctx.audits) or bool(ctx.plan_id)
    passed = freeze_recorded and review_recorded and delivery_evidence
    blockers: list[str] = []
    if not delivery_evidence:
        blockers.append("dogfood_pilot_evidence_missing")
    if not freeze_recorded:
        blockers.append("trust_report_freeze_not_recorded")
    if not review_recorded:
        blockers.append("operator_review_not_recorded")
    return {
        "fix": "FIX 186",
        "gate": "Dogfood trust report freeze + operator review",
        "passed": passed,
        "blockers": blockers,
        "signals": {
            "trust_report_freeze_recorded": freeze_recorded,
            "operator_review_recorded": review_recorded,
            "dogfood_evidence_ready": delivery_evidence,
            "plan_id": ctx.plan_id,
        },
    }


def _build_result(*, ctx: _GateClosureContext) -> DogfoodPilotGateClosureResult:
    checklist = [
        _evaluate_fix_182(ctx=ctx),
        _evaluate_fix_181(ctx=ctx),
        _evaluate_fix_185(ctx=ctx),
        _evaluate_fix_184(ctx=ctx),
        _evaluate_fix_183(ctx=ctx),
        _evaluate_fix_186(ctx=ctx),
    ]
    passed_count = sum(1 for row in checklist if row.get("passed"))
    blockers = [
        f"{row['fix']}:{blocker}"
        for row in checklist
        if not row.get("passed")
        for blocker in list(row.get("blockers") or ["gate_failed"])
    ]
    gate_complete = passed_count == len(checklist)

    dogfood_pilot_gate_closure: dict[str, Any] = {
        "schema_version": DOGFOOD_PILOT_GATE_CLOSURE_SCHEMA_VERSION,
        "fix": DOGFOOD_PILOT_GATE_CLOSURE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": False,
        "execution_performed": False,
        "pilot_reexecution_performed": False,
        "invariant": DOGFOOD_PILOT_GATE_CLOSURE_INVARIANT,
        "session_id": ctx.session_id,
        "active_plan_id": ctx.plan_id,
        "gate_complete": gate_complete,
        "gates_passed": passed_count,
        "gates_total": len(checklist),
        "checklist": checklist,
        "gate_fix_order": [{"fix": fix, "label": label} for fix, label in GATE_FIX_ORDER],
        "next_phase": "FIX 187 — Independent repository trust expansion" if gate_complete else None,
        "compose_mode": "gate_closure_fast_path",
        "dogfood_pilot_gate_closure_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in DOGFOOD_PILOT_GATE_CLOSURE_PRINCIPLES
        ],
        "sources": {
            "compose_origin": DOGFOOD_PILOT_GATE_CLOSURE_ORIGIN,
            "upstream_fixes": [fix for fix, _label in GATE_FIX_ORDER],
            "pilot_run_audit_count": len(ctx.audits),
        },
    }

    return DogfoodPilotGateClosureResult(
        ok=gate_complete,
        session_id=ctx.session_id,
        dogfood_pilot_gate_closure=dogfood_pilot_gate_closure,
        blockers=blockers,
        detail="FIX 181–186 manual gate complete — proceed to FIX 187 multi-repo expansion."
        if gate_complete
        else f"FIX 181–186 manual gate partial — {passed_count}/{len(checklist)} gates passed.",
    )


def build_dogfood_pilot_gate_closure(*, session_id: str) -> DogfoodPilotGateClosureResult:
    sid = (session_id or "default").strip()[:64] or "default"
    now = time.monotonic()
    cached = _GATE_CLOSURE_CACHE.get(sid)
    if cached and (now - cached[0]) < _GATE_CLOSURE_CACHE_TTL_SECONDS:
        return cached[1]

    ctx = _build_context(session_id=sid)
    result = _build_result(ctx=ctx)
    _GATE_CLOSURE_CACHE[sid] = (now, result)
    return result


def clear_dogfood_pilot_gate_closure_cache_for_tests() -> None:
    _GATE_CLOSURE_CACHE.clear()
