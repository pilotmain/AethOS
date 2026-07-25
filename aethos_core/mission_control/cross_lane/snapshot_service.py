# SPDX-License-Identifier: Apache-2.0
"""FIX 128 — Mission Control cross-lane snapshot service."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.cross_lane.correlation import derive_correlation_id
from aethos_core.mission_control.cross_lane.cross_lane_contract import (
    CROSS_LANE_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_128,
    OBSERVED_LANES,
)
from aethos_core.mission_control.cross_lane.lane_collectors import (
    collect_durable_jobs,
    collect_incident_command,
    collect_multi_agent,
    collect_production_governance,
    collect_railway_orchestration,
    collect_route_diagnostics,
    collect_software_delivery,
    collect_unified_timeline,
)

_SNAPSHOT_RX = re.compile(
    r"\bshow\s+mission\s+control\s+(?:operational\s+)?snapshot\b",
    re.I,
)
_TIMELINE_RX = re.compile(r"\bshow\s+mission\s+control\s+(?:unified\s+)?timeline\b", re.I)
_ATTENTION_RX = re.compile(r"\bshow\s+mission\s+control\s+attention\s+queue\b", re.I)
_HEALTH_RX = re.compile(r"\bshow\s+mission\s+control\s+health\s+summary\b", re.I)
_AUDIT_RX = re.compile(r"\bsearch\s+mission\s+control\s+audit\b", re.I)
_DASHBOARD_RX = re.compile(r"\bshow\s+mission\s+control\s+dashboard\b", re.I)


@dataclass(frozen=True)
class MissionControlSnapshotResult:
    ok: bool
    snapshot: dict[str, Any]
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def is_mission_control_observability_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        _SNAPSHOT_RX.search(raw)
        or _TIMELINE_RX.search(raw)
        or _ATTENTION_RX.search(raw)
        or _HEALTH_RX.search(raw)
        or _AUDIT_RX.search(raw)
        or _DASHBOARD_RX.search(raw)
    )


def load_mission_control_config() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "enabled": bool(getattr(settings, "mission_control_cross_lane_enabled", True)),
    }


def build_mission_control_snapshot(*, session_id: str) -> MissionControlSnapshotResult:
    cfg = load_mission_control_config()
    if not cfg["enabled"]:
        return MissionControlSnapshotResult(ok=False, snapshot={}, blockers=["mission_control_disabled"])

    sd = collect_software_delivery(session_id=session_id)
    plan_id = str(sd.get("plan_id") or "")
    correlation_id = derive_correlation_id(session_id=session_id, plan_id=plan_id)

    lanes = {
        "software_delivery": sd,
        "multi_agent_collaboration": collect_multi_agent(session_id=session_id),
        "railway_orchestration": collect_railway_orchestration(session_id=session_id),
        "production_governance": collect_production_governance(session_id=session_id),
        "incident_command": collect_incident_command(session_id=session_id),
        "route_diagnostics": collect_route_diagnostics(session_id=session_id),
        "durable_jobs": collect_durable_jobs(session_id=session_id),
    }

    pending_gates: list[dict[str, Any]] = []
    for gate in sd.get("governance_gates") or []:
        if not gate.get("passed"):
            pending_gates.append(
                {
                    "lane": "software_delivery",
                    "gate": gate.get("gate"),
                    "priority": "high" if gate.get("gate") in {"workspace_verification", "github_preflight_approved"} else "medium",
                }
            )
    if lanes["incident_command"].get("open_incidents"):
        pending_gates.append(
            {
                "lane": "incident_command",
                "gate": "open_production_incident",
                "priority": "critical",
                "count": lanes["incident_command"].get("open_incidents"),
            }
        )

    snapshot = {
        "snapshot_id": f"mcs-{uuid.uuid4().hex[:12]}",
        "schema_version": CROSS_LANE_SCHEMA_VERSION,
        "session_id": session_id,
        "correlation_id": correlation_id,
        "plan_id": plan_id,
        "observed_lanes": list(OBSERVED_LANES),
        "mutation_performed": MUTATION_PERFORMED_FIX_128,
        "recorded_at": datetime.now(UTC).isoformat(),
        "lanes": lanes,
        "unified_timeline": [],
        "execution_health": {},
        "attention_queue": pending_gates,
        "active_approvals": [g for g in pending_gates if "approval" in str(g.get("gate") or "") or "preflight" in str(g.get("gate") or "")],
        "rollout_visibility": lanes["production_governance"],
        "incident_linkage": lanes["incident_command"],
        "agent_collaboration_summary": lanes["multi_agent_collaboration"],
    }
    snapshot["unified_timeline"] = collect_unified_timeline(snapshot)
    snapshot["execution_health"] = _execution_health_summary(lanes)

    return MissionControlSnapshotResult(
        ok=True,
        snapshot=snapshot,
        detail="Cross-lane operational snapshot assembled (read-only).",
    )


def _execution_health_summary(lanes: dict[str, Any]) -> dict[str, Any]:
    sd = lanes.get("software_delivery") or {}
    pending = len(sd.get("pending_gates") or [])
    return {
        "overall": "healthy" if pending <= 2 else "attention_required",
        "software_delivery_pending_gates": pending,
        "railway_journals_seen": (lanes.get("railway_orchestration") or {}).get("recent_journals", 0),
        "open_incidents": (lanes.get("incident_command") or {}).get("open_incidents", 0),
        "route_trace_present": bool((lanes.get("route_diagnostics") or {}).get("route_id")),
        "mutation_performed_in_snapshot": False,
    }


def search_mission_control_audit(*, session_id: str, query: str) -> MissionControlSnapshotResult:
    result = build_mission_control_snapshot(session_id=session_id)
    if not result.ok:
        return result
    needle = (query or "").strip().lower()
    if not needle:
        result.snapshot["audit_matches"] = []
        return result
    matches: list[dict[str, Any]] = []
    for entry in result.snapshot.get("unified_timeline") or []:
        blob = f"{entry.get('lane')} {entry.get('action')} {entry.get('detail')}".lower()
        if needle in blob:
            matches.append(entry)
    snap = dict(result.snapshot)
    snap["audit_query"] = query
    snap["audit_matches"] = matches
    return MissionControlSnapshotResult(ok=True, snapshot=snap, detail=f"{len(matches)} audit match(es).")
