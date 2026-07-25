# SPDX-License-Identifier: Apache-2.0
"""FIX 136 — aggregate read-only operator evidence bundle for export."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.cross_lane.cross_lane_contract import ARCHITECTURE_BOUNDARY, OBSERVED_LANES
from aethos_core.mission_control.cross_lane.lane_drilldown_service import build_lane_drilldown
from aethos_core.mission_control.cross_lane.snapshot_service import build_mission_control_snapshot
from aethos_core.mission_control.evidence_bundle.evidence_bundle_contract import (
    EVIDENCE_BUNDLE_FIX,
    EVIDENCE_BUNDLE_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_136,
)
from aethos_core.mission_control.evidence_bundle.evidence_bundle_redaction import redact_dict, redact_sensitive_value


@dataclass(frozen=True)
class EvidenceBundleResult:
    ok: bool
    session_id: str
    bundle: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _session_jobs(session_id: str, *, job_id: str | None = None) -> list[dict[str, Any]]:
    from aethos_core.runtime.jobs import job_store

    rows: list[dict[str, Any]] = []
    for job in job_store.list_all():
        if job.session_id != session_id:
            continue
        if job_id and job.id != job_id:
            continue
        rows.append(redact_dict(job.to_dict()))
    return rows


def _job_events(session_id: str, *, job_ids: list[str]) -> list[dict[str, Any]]:
    from aethos_core.runtime.authority import authority

    events = authority.list_job_events(session_id=session_id)
    if job_ids:
        allowed = set(job_ids)
        events = [ev for ev in events if str(ev.get("job_id") or "") in allowed]
    return [redact_dict(ev) if isinstance(ev, dict) else ev for ev in events]


def _job_evidence_map(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    from aethos_core.provider_evidence.store import get_evidence_bundle

    out: dict[str, Any] = {}
    for job in jobs:
        jid = str(job.get("id") or "")
        if not jid:
            continue
        resp = get_evidence_bundle(job_id=jid)
        if resp.get("ok"):
            out[jid] = redact_dict(dict(resp.get("bundle") or {}))
    return out


def _lifecycle_entries(session_id: str) -> list[dict[str, Any]]:
    from aethos_core.operation_lifecycle.global_lifecycle_index import list_lifecycle_entries_for_session

    return [redact_dict(dict(entry)) for entry in list_lifecycle_entries_for_session(session_id, limit=40)]


def _collect_receipts(lane_drilldowns: dict[str, Any]) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for lane_payload in lane_drilldowns.values():
        for section in lane_payload.get("sections") or []:
            if section.get("kind") != "receipt_list":
                continue
            for item in section.get("items") or []:
                if isinstance(item, dict):
                    receipts.append(redact_dict(item))
    return receipts


def _collect_verification(lane_drilldowns: dict[str, Any]) -> dict[str, Any]:
    verification: dict[str, Any] = {"sections": [], "summary": {}}
    sd = lane_drilldowns.get("software_delivery") or {}
    for section in sd.get("sections") or []:
        kind = str(section.get("kind") or "")
        if kind in {"verification_evidence", "gate_list", "key_value"}:
            verification["sections"].append(
                {
                    "section_id": section.get("section_id"),
                    "title": section.get("title"),
                    "kind": kind,
                    "rows": section.get("rows"),
                    "items": redact_sensitive_value(section.get("items")),
                }
            )
    return verification


def _collect_blockers(
    *,
    snapshot: dict[str, Any],
    approval_inbox: dict[str, Any],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for item in snapshot.get("attention_queue") or []:
        blockers.append(
            {
                "source": "attention_queue",
                "lane": item.get("lane"),
                "gate": item.get("gate"),
                "priority": item.get("priority"),
                "detail": item.get("detail") or item.get("gate"),
            }
        )
    for item in approval_inbox.get("items") or []:
        for forbidden in item.get("remains_forbidden") or []:
            blockers.append(
                {
                    "source": "approval_inbox",
                    "inbox_id": item.get("inbox_id"),
                    "lane": item.get("lane"),
                    "gate_id": item.get("gate_id"),
                    "detail": f"forbidden:{forbidden}",
                }
            )
    health = snapshot.get("execution_health") or {}
    if str(health.get("overall") or "") not in {"", "healthy", "unknown"}:
        blockers.append(
            {
                "source": "execution_health",
                "detail": f"overall_health:{health.get('overall')}",
            }
        )
    return blockers


def build_evidence_bundle(*, session_id: str, job_id: str | None = None) -> EvidenceBundleResult:
    sid = (session_id or "default").strip()[:64] or "default"
    focus_job = (job_id or "").strip() or None

    snap_result = build_mission_control_snapshot(session_id=sid)
    if not snap_result.ok or not snap_result.snapshot:
        return EvidenceBundleResult(
            ok=False,
            session_id=sid,
            blockers=list(snap_result.blockers or ["snapshot_unavailable"]),
            detail=snap_result.detail or "snapshot_unavailable",
        )

    snapshot = redact_dict(dict(snap_result.snapshot))
    lane_drilldowns: dict[str, Any] = {}
    for lane in OBSERVED_LANES:
        drill = build_lane_drilldown(session_id=sid, lane=lane)
        if drill.ok:
            lane_drilldowns[lane] = {
                "lane": lane,
                "session_id": sid,
                "sections": redact_sensitive_value(drill.sections),
            }

    from aethos_core.mission_control.approval_inbox.approval_audit_service import audit_history_payload
    from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload

    approval_inbox = approval_inbox_payload(session_id=sid)
    approval_audits = audit_history_payload(session_id=sid, limit=100)
    jobs = _session_jobs(sid, job_id=focus_job)
    job_ids = [str(j.get("id") or "") for j in jobs if j.get("id")]
    job_events = _job_events(sid, job_ids=job_ids if focus_job else job_ids)
    timeline = list(snapshot.get("unified_timeline") or [])
    timeline.extend(
        {
            "lane": "tracked_jobs",
            "timestamp": datetime.fromtimestamp(float(ev.get("at") or 0), UTC).isoformat()
            if ev.get("at")
            else "",
            "action": ev.get("event_type") or "job_event",
            "detail": ev.get("message") or "",
            "job_id": ev.get("job_id"),
        }
        for ev in job_events
        if isinstance(ev, dict)
    )

    bundle: dict[str, Any] = {
        "schema_version": EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "fix": EVIDENCE_BUNDLE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_136,
        "session_id": sid,
        "job_id": focus_job,
        "mission": {
            "session_id": sid,
            "correlation_id": snapshot.get("correlation_id"),
            "plan_id": snapshot.get("plan_id"),
            "snapshot_id": snapshot.get("snapshot_id"),
        },
        "snapshot": snapshot,
        "timeline": timeline,
        "receipts": _collect_receipts(lane_drilldowns),
        "approvals": {
            "pending_inbox": approval_inbox,
            "ui_audit": approval_audits,
        },
        "blockers": _collect_blockers(snapshot=snapshot, approval_inbox=approval_inbox),
        "verification": _collect_verification(lane_drilldowns),
        "audit": {
            "ui_approval_audits": approval_audits.get("audits") or [],
            "route_diagnostics": lane_drilldowns.get("route_diagnostics"),
        },
        "lane_drilldowns": lane_drilldowns,
        "jobs": jobs,
        "job_evidence": _job_evidence_map(jobs),
        "operation_lifecycle": _lifecycle_entries(sid),
        "incident_links": redact_sensitive_value(snapshot.get("incident_linkage") or {}),
        "architecture_boundary": ARCHITECTURE_BOUNDARY,
    }
    return EvidenceBundleResult(ok=True, session_id=sid, bundle=bundle, detail="Evidence bundle exported (read-only).")
