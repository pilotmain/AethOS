# SPDX-License-Identifier: Apache-2.0
"""FIX 240 — repository knowledge graph service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_240_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_store import (
    deploy_target_environment,
    list_governed_deploy_lifecycle_records,
)
from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_store import (
    list_governed_monitoring_lifecycle_records,
    operational_decision_status,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    PHASE_1_REPOSITORY,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_contract import (
    ARCHITECTURE_NODE_KINDS,
    CODE_MODIFICATION_AUTHORITY_FIX_240,
    CROSS_REPO_AUTHORITY_FIX_240,
    DEFAULT_ARCHITECTURE_BY_REPOSITORY,
    DEFAULT_DEPENDENCIES_BY_REPOSITORY,
    DEFAULT_OWNERSHIP_BY_REPOSITORY,
    DEPLOY_AUTHORITY_FIX_240,
    EXECUTION_PERFORMED_FIX_240,
    FORBIDDEN_KNOWLEDGE_GRAPH_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_240,
    GOVERNANCE_MUTATION_PERFORMED_FIX_240,
    KNOWLEDGE_GRAPH_EXECUTION_FIX_240,
    MERGE_AUTHORITY_FIX_240,
    MUTATION_PERFORMED_FIX_240,
    PHASE_1_KNOWLEDGE_REPOSITORIES,
    REPOSITORY_AUTHORITY_FIX_240,
    REPOSITORY_DISPLAY_NAMES,
    REPOSITORY_KNOWLEDGE_GRAPH_COMPOSES_EVIDENCE_ONLY_FIX_240,
    REPOSITORY_KNOWLEDGE_GRAPH_FIX,
    REPOSITORY_KNOWLEDGE_GRAPH_INVARIANT,
    REPOSITORY_KNOWLEDGE_GRAPH_PRINCIPLES,
    REPOSITORY_KNOWLEDGE_GRAPH_SCHEMA_VERSION,
    REQUIRED_INTELLIGENCE_EVIDENCE_IDS,
    ROLLBACK_AUTHORITY_FIX_240,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_store import (
    list_repository_knowledge_graph_records,
)
from aethos_core.software_delivery.github_pr_open_store import load_github_pr_open_for_plan
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
from aethos_core.software_delivery.workspace_verification_store import workspace_verification_passed


@dataclass(frozen=True)
class RepositoryKnowledgeGraphResult:
    ok: bool
    session_id: str
    repository_knowledge_graph: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _resolve_repository_id(*, plan: dict[str, Any] | None, pr_open: dict[str, Any] | None) -> str:
    repo = str((pr_open or {}).get("repository") or "")
    if repo in PHASE_1_KNOWLEDGE_REPOSITORIES:
        return repo
    issue_ref = str((plan or {}).get("issue_reference") or "")
    for registry_repo in PHASE_1_KNOWLEDGE_REPOSITORIES:
        if registry_repo.lower() in issue_ref.lower():
            return registry_repo
    return PHASE_1_REPOSITORY


def _path_subsystem(path: str) -> str:
    normalized = (path or "").strip().replace("\\", "/")
    if normalized.startswith("web/"):
        return "web-app"
    if normalized.startswith("aethos_core/mission_control/"):
        return "mission-control"
    if normalized.startswith("aethos_core/software_delivery/"):
        return "software-delivery"
    if normalized.startswith("aethos_core/"):
        return "aethos-core"
    if normalized.startswith("tests/"):
        return "tests"
    if normalized.startswith("docs/"):
        return "docs"
    parts = normalized.split("/")
    return parts[0] if parts and parts[0] else "unknown"


def _architecture_graph(
    *,
    repository_id: str,
    affected_files: list[str],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    nodes = [
        {
            "node_id": node_id,
            "kind": kind,
            "path": path,
            "repository_id": repository_id,
            "read_only": True,
        }
        for node_id, kind, path in DEFAULT_ARCHITECTURE_BY_REPOSITORY.get(repository_id, ())
    ]
    for record in records:
        if str(record.get("kind") or "") != "architecture_discovery_note":
            continue
        meta = dict(record.get("metadata") or {})
        node_id = str(meta.get("node_id") or f"discovered-{record.get('record_id')}")
        nodes.append(
            {
                "node_id": node_id,
                "kind": str(meta.get("kind") or "module"),
                "path": meta.get("path"),
                "source": "operator_discovery",
                "read_only": True,
            }
        )

    active_nodes = {_path_subsystem(f) for f in affected_files if f}
    edges = [
        {
            "edge_id": f"{src}->{dst}",
            "source": src,
            "target": dst,
            "relationship": "contains",
            "read_only": True,
        }
        for src, dst in (
            ("aethos-core", "mission-control"),
            ("aethos-core", "software-delivery"),
            ("web-app", "aethos-core"),
        )
        if repository_id == PHASE_1_REPOSITORY
    ]

    return {
        "graph_id": f"architecture-{repository_id}",
        "repository_id": repository_id,
        "nodes": nodes,
        "edges": edges,
        "active_subsystems": sorted(active_nodes),
        "valid_node_kinds": list(ARCHITECTURE_NODE_KINDS),
        "present": bool(nodes),
        "read_only": True,
    }


def _dependency_registry(
    *,
    repository_id: str,
    records: list[dict[str, Any]],
    affected_files: list[str],
) -> dict[str, Any]:
    dependencies = [
        {
            "dependency_id": f"{src}->{dst}",
            "source": src,
            "target": dst,
            "dependency_type": dep_type,
            "read_only": True,
        }
        for src, dst, dep_type in DEFAULT_DEPENDENCIES_BY_REPOSITORY.get(repository_id, ())
    ]
    external: list[dict[str, Any]] = []
    for record in records:
        if str(record.get("kind") or "") != "dependency_mapping_note":
            continue
        meta = dict(record.get("metadata") or {})
        dependencies.append(
            {
                "dependency_id": str(meta.get("dependency_id") or record.get("record_id")),
                "source": meta.get("source"),
                "target": meta.get("target"),
                "dependency_type": meta.get("dependency_type") or "internal",
                "source_record_id": record.get("record_id"),
                "read_only": True,
            }
        )
        if str(meta.get("dependency_type") or "").lower() == "external":
            external.append(
                {
                    "package": meta.get("target"),
                    "source_subsystem": meta.get("source"),
                    "read_only": True,
                }
            )

    touched = {_path_subsystem(f) for f in affected_files if f}
    critical_paths = [
        dep
        for dep in dependencies
        if dep.get("source") in touched or dep.get("target") in touched
    ]

    return {
        "registry_id": f"dependencies-{repository_id}",
        "repository_id": repository_id,
        "dependencies": dependencies,
        "external_dependencies": external,
        "critical_paths": critical_paths,
        "shared_components": [
            dep for dep in dependencies if dep.get("dependency_type") == "internal"
        ],
        "present": bool(dependencies),
        "read_only": True,
    }


def _dependency_risk_report(*, registry: dict[str, Any], plan_risk: dict[str, Any]) -> dict[str, Any]:
    critical_count = len(registry.get("critical_paths") or [])
    external_count = len(registry.get("external_dependencies") or [])
    tier = str(plan_risk.get("risk_tier") or "medium")
    score = 20
    score += critical_count * 15
    score += external_count * 10
    if tier == "high":
        score += 20
    elif tier == "critical":
        score += 35
    score = max(0, min(100, score))
    return {
        "report_id": "dependency-risk",
        "risk_score": score,
        "critical_path_count": critical_count,
        "external_dependency_count": external_count,
        "advisory_only": True,
        "read_only": True,
    }


def _ownership_registry(*, repository_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    owners = [
        {
            "ownership_id": f"{subsystem}:{team}",
            "subsystem": subsystem,
            "team": team,
            "role": role,
            "read_only": True,
        }
        for subsystem, team, role in DEFAULT_OWNERSHIP_BY_REPOSITORY.get(repository_id, ())
    ]
    for record in records:
        if str(record.get("kind") or "") != "ownership_record_note":
            continue
        meta = dict(record.get("metadata") or {})
        owners.append(
            {
                "ownership_id": str(meta.get("ownership_id") or record.get("record_id")),
                "subsystem": meta.get("subsystem"),
                "team": meta.get("team") or meta.get("maintainer"),
                "role": meta.get("role") or "maintainer",
                "source_record_id": record.get("record_id"),
                "read_only": True,
            }
        )
    return {
        "registry_id": f"ownership-{repository_id}",
        "repository_id": repository_id,
        "owners": owners,
        "present": bool(owners),
        "read_only": True,
    }


def _ownership_confidence(*, registry: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    operator_notes = [
        r for r in records if str(r.get("kind") or "") == "ownership_record_note"
    ]
    base = 55
    base += min(30, len(registry.get("owners") or []) * 5)
    base += min(15, len(operator_notes) * 5)
    score = max(0, min(100, base))
    return {
        "score_id": "ownership-confidence",
        "confidence_score": score,
        "operator_record_count": len(operator_notes),
        "advisory_only": True,
        "read_only": True,
    }


def _historical_change_report(
    *,
    session_id: str,
    plan_id: str,
    affected_files: list[str],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    deploy_records = list_governed_deploy_lifecycle_records(session_id=session_id, plan_id=plan_id)
    monitoring_records = list_governed_monitoring_lifecycle_records(session_id=session_id, plan_id=plan_id)
    failures = [
        r
        for r in deploy_records + monitoring_records
        if str((r.get("metadata") or {}).get("workflow_status") or "").lower() in {"failure", "failed"}
    ]
    pattern_notes = [r for r in records if str(r.get("kind") or "") == "historical_pattern_note"]
    return {
        "report_id": f"historical-change-{plan_id}",
        "frequently_changed_files": affected_files,
        "stable_files": [f for f in affected_files if f.startswith("docs/")],
        "deployment_history_count": len(deploy_records),
        "failure_events": len(failures),
        "operator_pattern_notes": len(pattern_notes),
        "present": bool(affected_files or deploy_records or pattern_notes),
        "read_only": True,
    }


def _hotspot_map(*, affected_files: list[str], historical: dict[str, Any]) -> dict[str, Any]:
    hotspots = []
    for path in affected_files:
        subsystem = _path_subsystem(path)
        severity = "high" if subsystem in {"mission-control", "software-delivery"} else "medium"
        if historical.get("failure_events"):
            severity = "critical" if subsystem == "mission-control" else severity
        hotspots.append(
            {
                "path": path,
                "subsystem": subsystem,
                "hotspot_severity": severity,
                "read_only": True,
            }
        )
    return {
        "map_id": "repository-hotspots",
        "hotspots": hotspots,
        "failure_prone_areas": [h for h in hotspots if h.get("hotspot_severity") in {"high", "critical"}],
        "read_only": True,
    }


def _repository_risk_profile(
    *,
    plan_risk: dict[str, Any],
    historical: dict[str, Any],
    dependency_risk: dict[str, Any],
    monitoring_classification: str | None,
) -> dict[str, Any]:
    complexity = min(100, 20 + len(historical.get("frequently_changed_files") or []) * 8)
    coupling = min(100, dependency_risk.get("critical_path_count", 0) * 18)
    operational = 15
    if monitoring_classification in {"INCIDENT", "DEGRADED"}:
        operational = 75
    elif monitoring_classification == "WARNING":
        operational = 45
    failure_history = min(100, (historical.get("failure_events") or 0) * 25)
    overall = int((complexity + coupling + operational + failure_history) / 4)
    return {
        "profile_id": "repository-risk",
        "overall_risk_score": overall,
        "complexity": complexity,
        "coupling": coupling,
        "operational_sensitivity": operational,
        "failure_history": failure_history,
        "risk_tier": plan_risk.get("risk_tier"),
        "advisory_only": True,
        "read_only": True,
    }


def _subsystem_risk_profiles(*, hotspots: dict[str, Any], ownership: dict[str, Any]) -> list[dict[str, Any]]:
    owner_by_subsystem = {
        str(o.get("subsystem") or ""): o for o in (ownership.get("owners") or [])
    }
    profiles: list[dict[str, Any]] = []
    seen: set[str] = set()
    for hotspot in hotspots.get("hotspots") or []:
        subsystem = str(hotspot.get("subsystem") or "")
        if not subsystem or subsystem in seen:
            continue
        seen.add(subsystem)
        severity = str(hotspot.get("hotspot_severity") or "medium")
        score = {"low": 20, "medium": 45, "high": 70, "critical": 90}.get(severity, 45)
        profiles.append(
            {
                "subsystem": subsystem,
                "risk_score": score,
                "owner": (owner_by_subsystem.get(subsystem) or {}).get("team"),
                "read_only": True,
            }
        )
    return profiles


def _change_impact_assessment(
    *,
    plan: dict[str, Any] | None,
    affected_files: list[str],
    architecture: dict[str, Any],
    dependencies: dict[str, Any],
    ownership: dict[str, Any],
    plan_risk: dict[str, Any],
    deploy_env: str | None,
    monitoring_classification: str | None,
) -> dict[str, Any]:
    subsystems = sorted({_path_subsystem(f) for f in affected_files if f})
    impacted_deps = dependencies.get("critical_paths") or []
    owners = ownership.get("owners") or []
    likely_reviewers = sorted(
        {
            str(o.get("team"))
            for o in owners
            if str(o.get("subsystem") or "") in subsystems and o.get("team")
        }
    )
    deployment_impact = "none"
    if deploy_env:
        deployment_impact = f"{deploy_env}_redeploy_review"
    if monitoring_classification in {"INCIDENT", "DEGRADED"}:
        deployment_impact = f"{deploy_env or 'unknown'}_operational_review_required"

    return {
        "assessment_id": "change-impact",
        "issue_reference": (plan or {}).get("issue_reference"),
        "affected_systems": subsystems,
        "active_architecture_nodes": architecture.get("active_subsystems"),
        "dependency_impact": impacted_deps,
        "blast_radius": plan_risk.get("blast_radius"),
        "likely_reviewers": likely_reviewers,
        "likely_deployment_impact": deployment_impact,
        "advisory_only": True,
        "read_only": True,
    }


def _required_evidence(
    *,
    repository_id: str,
    architecture: dict[str, Any],
    dependencies: dict[str, Any],
    ownership: dict[str, Any],
    historical: dict[str, Any],
    risk_profile: dict[str, Any],
) -> dict[str, Any]:
    items = {
        "repository_reference": {"present": bool(repository_id), "repository_id": repository_id},
        "architecture_graph": {"present": bool(architecture.get("present")), "node_count": len(architecture.get("nodes") or [])},
        "dependency_registry": {
            "present": bool(dependencies.get("present")),
            "dependency_count": len(dependencies.get("dependencies") or []),
        },
        "ownership_registry": {
            "present": bool(ownership.get("present")),
            "owner_count": len(ownership.get("owners") or []),
        },
        "historical_change_signals": {
            "present": bool(historical.get("present")),
            "deployment_history_count": historical.get("deployment_history_count"),
        },
        "risk_profile": {
            "present": bool(risk_profile.get("overall_risk_score") is not None),
            "overall_risk_score": risk_profile.get("overall_risk_score"),
        },
    }
    missing = [key for key in REQUIRED_INTELLIGENCE_EVIDENCE_IDS if not items[key]["present"]]
    return {
        "evidence_id": "required-intelligence-evidence",
        "items": items,
        "missing_evidence": missing,
        "evidence_complete": len(missing) == 0,
        "read_only": True,
    }


def _cross_repository_knowledge(*, primary_repository_id: str) -> dict[str, Any]:
    links = []
    for repo in PHASE_1_KNOWLEDGE_REPOSITORIES:
        if repo == primary_repository_id:
            continue
        links.append(
            {
                "link_id": f"{primary_repository_id}->{repo}",
                "source_repository": primary_repository_id,
                "target_repository": repo,
                "target_display_name": REPOSITORY_DISPLAY_NAMES.get(repo, repo),
                "relationship": "advisory_cross_repo_reference",
                "cross_repo_authority": False,
                "read_only": True,
            }
        )
    return {
        "cross_repo_id": "phase-1-knowledge-repositories",
        "primary_repository": primary_repository_id,
        "repositories": [
            {
                "repository_id": repo,
                "display_name": REPOSITORY_DISPLAY_NAMES.get(repo, repo),
                "phase_1": True,
                "read_only": True,
            }
            for repo in PHASE_1_KNOWLEDGE_REPOSITORIES
        ],
        "advisory_links": links,
        "cross_repo_authority": False,
        "read_only": True,
    }


def _repository_memory(*, records: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind: dict[str, int] = {}
    for record in records:
        kind = str(record.get("kind") or "unknown")
        by_kind[kind] = by_kind.get(kind, 0) + 1
    return {
        "memory_id": "repository-memory",
        "record_count": len(records),
        "records_by_kind": by_kind,
        "reusable_for_future_issues": True,
        "read_only": True,
    }


def _engineering_intelligence_dashboard(
    *,
    repository_id: str,
    architecture: dict[str, Any],
    dependency_risk: dict[str, Any],
    ownership_confidence: dict[str, Any],
    risk_profile: dict[str, Any],
    change_impact: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "dashboard_id": "engineering-intelligence",
        "repository_id": repository_id,
        "display_name": REPOSITORY_DISPLAY_NAMES.get(repository_id, repository_id),
        "architecture_node_count": len(architecture.get("nodes") or []),
        "dependency_risk_score": dependency_risk.get("risk_score"),
        "ownership_confidence_score": ownership_confidence.get("confidence_score"),
        "repository_risk_score": risk_profile.get("overall_risk_score"),
        "change_impact_systems": change_impact.get("affected_systems"),
        "evidence_complete": evidence.get("evidence_complete"),
        "advisory_only": True,
        "read_only": True,
    }


def _monitoring_classification(*, session_id: str, plan_id: str) -> str | None:
    records = list_governed_monitoring_lifecycle_records(session_id=session_id, plan_id=plan_id)
    workflow_records = [
        r
        for r in records
        if str(r.get("kind") or "") in {"workflow_result_note", "monitoring_observation"}
    ]
    deploy_records = list_governed_deploy_lifecycle_records(session_id=session_id, plan_id=plan_id)
    workflow_records.extend(
        r
        for r in deploy_records
        if str(r.get("kind") or "") in {"deploy_execution_request_note", "deploy_handoff_note"}
    )
    if not workflow_records:
        return None
    latest = workflow_records[-1]
    status = str((latest.get("metadata") or {}).get("workflow_status") or "").lower()
    if status == "success":
        return "HEALTHY"
    if status in {"failure", "failed", "error"}:
        return "INCIDENT"
    if status in {"degraded", "cancelled", "timeout"}:
        return "DEGRADED"
    return "WARNING"


def build_repository_knowledge_graph(*, session_id: str) -> RepositoryKnowledgeGraphResult:
    sid = (session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "")
    pr_open = load_github_pr_open_for_plan(plan_id=plan_id) if plan_id else None
    repository_id = _resolve_repository_id(plan=plan, pr_open=pr_open)
    affected_files = list((plan or {}).get("affected_files") or [])
    plan_risk = dict((plan or {}).get("risk_assessment") or {})
    records = list_repository_knowledge_graph_records(session_id=sid, repository_id=repository_id)
    deploy_env = deploy_target_environment(session_id=sid, plan_id=plan_id) if plan_id else None
    monitoring_classification = _monitoring_classification(session_id=sid, plan_id=plan_id) if plan_id else None

    blockers: list[str] = []
    if not plan:
        blockers.append("no_issue_plan_for_session")

    architecture = _architecture_graph(
        repository_id=repository_id,
        affected_files=affected_files,
        records=records,
    )
    dependencies = _dependency_registry(
        repository_id=repository_id,
        records=records,
        affected_files=affected_files,
    )
    dependency_risk = _dependency_risk_report(registry=dependencies, plan_risk=plan_risk)
    ownership = _ownership_registry(repository_id=repository_id, records=records)
    ownership_confidence = _ownership_confidence(registry=ownership, records=records)
    historical = _historical_change_report(
        session_id=sid,
        plan_id=plan_id,
        affected_files=affected_files,
        records=records,
    ) if plan_id else {"present": False}
    hotspots = _hotspot_map(affected_files=affected_files, historical=historical)
    risk_profile = _repository_risk_profile(
        plan_risk=plan_risk,
        historical=historical,
        dependency_risk=dependency_risk,
        monitoring_classification=monitoring_classification,
    )
    subsystem_risks = _subsystem_risk_profiles(hotspots=hotspots, ownership=ownership)
    change_impact = _change_impact_assessment(
        plan=plan,
        affected_files=affected_files,
        architecture=architecture,
        dependencies=dependencies,
        ownership=ownership,
        plan_risk=plan_risk,
        deploy_env=deploy_env,
        monitoring_classification=monitoring_classification,
    )
    evidence = _required_evidence(
        repository_id=repository_id,
        architecture=architecture,
        dependencies=dependencies,
        ownership=ownership,
        historical=historical,
        risk_profile=risk_profile,
    )
    cross_repo = _cross_repository_knowledge(primary_repository_id=repository_id)
    memory = _repository_memory(records=records)
    dashboard = _engineering_intelligence_dashboard(
        repository_id=repository_id,
        architecture=architecture,
        dependency_risk=dependency_risk,
        ownership_confidence=ownership_confidence,
        risk_profile=risk_profile,
        change_impact=change_impact,
        evidence=evidence,
    )

    sections = {
        "architecture_graph": [architecture],
        "dependency_registry": [dependencies],
        "dependency_risk_report": [dependency_risk],
        "ownership_registry": [ownership],
        "ownership_confidence": [ownership_confidence],
        "historical_change_report": [historical],
        "repository_hotspot_map": [hotspots],
        "change_impact_assessment": [change_impact],
        "repository_risk_profile": [risk_profile],
        "subsystem_risk_profiles": subsystem_risks,
        "engineering_intelligence_dashboard": [dashboard],
        "cross_repository_knowledge": [cross_repo],
        "repository_memory": [memory],
        "forbidden_knowledge_graph_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_KNOWLEDGE_GRAPH_ACTIONS
        ],
        "operator_intelligence_records": [{**r, "read_only": True} for r in records],
    }

    payload: dict[str, Any] = {
        "schema_version": REPOSITORY_KNOWLEDGE_GRAPH_SCHEMA_VERSION,
        "fix": REPOSITORY_KNOWLEDGE_GRAPH_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_240,
        "execution_performed": EXECUTION_PERFORMED_FIX_240,
        "repository_compose_evidence_only": REPOSITORY_KNOWLEDGE_GRAPH_COMPOSES_EVIDENCE_ONLY_FIX_240,
        "repository_authority": REPOSITORY_AUTHORITY_FIX_240,
        "code_modification_authority": CODE_MODIFICATION_AUTHORITY_FIX_240,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_240,
        "knowledge_graph_execution": KNOWLEDGE_GRAPH_EXECUTION_FIX_240,
        "merge_authority": MERGE_AUTHORITY_FIX_240,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_240,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_240,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_240,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_240,
        "invariant": REPOSITORY_KNOWLEDGE_GRAPH_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id or None,
        "repository_id": repository_id,
        "repository_display_name": REPOSITORY_DISPLAY_NAMES.get(repository_id, repository_id),
        "human_operational_decision": operational_decision_status(session_id=sid, plan_id=plan_id or None),
        "verification_passed": workspace_verification_passed(plan_id=plan_id) if plan_id else False,
        "sections": sections,
        "intelligence_record_count": len(records),
        "fix_240_certification_requirements": list(FIX_240_CERTIFICATION_REQUIREMENTS),
        "repository_knowledge_graph_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in REPOSITORY_KNOWLEDGE_GRAPH_PRINCIPLES
        ],
        "sources": {
            "composes_issue_plan_and_verification": True,
            "composes_lifecycle_deploy_monitoring_evidence": True,
            "phase_1_repositories": list(PHASE_1_KNOWLEDGE_REPOSITORIES),
            "code_modification_performed": False,
        },
    }

    return RepositoryKnowledgeGraphResult(
        ok=True,
        session_id=sid,
        repository_knowledge_graph=payload,
        blockers=blockers,
        detail="Repository knowledge graph assembled (repository_intelligence ≠ repository_authority).",
    )
