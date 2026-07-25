# SPDX-License-Identifier: Apache-2.0
"""FIX 348 / WORKSTREAM_F2 — customer value & adoption validation executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    list_customer_value_adoption_validation_records,
    list_usage_observation_registry_entries,
    register_usage_observation,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    get_latest_customer_delivery_request,
    list_customer_pilot_run_registry_entries,
)


def _session_rows(rows: list[dict[str, Any]], *, session_id: str) -> list[dict[str, Any]]:
    return [row for row in rows if str(row.get("session_id") or "") == session_id]


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def build_delivered_solution_registry(*, session_id: str) -> dict[str, Any]:
    runs = _session_rows(list_customer_pilot_run_registry_entries(), session_id=session_id)
    request = get_latest_customer_delivery_request(session_id=session_id)
    solutions = []
    for run in runs:
        deployment = (run.get("stage_results") or {}).get("deployment") or {}
        solutions.append(
            {
                "run_id": run.get("run_id"),
                "request_type": run.get("request_type"),
                "scenario_id": run.get("scenario_id"),
                "deployment_identifier": deployment.get("deployment_id") or run.get("run_id"),
                "certification_passed": run.get("passed") is True,
                "customer_acceptance_status": "human_review_pending",
                "composed_from_workstream_f1": True,
            }
        )
    return {
        "registry_id": "delivered-solution-registry",
        "session_id": session_id,
        "solution_count": len(solutions),
        "solutions": solutions,
        "latest_request": request,
        "read_only": True,
    }


def build_customer_usage_report(*, session_id: str) -> dict[str, Any]:
    observations = _session_rows(list_usage_observation_registry_entries(), session_id=session_id)
    records = _session_rows(list_customer_value_adoption_validation_records(), session_id=session_id)
    usage_notes = [r for r in records if str(r.get("kind") or "") == "customer_usage_observation"]
    total_executions = sum(int(o.get("executions") or 0) for o in observations)
    endpoints = sorted({str(o.get("endpoint") or "") for o in observations if o.get("endpoint")})
    workflows = sorted({str(o.get("workflow") or "") for o in observations if o.get("workflow")})
    return {
        "report_id": "customer-usage-report",
        "session_id": session_id,
        "observation_count": len(observations),
        "usage_note_count": len(usage_notes),
        "application_usage_events": total_executions,
        "workflow_executions": workflows,
        "endpoint_utilization": endpoints,
        "engagement_signals": observations[-10:],
        "read_only": True,
    }


def build_customer_adoption_report(*, session_id: str) -> dict[str, Any]:
    observations = _session_rows(list_usage_observation_registry_entries(), session_id=session_id)
    first_use = bool(observations)
    repeat_use = any(int(o.get("executions") or 0) > 1 for o in observations)
    active = any(str(o.get("status") or "").lower() == "active" for o in observations) or repeat_use
    abandoned = any(str(o.get("status") or "").lower() == "abandoned" for o in observations)
    if observations and not active and not abandoned:
        active = True
    return {
        "report_id": "customer-adoption-report",
        "session_id": session_id,
        "first_use": first_use,
        "repeat_use": repeat_use,
        "active_usage": active,
        "abandoned_usage": abandoned,
        "adoption_rate": 1.0 if first_use else 0.0,
        "repeat_usage_rate": 1.0 if repeat_use else 0.0,
        "read_only": True,
    }


def build_customer_value_validation_report(*, session_id: str) -> dict[str, Any]:
    request = get_latest_customer_delivery_request(session_id=session_id) or {}
    adoption = build_customer_adoption_report(session_id=session_id)
    usage = build_customer_usage_report(session_id=session_id)
    expected = {
        "success_criteria": request.get("success_criteria"),
        "goal": request.get("goal"),
        "scope": request.get("scope"),
    }
    observed = {
        "application_usage_events": usage.get("application_usage_events"),
        "repeat_use": adoption.get("repeat_use"),
        "active_usage": adoption.get("active_usage"),
    }
    aligned = adoption.get("first_use") and (
        adoption.get("repeat_use") or usage.get("application_usage_events", 0) > 0
    )
    score = round(
        (
            (1.0 if adoption.get("first_use") else 0.0)
            + (1.0 if adoption.get("repeat_use") else 0.0)
            + (0.5 if adoption.get("active_usage") else 0.0)
        )
        / 2.5,
        3,
    )
    return {
        "report_id": "customer-value-validation-report",
        "session_id": session_id,
        "expected_value": expected,
        "observed_value": observed,
        "value_aligned": aligned,
        "value_realization_score": score,
        "customer_manipulation_performed": False,
        "read_only": True,
    }


def build_customer_retention_report(*, session_id: str) -> dict[str, Any]:
    observations = _session_rows(list_usage_observation_registry_entries(), session_id=session_id)
    continued = any(str(o.get("trend") or "").lower() == "continued" for o in observations) or len(observations) >= 2
    declining = any(str(o.get("trend") or "").lower() == "declining" for o in observations)
    dormant = any(str(o.get("trend") or "").lower() == "dormant" for o in observations) or (
        not observations and _session_rows(list_customer_pilot_run_registry_entries(), session_id=session_id)
    )
    retention_rate = 1.0 if continued else (0.5 if observations else 0.0)
    return {
        "report_id": "customer-retention-report",
        "session_id": session_id,
        "continued_usage": continued,
        "declining_usage": declining,
        "dormant_usage": dormant,
        "retention_rate": retention_rate,
        "abandonment_rate": 1.0 if dormant and not continued else 0.0,
        "read_only": True,
    }


def build_customer_friction_report(*, session_id: str) -> dict[str, Any]:
    records = _session_rows(list_customer_value_adoption_validation_records(), session_id=session_id)
    notes = [str(r.get("content") or "") for r in records if str(r.get("kind") or "") == "customer_value_note"]

    def _match(keywords: tuple[str, ...]) -> list[str]:
        return [note for note in notes if any(k in note.lower() for k in keywords)]

    return {
        "report_id": "customer-friction-report",
        "session_id": session_id,
        "onboarding_friction": _match(("onboard", "setup", "getting started")),
        "usability_friction": _match(("usability", "confus", "unclear", "hard to use")),
        "trust_friction": _match(("trust", "approval", "governance", "permission")),
        "operational_friction": _match(("deploy", "provider", "git", "workflow", "slow")),
        "note_count": len(notes),
        "read_only": True,
    }


def build_customer_value_opportunity_registry(*, session_id: str) -> dict[str, Any]:
    adoption = build_customer_adoption_report(session_id=session_id)
    friction = build_customer_friction_report(session_id=session_id)
    retention = build_customer_retention_report(session_id=session_id)
    opportunities: list[dict[str, Any]] = []
    if not adoption.get("repeat_use"):
        opportunities.append(
            {
                "opportunity_id": "adopt-repeat-use",
                "category": "adoption",
                "detail": "Encourage repeat usage observation after first delivery",
                "automatic_action_forbidden": True,
            }
        )
    if retention.get("dormant_usage"):
        opportunities.append(
            {
                "opportunity_id": "retention-reactivation-signal",
                "category": "retention",
                "detail": "Dormant usage detected — advisory only, no automated outreach",
                "automatic_action_forbidden": True,
            }
        )
    for category, items in (
        ("onboarding", friction.get("onboarding_friction") or []),
        ("usability", friction.get("usability_friction") or []),
        ("value_realization", friction.get("operational_friction") or []),
    ):
        for idx, detail in enumerate(items[:2]):
            opportunities.append(
                {
                    "opportunity_id": f"{category}-{idx + 1}",
                    "category": category,
                    "detail": detail,
                    "automatic_action_forbidden": True,
                }
            )
    return {
        "registry_id": "customer-value-opportunity-registry",
        "session_id": session_id,
        "opportunity_count": len(opportunities),
        "opportunities": opportunities,
        "read_only": True,
    }


def compute_validation_metrics(*, session_id: str) -> dict[str, Any]:
    adoption = build_customer_adoption_report(session_id=session_id)
    validation = build_customer_value_validation_report(session_id=session_id)
    retention = build_customer_retention_report(session_id=session_id)
    runs = _session_rows(list_customer_pilot_run_registry_entries(), session_id=session_id)
    satisfaction = "positive" if runs and runs[-1].get("customer_satisfaction") == "positive" else "neutral"
    if adoption.get("repeat_use"):
        satisfaction = "positive"
    return {
        "adoption_rate": adoption.get("adoption_rate", 0.0),
        "repeat_usage_rate": adoption.get("repeat_usage_rate", 0.0),
        "retention_rate": retention.get("retention_rate", 0.0),
        "value_realization_score": validation.get("value_realization_score", 0.0),
        "customer_satisfaction_trend": satisfaction,
        "abandonment_rate": retention.get("abandonment_rate", 0.0),
        "read_only": True,
    }


def record_customer_usage_observation(*, session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    observation = register_usage_observation(
        entry={
            "observation_id": f"f2-usage-{len(list_usage_observation_registry_entries()) + 1:05d}",
            "session_id": session_id,
            "workflow": kv.get("workflow") or kv.get("application"),
            "endpoint": kv.get("endpoint") or kv.get("path"),
            "executions": int(kv.get("executions") or kv.get("hits") or 1),
            "status": kv.get("status") or "active",
            "trend": kv.get("trend") or "continued",
            "detail": body,
        }
    )
    from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
        append_customer_value_adoption_validation_record,
    )

    append_customer_value_adoption_validation_record(
        session_id=session_id,
        kind="customer_usage_observation",
        content=body,
        metadata=observation,
    )
    return observation
