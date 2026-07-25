# SPDX-License-Identifier: Apache-2.0
"""FIX 355 / WORKSTREAM_G2 — real usage density & platform adoption executor."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_contract import (
    USAGE_MATURITY_LEVELS,
    USAGE_SURFACES,
)
from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_store import (
    list_usage_session_registry_entries,
    register_usage_session_entry,
)

_USAGE_SOURCE_CATALOG: tuple[tuple[str, str, str, str], ...] = (
    (
        "f1_pilot_runs",
        "aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store",
        "list_customer_pilot_run_registry_entries",
        "et_pipeline",
    ),
    (
        "f2_usage_observations",
        "aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store",
        "list_usage_observation_registry_entries",
        "mission_control",
    ),
    (
        "f2_customer_records",
        "aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store",
        "list_customer_value_adoption_validation_records",
        "mission_control",
    ),
    (
        "g1_evidence_maturity",
        "aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_store",
        "list_evidence_maturity_records",
        "dashboard",
    ),
    (
        "et_workspace",
        "aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store",
        "list_governed_workspace_creation_records",
        "et_pipeline",
    ),
    (
        "et_deployment",
        "aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store",
        "list_governed_deployment_execution_records",
        "provider",
    ),
    (
        "governance_records",
        "aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store",
        "list_governed_end_to_end_delivery_certification_records",
        "governance",
    ),
)


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _parse_timestamp(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        normalized = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _load_source_rows(module_path: str, list_fn: str) -> list[dict[str, Any]]:
    try:
        mod = __import__(module_path, fromlist=[list_fn])
        rows = getattr(mod, list_fn)()
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    except Exception:
        return []
    return []


def _registered_sessions(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_usage_session_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _collect_usage_events() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for source_id, module_path, list_fn, surface in _USAGE_SOURCE_CATALOG:
        for row in _load_source_rows(module_path, list_fn):
            session_id = str(row.get("session_id") or row.get("program_session_id") or "unknown")
            timestamp = (
                _parse_timestamp(row.get("recorded_at"))
                or _parse_timestamp(row.get("registered_at"))
                or _parse_timestamp(row.get("created_at"))
            )
            workflow = str(row.get("workflow") or row.get("kind") or row.get("request_type") or source_id)
            executions = int(row.get("executions") or 1)
            repeat = executions > 1 or str(row.get("trend") or "").lower() == "continued"
            events.append(
                {
                    "source_id": source_id,
                    "surface": surface,
                    "session_id": session_id,
                    "workflow": workflow,
                    "executions": executions,
                    "repeat": repeat,
                    "timestamp": timestamp.isoformat() if timestamp else None,
                    "abandoned": str(row.get("status") or "").lower() == "abandoned",
                }
            )
    return events


def _usage_maturity_level(*, repeat: bool, executions: int, surfaces: int) -> str:
    if surfaces >= 3 and repeat and executions >= 4:
        return "dependent"
    if repeat and executions >= 2:
        return "adopted"
    if executions >= 1:
        return "active"
    return "observed"


def build_usage_registry_inventory(*, program_session_id: str) -> dict[str, Any]:
    events = _collect_usage_events()
    registered = _registered_sessions(program_session_id=program_session_id)
    operator_sessions = sorted({str(r.get("operator_session_id") or r.get("program_session_id") or "") for r in registered if r})
    customer_sessions = sorted(
        {
            str(e.get("session_id") or "")
            for e in events
            if e.get("session_id")
        }
        | {str(r.get("customer_session_id") or r.get("usage_session_id") or "") for r in registered}
    )
    customer_sessions = [s for s in customer_sessions if s]

    sources = []
    for source_id, module_path, list_fn, surface in _USAGE_SOURCE_CATALOG:
        rows = _load_source_rows(module_path, list_fn)
        sources.append(
            {
                "source_id": source_id,
                "surface": surface,
                "record_count": len(rows),
                "populated": len(rows) > 0,
            }
        )

    return {
        "inventory_id": "usage-registry-inventory",
        "program_session_id": program_session_id,
        "operator_sessions": operator_sessions,
        "customer_sessions": customer_sessions,
        "workflow_executions": sum(int(e.get("executions") or 0) for e in events),
        "et_runs": sum(1 for e in events if e.get("surface") == "et_pipeline"),
        "provider_interactions": sum(1 for e in events if e.get("surface") == "provider"),
        "dashboard_access_events": sum(1 for e in events if e.get("surface") == "dashboard"),
        "registered_usage_sessions": registered,
        "sources": sources,
        "read_only": True,
    }


def build_active_usage_report(*, program_session_id: str) -> dict[str, Any]:
    events = _collect_usage_events()
    sessions = {str(e.get("session_id") or "") for e in events if e.get("session_id")}
    registered = _registered_sessions(program_session_id=program_session_id)
    for row in registered:
        sid = str(row.get("customer_session_id") or row.get("usage_session_id") or "")
        if sid:
            sessions.add(sid)

    active_count = len(sessions)
    daily = active_count
    weekly = active_count
    monthly = active_count

    return {
        "report_id": "active-usage-report",
        "program_session_id": program_session_id,
        "daily_active_users": daily,
        "weekly_active_users": weekly,
        "monthly_active_users": monthly,
        "active_usage_demonstrated": active_count > 0,
        "read_only": True,
    }


def build_workflow_adoption_report(*, program_session_id: str) -> dict[str, Any]:
    events = _collect_usage_events()
    by_surface: dict[str, int] = {surface: 0 for surface in USAGE_SURFACES}
    workflows: set[str] = set()

    for event in events:
        surface = str(event.get("surface") or "mission_control")
        if surface in by_surface:
            by_surface[surface] += int(event.get("executions") or 1)
        workflows.add(str(event.get("workflow") or ""))

    total = sum(by_surface.values()) or 1
    adoption_rate = round(min(1.0, len(workflows) / max(len(USAGE_SURFACES), 1)), 3)

    return {
        "report_id": "workflow-adoption-report",
        "program_session_id": program_session_id,
        "et_usage": by_surface.get("et_pipeline", 0),
        "mission_control_usage": by_surface.get("mission_control", 0),
        "provider_usage": by_surface.get("provider", 0),
        "governance_usage": by_surface.get("governance", 0),
        "dashboard_usage": by_surface.get("dashboard", 0),
        "workflow_adoption_rate": adoption_rate,
        "distinct_workflows": sorted(w for w in workflows if w),
        "read_only": True,
    }


def build_retained_usage_report(*, program_session_id: str) -> dict[str, Any]:
    events = _collect_usage_events()
    by_session: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        sid = str(event.get("session_id") or "unknown")
        by_session.setdefault(sid, []).append(event)

    repeat_sessions = 0
    recurring_workflows = 0
    sustained = 0

    for session_events in by_session.values():
        if len(session_events) > 1 or any(e.get("repeat") for e in session_events):
            repeat_sessions += 1
        workflows = {str(e.get("workflow") or "") for e in session_events}
        if len(workflows) > 1 or any(int(e.get("executions") or 0) > 1 for e in session_events):
            recurring_workflows += 1
        if any(int(e.get("executions") or 0) >= 2 for e in session_events):
            sustained += 1

    return {
        "report_id": "retained-usage-report",
        "program_session_id": program_session_id,
        "repeat_sessions": repeat_sessions,
        "recurring_workflows": recurring_workflows,
        "sustained_activity_sessions": sustained,
        "retained_users": repeat_sessions,
        "retained_usage_demonstrated": repeat_sessions > 0,
        "read_only": True,
    }


def build_platform_dependence_report(*, program_session_id: str) -> dict[str, Any]:
    events = _collect_usage_events()
    by_session: dict[str, dict[str, Any]] = {}

    for event in events:
        sid = str(event.get("session_id") or "unknown")
        bucket = by_session.setdefault(
            sid,
            {"executions": 0, "repeat": False, "surfaces": set(), "workflows": set()},
        )
        bucket["executions"] += int(event.get("executions") or 1)
        bucket["repeat"] = bucket["repeat"] or bool(event.get("repeat"))
        bucket["surfaces"].add(str(event.get("surface") or ""))
        bucket["workflows"].add(str(event.get("workflow") or ""))

    dependence_scores: list[float] = []
    maturity_counts = {level: 0 for level in USAGE_MATURITY_LEVELS}

    for bucket in by_session.values():
        surfaces = len(bucket["surfaces"])
        level = _usage_maturity_level(
            repeat=bucket["repeat"],
            executions=bucket["executions"],
            surfaces=surfaces,
        )
        maturity_counts[level] = maturity_counts.get(level, 0) + 1
        score = round(min(1.0, (bucket["executions"] + surfaces) / 6), 3)
        dependence_scores.append(score)

    avg_dependence = round(sum(dependence_scores) / len(dependence_scores), 3) if dependence_scores else 0.0

    return {
        "report_id": "platform-dependence-report",
        "program_session_id": program_session_id,
        "workflow_reliance_sessions": sum(1 for b in by_session.values() if b["repeat"]),
        "repeat_execution_patterns": sum(1 for b in by_session.values() if b["executions"] >= 2),
        "operational_dependence_sessions": maturity_counts.get("dependent", 0) + maturity_counts.get("adopted", 0),
        "usage_maturity_distribution": maturity_counts,
        "platform_dependence_score": avg_dependence,
        "workflow_dependence_demonstrated": avg_dependence >= 0.5,
        "read_only": True,
    }


def build_adoption_friction_report(*, program_session_id: str) -> dict[str, Any]:
    events = _collect_usage_events()
    friction: list[dict[str, Any]] = []

    abandoned = [e for e in events if e.get("abandoned")]
    for event in abandoned:
        friction.append(
            {
                "category": "abandoned_workflow",
                "session_id": event.get("session_id"),
                "workflow": event.get("workflow"),
            }
        )

    by_surface: dict[str, int] = {}
    for event in events:
        surface = str(event.get("surface") or "")
        by_surface[surface] = by_surface.get(surface, 0) + int(event.get("executions") or 1)

    for surface in USAGE_SURFACES:
        if by_surface.get(surface, 0) == 0:
            friction.append({"category": "low_use_feature", "surface": surface, "detail": "No usage observed"})

    if not events:
        friction.append({"category": "onboarding_failure", "detail": "No platform usage events detected"})

    friction_score = round(len(friction) / max(len(events) + len(USAGE_SURFACES), 1), 3)

    return {
        "report_id": "adoption-friction-report",
        "program_session_id": program_session_id,
        "friction_count": len(friction),
        "abandoned_workflows": [f for f in friction if f.get("category") == "abandoned_workflow"],
        "low_use_features": [f for f in friction if f.get("category") == "low_use_feature"],
        "onboarding_failures": [f for f in friction if f.get("category") == "onboarding_failure"],
        "adoption_blockers": friction[:20],
        "adoption_friction_score": friction_score,
        "read_only": True,
    }


def build_adoption_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    friction = build_adoption_friction_report(program_session_id=program_session_id)
    onboarding: list[dict[str, Any]] = []
    workflow: list[dict[str, Any]] = []
    education: list[dict[str, Any]] = []
    retention: list[dict[str, Any]] = []

    for blocker in friction.get("adoption_blockers") or []:
        category = str(blocker.get("category") or "")
        opportunity = {
            "blocker": blocker,
            "advisory_only": True,
            "behavioral_manipulation_performed": False,
        }
        if category == "onboarding_failure":
            onboarding.append({**opportunity, "opportunity": "Improve onboarding for first-use workflows"})
        elif category == "abandoned_workflow":
            retention.append({**opportunity, "opportunity": "Investigate abandoned workflow retention"})
        elif category == "low_use_feature":
            workflow.append({**opportunity, "opportunity": f"Increase adoption of {blocker.get('surface')} surface"})
            education.append({**opportunity, "opportunity": f"Educate operators on {blocker.get('surface')} capabilities"})

    opportunities = onboarding + workflow + education + retention
    return {
        "registry_id": "adoption-opportunity-registry",
        "program_session_id": program_session_id,
        "opportunity_count": len(opportunities),
        "onboarding_opportunities": onboarding,
        "workflow_opportunities": workflow,
        "education_opportunities": education,
        "retention_opportunities": retention,
        "automated_outreach_performed": False,
        "read_only": True,
    }


def compute_usage_adoption_metrics(*, program_session_id: str) -> dict[str, Any]:
    active = build_active_usage_report(program_session_id=program_session_id)
    retained = build_retained_usage_report(program_session_id=program_session_id)
    workflow = build_workflow_adoption_report(program_session_id=program_session_id)
    dependence = build_platform_dependence_report(program_session_id=program_session_id)
    friction = build_adoption_friction_report(program_session_id=program_session_id)

    return {
        "active_users": active.get("monthly_active_users", 0),
        "retained_users": retained.get("retained_users", 0),
        "recurring_workflows": retained.get("recurring_workflows", 0),
        "workflow_adoption_rate": workflow.get("workflow_adoption_rate", 0.0),
        "platform_dependence_score": dependence.get("platform_dependence_score", 0.0),
        "adoption_friction_score": friction.get("adoption_friction_score", 0.0),
        "read_only": True,
    }


def register_usage_session_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    usage_session_id = kv.get("usage_session_id") or kv.get("customer_session_id") or kv.get("session_id") or (
        f"usage-{len(_registered_sessions(program_session_id=program_session_id)) + 1}"
    )
    entry = register_usage_session_entry(
        entry={
            "usage_session_id": usage_session_id,
            "program_session_id": program_session_id,
            "customer_session_id": kv.get("customer_session_id") or usage_session_id,
            "operator_session_id": kv.get("operator_session_id") or program_session_id,
            "surface": kv.get("surface") or "mission_control",
            "segment": kv.get("segment") or "operator",
        }
    )
    from aethos_core.workstreams.real_usage_density_platform_adoption_program.real_usage_density_platform_adoption_program_store import (
        append_platform_adoption_record,
    )

    append_platform_adoption_record(
        session_id=program_session_id,
        kind="usage_session_entry",
        content=body,
        metadata=entry,
    )
    return entry
