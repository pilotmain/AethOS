# SPDX-License-Identifier: Apache-2.0
"""FIX 250 — governed application generation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_250_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_application_generation.governed_application_generation_contract import (
    APPLICATION_GENERATION_AUTHORITY_FIX_250,
    BOUNDED_GENERATION_AGENT_ROLES,
    CODE_GENERATION_AUTHORITY_FIX_250,
    DEPLOYMENT_AUTHORITY_FIX_250,
    EXECUTION_PERFORMED_FIX_250,
    FORBIDDEN_APPLICATION_GENERATION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_250,
    GENERATION_DECISION_KINDS,
    GENERATION_PIPELINE_STAGES,
    GITHUB_MUTATION_AUTHORITY_FIX_250,
    GOVERNANCE_MUTATION_PERFORMED_FIX_250,
    GOVERNED_APPLICATION_GENERATION_COMPOSES_EVIDENCE_ONLY_FIX_250,
    GOVERNED_APPLICATION_GENERATION_FIX,
    GOVERNED_APPLICATION_GENERATION_HANDOFF_EXECUTABLE,
    GOVERNED_APPLICATION_GENERATION_HANDOFF_SCHEMA_VERSION,
    GOVERNED_APPLICATION_GENERATION_INVARIANT,
    GOVERNED_APPLICATION_GENERATION_PRINCIPLES,
    GOVERNED_APPLICATION_GENERATION_SCHEMA_VERSION,
    INFRASTRUCTURE_MUTATION_AUTHORITY_FIX_250,
    MERGE_AUTHORITY_FIX_250,
    MUTATION_PERFORMED_FIX_250,
    PROVIDER_AUTHORITY_FIX_250,
    REPOSITORY_CREATION_AUTHORITY_FIX_250,
    REQUIRED_GENERATION_EVIDENCE_IDS,
    ROLLBACK_AUTHORITY_FIX_250,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_store import (
    generation_decision_status,
    latest_record_by_kind,
    list_governed_application_generation_records,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import replay_link_key, timeline_link_ref
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session


@dataclass(frozen=True)
class GovernedApplicationGenerationResult:
    ok: bool
    session_id: str
    governed_application_generation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class GovernedApplicationGenerationHandoffResult:
    ok: bool
    session_id: str
    delivery_pipeline_handoff: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _record_content(*, session_id: str, kind: str) -> str:
    record = latest_record_by_kind(session_id=session_id, kind=kind)
    return str((record or {}).get("content") or "").strip()


def _record_meta(*, session_id: str, kind: str) -> dict[str, Any]:
    record = latest_record_by_kind(session_id=session_id, kind=kind)
    return dict((record or {}).get("metadata") or {})


def _product_name(*, session_id: str) -> str:
    meta = _record_meta(session_id=session_id, kind="prd_intake_note")
    if meta.get("product_name"):
        return str(meta["product_name"])
    prd = _record_content(session_id=session_id, kind="prd_intake_note")
    if prd:
        first_line = prd.splitlines()[0].strip()
        if first_line:
            return first_line[:80]
    return "unspecified-product"


def _product_understanding_package(*, session_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    prd = _record_content(session_id=session_id, kind="prd_intake_note")
    vision = _record_content(session_id=session_id, kind="product_vision_note")
    requirements = _record_content(session_id=session_id, kind="requirements_note")
    constraints = _record_content(session_id=session_id, kind="constraints_note")
    return {
        "package_id": "product-understanding",
        "product_name": _product_name(session_id=session_id),
        "prd_summary": prd[:500] if prd else None,
        "vision": vision[:500] if vision else None,
        "requirements_preview": requirements[:500] if requirements else None,
        "constraints_preview": constraints[:500] if constraints else None,
        "present": bool(prd),
        "read_only": True,
        "source_record_count": len(
            [r for r in records if str(r.get("kind") or "") in {"prd_intake_note", "product_vision_note", "requirements_note", "constraints_note"}]
        ),
    }


def _architecture_package(*, session_id: str, product: dict[str, Any]) -> dict[str, Any]:
    explicit = _record_content(session_id=session_id, kind="architecture_package_note")
    meta = _record_meta(session_id=session_id, kind="architecture_package_note")
    product_name = str(product.get("product_name") or "product")
    return {
        "package_id": "architecture-package",
        "system_architecture": meta.get("system_architecture")
        or f"Modular {product_name} with bounded service boundaries",
        "service_boundaries": meta.get("service_boundaries")
        or ["api-service", "web-application", "shared-library"],
        "data_architecture": meta.get("data_architecture") or "PostgreSQL primary store with event audit log",
        "api_architecture": meta.get("api_architecture") or "REST API with versioned contracts",
        "deployment_architecture": meta.get("deployment_architecture")
        or "GitHub Actions CI/CD to staging before production review",
        "operator_notes": explicit[:500] if explicit else None,
        "present": bool(explicit or product.get("present")),
        "read_only": True,
    }


def _repository_blueprint(*, session_id: str, architecture: dict[str, Any]) -> dict[str, Any]:
    explicit = _record_content(session_id=session_id, kind="repository_blueprint_note")
    meta = _record_meta(session_id=session_id, kind="repository_blueprint_note")
    folders = meta.get("folders") or [
        "src/",
        "web/",
        "tests/",
        "docs/",
        ".github/workflows/",
    ]
    modules = meta.get("modules") or list(architecture.get("service_boundaries") or [])
    return {
        "blueprint_id": "repository-blueprint",
        "repository_structure": folders,
        "modules": modules,
        "projects": meta.get("projects") or ["monorepo-root"],
        "service_boundaries": architecture.get("service_boundaries"),
        "branch_strategy": meta.get("branch_strategy") or "main + feature branches + governed PR flow",
        "operator_notes": explicit[:500] if explicit else None,
        "present": bool(explicit or architecture.get("present")),
        "read_only": True,
    }


def _delivery_backlog(*, session_id: str, product: dict[str, Any]) -> dict[str, Any]:
    explicit = _record_content(session_id=session_id, kind="delivery_backlog_note")
    meta = _record_meta(session_id=session_id, kind="delivery_backlog_note")
    epics = meta.get("epics") or [
        f"{product.get('product_name')} foundation",
        "Core API and data model",
        "Web application shell",
        "Verification and delivery integration",
    ]
    return {
        "backlog_id": "delivery-backlog",
        "epics": epics,
        "features": meta.get("features") or ["auth", "core-domain", "operator-dashboard"],
        "stories": meta.get("stories") or ["scaffold repository", "implement API skeleton", "add verification gate"],
        "tasks": meta.get("tasks") or ["create plan", "bounded patch", "workspace verification"],
        "dependencies": meta.get("dependencies") or ["architecture-package", "repository-blueprint"],
        "risk_areas": meta.get("risk_areas") or ["scope creep", "unbounded autonomy", "missing verification"],
        "operator_notes": explicit[:500] if explicit else None,
        "present": bool(explicit or product.get("present")),
        "read_only": True,
    }


def _repository_creation_plan(
    *,
    session_id: str,
    product: dict[str, Any],
    architecture: dict[str, Any],
    blueprint: dict[str, Any],
    backlog: dict[str, Any],
) -> dict[str, Any]:
    product_slug = str(product.get("product_name") or "product").lower().replace(" ", "-")[:48]
    return {
        "plan_id": f"repo-creation-plan-{session_id}",
        "repository_creation_proposal": {
            "proposed_name": f"pilotmain/{product_slug}",
            "creation_executable": False,
            "requires_human_approval": True,
        },
        "initial_structure_proposal": blueprint.get("repository_structure"),
        "branch_strategy": blueprint.get("branch_strategy"),
        "delivery_roadmap_preview": (backlog.get("epics") or [])[:4],
        "architecture_linkage": architecture.get("package_id"),
        "planning_only": True,
        "repository_creation_authority": False,
        "present": bool(product.get("present") and blueprint.get("present")),
        "read_only": True,
    }


def _bounded_agent_synthesis(*, session_id: str, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for role in BOUNDED_GENERATION_AGENT_ROLES:
        agent_records = [
            r
            for r in records
            if str((r.get("metadata") or {}).get("agent_role") or "") == role
            or str(r.get("kind") or "") == "agent_synthesis_note"
            and str((r.get("metadata") or {}).get("agent_role") or "") == role
        ]
        latest = agent_records[-1] if agent_records else None
        rows.append(
            {
                "agent_role": role,
                "bounded": True,
                "governed": True,
                "synthesis_record_id": (latest or {}).get("record_id"),
                "present": bool(latest),
                "read_only": True,
            }
        )
    return rows


def _generation_readiness_report(
    *,
    evidence: dict[str, Any],
    human_decision: str | None,
    product: dict[str, Any],
) -> dict[str, Any]:
    blockers = list(evidence.get("missing_evidence") or [])
    if human_decision != "approve":
        blockers.append("human_generation_approval_pending")
    score = 100 - len(blockers) * 12
    score = max(0, min(100, score))
    return {
        "report_id": "generation-readiness",
        "readiness_score": score,
        "product_name": product.get("product_name"),
        "evidence_complete": evidence.get("evidence_complete_for_handoff"),
        "outstanding_blockers": blockers,
        "required_evidence": evidence,
        "ready_for_delivery_pipeline_handoff": evidence.get("evidence_complete_for_handoff")
        and human_decision == "approve",
        "advisory_only": True,
        "read_only": True,
    }


def _required_evidence(
    *,
    product: dict[str, Any],
    architecture: dict[str, Any],
    blueprint: dict[str, Any],
    backlog: dict[str, Any],
    human_decision: str | None,
) -> dict[str, Any]:
    items = {
        "prd_reference": {
            "present": bool(product.get("present")),
            "product_name": product.get("product_name"),
        },
        "product_understanding": {"present": bool(product.get("present"))},
        "architecture_package": {"present": bool(architecture.get("present"))},
        "repository_blueprint": {"present": bool(blueprint.get("present"))},
        "delivery_backlog": {"present": bool(backlog.get("present"))},
        "human_generation_decision": {
            "present": human_decision is not None,
            "decision": human_decision,
        },
    }
    missing_all = [key for key in REQUIRED_GENERATION_EVIDENCE_IDS if not items[key]["present"]]
    missing_for_handoff = [
        key for key in missing_all if key != "human_generation_decision"
    ]
    return {
        "evidence_id": "required-generation-evidence",
        "items": items,
        "missing_evidence": missing_all,
        "missing_evidence_for_handoff": missing_for_handoff,
        "evidence_complete_for_recommendation": len(missing_for_handoff) == 0,
        "evidence_complete_for_handoff": len(missing_all) == 0 and human_decision == "approve",
        "read_only": True,
    }


def _delivery_pipeline_handoff_artifact(
    *,
    session_id: str,
    readiness: dict[str, Any],
    product: dict[str, Any],
    backlog: dict[str, Any],
    creation_plan: dict[str, Any],
    human_decision: str | None,
    plan_id: str | None,
) -> dict[str, Any] | None:
    if human_decision != "approve":
        return None
    if not readiness.get("ready_for_delivery_pipeline_handoff"):
        return None

    return {
        "handoff_id": f"delivery-pipeline-handoff-{session_id}",
        "session_id": session_id,
        "product_name": product.get("product_name"),
        "existing_pipeline_entry": "software_delivery_issue_plan",
        "linked_plan_id": plan_id,
        "first_backlog_epic": (backlog.get("epics") or [None])[0],
        "repository_creation_plan": creation_plan,
        "audit_linkage": {
            "timeline_ref": timeline_link_ref(
                lane="governed_application_generation",
                action="delivery_pipeline_handoff",
                timestamp=session_id,
            ),
            "replay_key": replay_link_key(
                source="governed_application_generation",
                lane="delivery_pipeline_handoff",
                action=session_id,
            ),
        },
        "handoff_executable": False,
        "feeds_existing_pipeline_only": True,
        "detail": "Delivery pipeline handoff — use existing Plan → Patch → Verify → PR path; no separate execution.",
        "read_only": True,
    }


def _generation_memory(*, records: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind: dict[str, int] = {}
    for record in records:
        kind = str(record.get("kind") or "unknown")
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        "memory_id": "generation-memory",
        "record_count": len(records),
        "records_by_kind": by_kind,
        "persists_prds_architecture_blueprints_backlogs_and_decisions": True,
        "read_only": True,
    }


def build_governed_application_generation(*, session_id: str) -> GovernedApplicationGenerationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "") or None
    human_decision = generation_decision_status(session_id=sid)
    records = list_governed_application_generation_records(session_id=sid)

    blockers: list[str] = []
    if not _record_content(session_id=sid, kind="prd_intake_note"):
        blockers.append("no_prd_intake_for_session")

    product = _product_understanding_package(session_id=sid, records=records)
    architecture = _architecture_package(session_id=sid, product=product)
    blueprint = _repository_blueprint(session_id=sid, architecture=architecture)
    backlog = _delivery_backlog(session_id=sid, product=product)
    creation_plan = _repository_creation_plan(
        session_id=sid,
        product=product,
        architecture=architecture,
        blueprint=blueprint,
        backlog=backlog,
    )
    evidence = _required_evidence(
        product=product,
        architecture=architecture,
        blueprint=blueprint,
        backlog=backlog,
        human_decision=human_decision,
    )
    readiness = _generation_readiness_report(
        evidence=evidence, human_decision=human_decision, product=product
    )
    handoff = _delivery_pipeline_handoff_artifact(
        session_id=sid,
        readiness=readiness,
        product=product,
        backlog=backlog,
        creation_plan=creation_plan,
        human_decision=human_decision,
        plan_id=plan_id,
    )
    agents = _bounded_agent_synthesis(session_id=sid, records=records)
    memory = _generation_memory(records=records)

    current_stage = "product_understanding"
    if handoff:
        current_stage = "existing_delivery_pipeline"
    elif human_decision:
        current_stage = "governed_repository_creation_plan"
    elif blueprint.get("present") and backlog.get("present"):
        current_stage = "delivery_backlog_generation"
    elif architecture.get("present"):
        current_stage = "architecture_generation"

    sections = {
        "product_understanding_package": [product],
        "architecture_package": [architecture],
        "repository_blueprint": [blueprint],
        "delivery_backlog": [backlog],
        "repository_creation_plan": [creation_plan],
        "generation_readiness_report": [readiness],
        "delivery_pipeline_handoff": [handoff] if handoff else [],
        "bounded_generation_agents": agents,
        "generation_memory": [memory],
        "human_generation_decisions": [
            {**r, "read_only": True}
            for r in records
            if str(r.get("kind") or "") in GENERATION_DECISION_KINDS
        ],
        "existing_delivery_pipeline_linkage": [
            {
                "pipeline_id": "software_delivery_issue_plan",
                "linked_plan_id": plan_id,
                "entry_intent": "issue → plan → patch → verify → PR → merge → deploy",
                "separate_execution_path": False,
                "read_only": True,
            }
        ],
        "forbidden_application_generation_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_APPLICATION_GENERATION_ACTIONS
        ],
        "operator_generation_records": [{**r, "read_only": True} for r in records],
    }

    payload: dict[str, Any] = {
        "schema_version": GOVERNED_APPLICATION_GENERATION_SCHEMA_VERSION,
        "fix": GOVERNED_APPLICATION_GENERATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_250,
        "execution_performed": EXECUTION_PERFORMED_FIX_250,
        "generation_compose_evidence_only": GOVERNED_APPLICATION_GENERATION_COMPOSES_EVIDENCE_ONLY_FIX_250,
        "application_generation_authority": APPLICATION_GENERATION_AUTHORITY_FIX_250,
        "repository_creation_authority": REPOSITORY_CREATION_AUTHORITY_FIX_250,
        "github_mutation_authority": GITHUB_MUTATION_AUTHORITY_FIX_250,
        "provider_authority": PROVIDER_AUTHORITY_FIX_250,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_250,
        "code_generation_authority": CODE_GENERATION_AUTHORITY_FIX_250,
        "merge_authority": MERGE_AUTHORITY_FIX_250,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_250,
        "infrastructure_mutation_authority": INFRASTRUCTURE_MUTATION_AUTHORITY_FIX_250,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_250,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_250,
        "invariant": GOVERNED_APPLICATION_GENERATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "product_name": product.get("product_name"),
        "lifecycle_stages": list(GENERATION_PIPELINE_STAGES),
        "current_stage": current_stage,
        "human_generation_decision": human_decision,
        "sections": sections,
        "generation_record_count": len(records),
        "fix_250_certification_requirements": list(FIX_250_CERTIFICATION_REQUIREMENTS),
        "governed_application_generation_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GOVERNED_APPLICATION_GENERATION_PRINCIPLES
        ],
        "sources": {
            "composes_prd_and_generation_memory": True,
            "links_existing_software_delivery_pipeline": True,
            "repository_creation_performed": False,
            "code_generation_performed": False,
        },
    }

    return GovernedApplicationGenerationResult(
        ok=True,
        session_id=sid,
        governed_application_generation=payload,
        blockers=blockers,
        detail="Governed application generation assembled (application_generation ≠ autonomous_authority).",
    )


def prepare_governed_application_generation_handoff(
    *, session_id: str
) -> GovernedApplicationGenerationHandoffResult:
    lifecycle = build_governed_application_generation(session_id=session_id)
    board = lifecycle.governed_application_generation
    handoff_rows = (board.get("sections") or {}).get("delivery_pipeline_handoff") or []
    blockers: list[str] = list(lifecycle.blockers)

    if not handoff_rows:
        blockers.append("delivery_pipeline_handoff_not_ready")
        if board.get("human_generation_decision") != "approve":
            blockers.append("human_generation_approval_required")
        readiness = ((board.get("sections") or {}).get("generation_readiness_report") or [{}])[0]
        if not readiness.get("ready_for_delivery_pipeline_handoff"):
            blockers.append("generation_evidence_incomplete")
        return GovernedApplicationGenerationHandoffResult(
            ok=False,
            session_id=lifecycle.session_id,
            blockers=blockers,
            detail="Delivery pipeline handoff blocked — PRD packages, evidence, and human approval required.",
        )

    handoff = dict(handoff_rows[0])
    handoff["schema_version"] = GOVERNED_APPLICATION_GENERATION_HANDOFF_SCHEMA_VERSION
    handoff["executable"] = GOVERNED_APPLICATION_GENERATION_HANDOFF_EXECUTABLE
    handoff["application_generation_authority"] = APPLICATION_GENERATION_AUTHORITY_FIX_250
    handoff["repository_creation_authority"] = REPOSITORY_CREATION_AUTHORITY_FIX_250

    return GovernedApplicationGenerationHandoffResult(
        ok=True,
        session_id=lifecycle.session_id,
        delivery_pipeline_handoff=handoff,
        detail="Delivery pipeline handoff prepared — feed existing Plan → Patch → Verify → PR pipeline.",
    )
