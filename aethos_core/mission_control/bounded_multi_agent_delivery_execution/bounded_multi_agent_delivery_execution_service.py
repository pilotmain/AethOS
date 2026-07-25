# SPDX-License-Identifier: Apache-2.0
"""FIX 189 — bounded multi-agent delivery execution service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_189_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_service import (
    build_bounded_execution_participation,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
    AGENT_EXECUTION_AUTHORITY_FIX_189,
    AGENT_EXECUTION_CATALOG,
    AGENT_EXECUTION_PIPELINE_ORDER,
    AGENT_EXECUTION_PIPELINE_STATES,
    AGENT_EXECUTION_ROLE_IDS,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_189,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_FIX,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_INVARIANT,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_PRINCIPLES,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_SCHEMA_VERSION,
    BOUNDED_WORK_PERFORMED_FIX_189,
    DEPLOY_AUTHORITY_FIX_189,
    FORBIDDEN_EXECUTION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_189,
    GOVERNANCE_MUTATION_PERFORMED_FIX_189,
    MERGE_AUTHORITY_FIX_189,
    MUTATION_PERFORMED_FIX_189,
    PROVIDER_AUTHORITY_FIX_189,
    RAILWAY_AUTHORITY_FIX_189,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_executors import (
    EXECUTION_RUNNERS,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
    list_agent_execution_receipts,
    list_bounded_multi_agent_delivery_execution_records,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
    build_bounded_delivery_work_packages,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_service import (
    build_mission_authorization,
)


@dataclass(frozen=True)
class BoundedMultiAgentDeliveryExecutionResult:
    ok: bool
    session_id: str
    bounded_multi_agent_delivery_execution: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class BoundedMultiAgentDeliveryExecutionRunResult:
    ok: bool
    session_id: str
    role_id: str = ""
    pipeline: bool = False
    agent_outputs: list[dict[str, Any]] = field(default_factory=list)
    pipeline_state: str = "BLOCKED"
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _authorization_granted(mission_authorization: dict[str, Any]) -> bool:
    envelopes = _sections(mission_authorization).get("bounded_work_envelope") or []
    for row in reversed(envelopes):
        if row.get("envelope_id") == "bounded-work-envelope":
            return bool(row.get("authorization_granted"))
    return False


def _execution_gates(
    *,
    mission_authorization: dict[str, Any],
    work_packages: dict[str, Any],
    participation: dict[str, Any],
) -> dict[str, Any]:
    auth_ok = _authorization_granted(mission_authorization)
    packages_ok = bool(_sections(work_packages).get("role_scoped_work_packages"))
    participation_ok = bool(participation.get("participation_ready"))
    return {
        "fix_170_authorization_granted": auth_ok,
        "fix_168_work_packages_ok": packages_ok,
        "fix_171_participation_ready": participation_ok,
        "eligible_to_run_pipeline": auth_ok and packages_ok and participation_ok,
        "read_only": True,
    }


def _agent_execution_packages(
    *,
    work_packages: dict[str, Any],
    receipts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    packages_by_role = {
        str(row.get("agent_role_id")): row
        for row in (_sections(work_packages).get("role_scoped_work_packages") or [])
        if row.get("agent_role_id")
    }
    receipt_by_role = {
        str((r.get("metadata") or {}).get("agent_role_id") or ""): r for r in receipts
    }
    rows: list[dict[str, Any]] = []
    for role_id, display, focus in AGENT_EXECUTION_CATALOG:
        pkg = packages_by_role.get(role_id) or {}
        receipt = receipt_by_role.get(role_id)
        meta = (receipt or {}).get("metadata") or {}
        rows.append(
            {
                "execution_package_id": f"exec-{role_id}",
                "agent_role_id": role_id,
                "display_name": display,
                "focus": focus,
                "work_package_id": pkg.get("package_id"),
                "work_performed": bool(meta.get("work_performed")),
                "artifact_type": meta.get("artifact_type"),
                "agent_execution_authority": AGENT_EXECUTION_AUTHORITY_FIX_189,
                "read_only": True,
            }
        )
    return rows


def _agent_execution_registry(*, receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    registry: list[dict[str, Any]] = []
    for receipt in receipts:
        meta = dict(receipt.get("metadata") or {})
        registry.append(
            {
                "receipt_id": receipt.get("record_id"),
                "agent_role_id": meta.get("agent_role_id"),
                "status": meta.get("status"),
                "artifact_type": meta.get("artifact_type"),
                "work_performed": meta.get("work_performed"),
                "recorded_at": receipt.get("recorded_at"),
                "read_only": True,
            }
        )
    return registry


def _pipeline_state_from_receipts(receipts: list[dict[str, Any]], *, gates: dict[str, Any]) -> str:
    if not gates.get("eligible_to_run_pipeline"):
        return "BLOCKED"
    completed = {
        str((r.get("metadata") or {}).get("agent_role_id"))
        for r in receipts
        if (r.get("metadata") or {}).get("work_performed")
    }
    if completed >= set(AGENT_EXECUTION_PIPELINE_ORDER):
        return "PIPELINE_COMPLETE"
    for role_id in AGENT_EXECUTION_PIPELINE_ORDER:
        if role_id not in completed:
            if not receipts:
                return "READY"
            prefix = role_id.replace("_agent", "").upper()
            if role_id == "diff_audit_agent":
                return "DIFF_AUDIT_RUNNING" if role_id not in completed else "DIFF_AUDIT_COMPLETE"
            return f"{prefix}_RUNNING"
    return "PIPELINE_COMPLETE"


def _execution_readiness(*, pipeline_state: str, gates: dict[str, Any]) -> dict[str, Any]:
    label = "blocked"
    if pipeline_state == "PIPELINE_COMPLETE":
        label = "pipeline_complete"
    elif pipeline_state == "READY":
        label = "ready_for_pipeline"
    elif pipeline_state.endswith("_RUNNING"):
        label = "pipeline_in_progress"
    elif gates.get("eligible_to_run_pipeline"):
        label = "partial"
    return {
        "assessment_id": "agent-execution-readiness",
        "assessment_label": label,
        "pipeline_state": pipeline_state,
        "downstream_gate_chain_required": True,
        "human_admission_required": pipeline_state == "PIPELINE_COMPLETE",
        "read_only": True,
    }


def build_bounded_multi_agent_delivery_execution(
    *, session_id: str
) -> BoundedMultiAgentDeliveryExecutionResult:
    sid = (session_id or "default").strip()[:64] or "default"

    auth_result = build_mission_authorization(session_id=sid)
    mission_authorization = auth_result.mission_authorization if auth_result.ok else {}
    packages_result = build_bounded_delivery_work_packages(session_id=sid)
    work_packages = packages_result.bounded_delivery_work_packages if packages_result.ok else {}
    participation_result = build_bounded_execution_participation(session_id=sid)
    participation = (
        participation_result.bounded_execution_participation if participation_result.ok else {}
    )

    plan_id = str(mission_authorization.get("plan_id") or work_packages.get("plan_id") or "") or None
    correlation_id = (
        str(mission_authorization.get("correlation_id") or work_packages.get("correlation_id") or "")
        or None
    )

    records = list_bounded_multi_agent_delivery_execution_records(session_id=sid, plan_id=plan_id)
    receipts = list_agent_execution_receipts(session_id=sid, plan_id=plan_id)
    gates = _execution_gates(
        mission_authorization=mission_authorization,
        work_packages=work_packages,
        participation=participation,
    )
    pipeline_state = _pipeline_state_from_receipts(receipts, gates=gates)

    blockers: list[str] = []
    if not gates["fix_170_authorization_granted"]:
        blockers.append("fix_170_authorization_not_granted")
    if not gates["fix_168_work_packages_ok"]:
        blockers.append("fix_168_work_packages_missing")
    if not gates["fix_171_participation_ready"]:
        blockers.append("fix_171_participation_not_ready")

    sections = {
        "execution_gates": [gates],
        "agent_execution_packages": _agent_execution_packages(
            work_packages=work_packages,
            receipts=receipts,
        ),
        "agent_execution_registry": _agent_execution_registry(receipts=receipts),
        "execution_pipeline_state_machine": [
            {
                "state_id": "agent-execution-pipeline",
                "current_state": pipeline_state,
                "states": list(AGENT_EXECUTION_PIPELINE_STATES),
                "pipeline_order": list(AGENT_EXECUTION_PIPELINE_ORDER),
                "read_only": True,
            }
        ],
        "execution_readiness_assessment": [_execution_readiness(pipeline_state=pipeline_state, gates=gates)],
        "forbidden_execution_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_EXECUTION_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_SCHEMA_VERSION,
        "fix": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_189,
        "bounded_work_performed": BOUNDED_WORK_PERFORMED_FIX_189,
        "agent_execution_authority": AGENT_EXECUTION_AUTHORITY_FIX_189,
        "merge_authority": MERGE_AUTHORITY_FIX_189,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_189,
        "railway_authority": RAILWAY_AUTHORITY_FIX_189,
        "provider_authority": PROVIDER_AUTHORITY_FIX_189,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_189,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_189,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_189,
        "invariant": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "pipeline_state": pipeline_state,
        "execution_ready": gates["eligible_to_run_pipeline"],
        "sections": sections,
        "execution_record_count": len(records),
        "agent_role_ids": list(AGENT_EXECUTION_ROLE_IDS),
        "fix_189_certification_requirements": list(FIX_189_CERTIFICATION_REQUIREMENTS),
        "bounded_multi_agent_delivery_execution_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_PRINCIPLES
        ],
        "sources": {
            "composes_fix_168_171_170": True,
            "mission_authorization": auth_result.ok,
            "work_packages": packages_result.ok,
            "participation": participation_result.ok,
        },
    }

    return BoundedMultiAgentDeliveryExecutionResult(
        ok=True,
        session_id=sid,
        bounded_multi_agent_delivery_execution=payload,
        blockers=blockers,
        detail="Bounded multi-agent delivery execution assembled (agents work — gates decide).",
    )


def _persist_agent_output(
    *,
    session_id: str,
    plan_id: str | None,
    correlation_id: str | None,
    output: dict[str, Any],
) -> None:
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        append_bounded_multi_agent_delivery_execution_record,
    )

    role_id = str(output.get("agent_role_id") or "")
    append_bounded_multi_agent_delivery_execution_record(
        session_id=session_id,
        kind="agent_execution_receipt",
        content=f"{role_id}:{output.get('status')}:{output.get('artifact_type')}",
        plan_id=plan_id,
        correlation_id=correlation_id,
        metadata={
            "agent_role_id": role_id,
            "status": output.get("status"),
            "artifact_type": output.get("artifact_type"),
            "work_performed": output.get("work_performed"),
            "blockers": output.get("blockers"),
            "risk_score": output.get("risk_score"),
            "diff_audit": output.get("diff_audit"),
            "verification_package": output.get("verification_package"),
        },
    )


def run_bounded_multi_agent_delivery_execution(
    *,
    session_id: str,
    role_id: str | None = None,
) -> BoundedMultiAgentDeliveryExecutionRunResult:
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        append_bounded_multi_agent_delivery_execution_record,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    view = build_bounded_multi_agent_delivery_execution(session_id=sid)
    gates = (view.bounded_multi_agent_delivery_execution.get("sections") or {}).get("execution_gates") or [{}]
    gate_row = gates[0] if gates else {}

    if not gate_row.get("eligible_to_run_pipeline"):
        return BoundedMultiAgentDeliveryExecutionRunResult(
            ok=False,
            session_id=sid,
            blockers=view.blockers or ["execution_gates_not_satisfied"],
            detail="Agent execution blocked — authorization envelope and participation required.",
        )

    plan_id = view.bounded_multi_agent_delivery_execution.get("plan_id")
    correlation_id = view.bounded_multi_agent_delivery_execution.get("correlation_id")

    roles = list(AGENT_EXECUTION_PIPELINE_ORDER) if role_id in (None, "__pipeline__") else [role_id]
    if role_id and role_id not in AGENT_EXECUTION_ROLE_IDS:
        return BoundedMultiAgentDeliveryExecutionRunResult(
            ok=False,
            session_id=sid,
            role_id=role_id,
            blockers=["invalid_agent_role"],
            detail=f"Role must be one of: {', '.join(AGENT_EXECUTION_ROLE_IDS)}",
        )

    append_bounded_multi_agent_delivery_execution_record(
        session_id=sid,
        kind="pipeline_transition",
        content=f"PIPELINE_START:{','.join(roles)}",
        plan_id=str(plan_id) if plan_id else None,
        correlation_id=str(correlation_id) if correlation_id else None,
    )

    outputs: list[dict[str, Any]] = []
    blockers: list[str] = []
    for rid in roles:
        runner = EXECUTION_RUNNERS.get(rid)
        if not runner:
            continue
        output = runner(session_id=sid, plan_id=str(plan_id) if plan_id else None)
        outputs.append(output)
        _persist_agent_output(
            session_id=sid,
            plan_id=str(plan_id) if plan_id else None,
            correlation_id=str(correlation_id) if correlation_id else None,
            output=output,
        )
        if output.get("blockers"):
            blockers.extend([str(b) for b in output.get("blockers") or []])

    pipeline_state = "PIPELINE_COMPLETE" if len(outputs) == len(roles) else "PARTIAL"
    append_bounded_multi_agent_delivery_execution_record(
        session_id=sid,
        kind="pipeline_transition",
        content=f"PIPELINE_END:{pipeline_state}",
        plan_id=str(plan_id) if plan_id else None,
        correlation_id=str(correlation_id) if correlation_id else None,
        metadata={"pipeline_state": pipeline_state, "agent_count": len(outputs)},
    )

    ok = all(o.get("work_performed") for o in outputs) if outputs else False
    return BoundedMultiAgentDeliveryExecutionRunResult(
        ok=ok,
        session_id=sid,
        role_id=role_id or "__pipeline__",
        pipeline=role_id in (None, "__pipeline__"),
        agent_outputs=outputs,
        pipeline_state=pipeline_state,
        blockers=blockers,
        detail=f"Agent execution package(s) complete for {len(outputs)} role(s). Gates decide downstream.",
    )
