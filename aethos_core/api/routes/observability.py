# SPDX-License-Identifier: Apache-2.0
"""Observability API — metrics and metering."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse, Response

router = APIRouter(tags=["observability"])


@router.get("/observability/dashboard")
def observability_dashboard_api() -> dict[str, Any]:
    from aethos_core.observability.dashboard import build_observability_dashboard

    return build_observability_dashboard()


@router.get("/observability/metrics")
def observability_metrics_api() -> dict[str, Any]:
    from aethos_core.observability.metrics import snapshot_metrics

    return {"ok": True, "metrics": snapshot_metrics()}


@router.get("/observability/metrics/prometheus")
def observability_prometheus_api() -> PlainTextResponse:
    from aethos_core.observability.metrics import prometheus_text

    return PlainTextResponse(prometheus_text(), media_type="text/plain; version=0.0.4")


@router.get("/observability/metering")
def observability_metering_api(org_id: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    from aethos_core.observability.metering import get_usage_summary

    return {"ok": True, **get_usage_summary(org_id=org_id, session_id=session_id)}


# §3 Unified tamper-evident audit ledger — Mission Control "Audit" panel + SIEM export.


@router.get("/observability/audit")
def observability_audit_list_api(
    org: str | None = None,
    actor: str | None = None,
    action: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    from aethos_core.observability.audit_ledger import read_entries, verify_chain

    entries = read_entries(org=org, actor=actor, action=action, limit=limit)
    return {"ok": True, "entries": entries, "count": len(entries), "integrity": verify_chain()}


@router.get("/observability/audit/verify")
def observability_audit_verify_api() -> dict[str, Any]:
    from aethos_core.observability.audit_ledger import verify_chain

    return {"ok": True, **verify_chain()}


# §8 Observability export — SLOs + telemetry status.


@router.get("/observability/slo")
def observability_slo_api() -> dict[str, Any]:
    from aethos_core.observability.telemetry import evaluate_slos

    return {"ok": True, **evaluate_slos()}


@router.get("/observability/route-trace/{session_id}")
def observability_route_trace_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.chat.route_trace import get_last_route_trace

    trace = get_last_route_trace(session_id=session_id)
    return {"ok": True, "session_id": session_id, "trace": trace, "deep_link": f"/mission-control?view=observability&session={session_id}"}


@router.get("/observability/job-trace/{job_id}")
def observability_job_trace_api(job_id: str) -> dict[str, Any]:
    from aethos_core.jobs.mutation_execution_runtime import get_mutation_job_audit, get_mutation_job_truth

    truth = get_mutation_job_truth(job_id)
    audit = get_mutation_job_audit(job_id)
    return {
        "ok": bool(truth),
        "job_id": job_id,
        "truth": truth,
        "audit": audit,
        "deep_link": f"/mission-control?view=mutation-audit&job={job_id}",
    }


@router.get("/observability/telemetry")
def observability_telemetry_api() -> dict[str, Any]:
    from aethos_core.observability.telemetry import telemetry_status

    return {"ok": True, **telemetry_status()}


# §10 Data governance — retention (dry-run report + apply).


@router.get("/observability/retention")
def observability_retention_report_api() -> dict[str, Any]:
    from aethos_core.data_governance.retention import prune_retention

    return {"ok": True, **prune_retention(dry_run=True)}


@router.post("/observability/retention/prune")
def observability_retention_prune_api() -> dict[str, Any]:
    from aethos_core.data_governance.retention import prune_retention

    return {"ok": True, **prune_retention(dry_run=False)}


@router.get("/observability/audit/export")
def observability_audit_export_api(
    format: str = "json",
    org: str | None = None,
    actor: str | None = None,
    action: str | None = None,
) -> Response:
    """Complete, ordered, hash-linked trail for SIEM ingestion (json | csv)."""
    from aethos_core.observability.audit_ledger import export_csv, read_entries

    rows = read_entries(org=org, actor=actor, action=action)
    if format == "csv":
        return Response(
            content=export_csv(rows),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=aethos_audit.csv"},
        )
    import json as _json

    return Response(
        content=_json.dumps({"entries": rows, "count": len(rows)}, default=str),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=aethos_audit.json"},
    )
