# SPDX-License-Identifier: Apache-2.0
"""Railway deployment lifecycle diagnostics — resolver trace without mutation."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
    _collect_legacy_lifecycle_parts,
    _load_lifecycle_from_route_trace,
    lifecycle_plan_snapshot,
    lifecycle_preflight_snapshot,
    lifecycle_simulation_snapshot,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
    format_global_lifecycle_entry_lines,
    inspect_all_global_lifecycle_entries,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    get_lifecycle_session,
    inspect_global_lifecycle_index,
    load_latest_active_lifecycle,
    load_lifecycle_by_repo,
    session_lifecycle_file_exists,
)


def _lifecycle_stage(record: dict[str, Any] | None) -> str:
    if not record or not record.get("repo"):
        return "empty"
    plan = record.get("plan") or {}
    if not plan.get("exists"):
        readiness = record.get("readiness") or {}
        if readiness.get("status") == "passed":
            return "readiness_passed"
        return "pre_plan"
    if not plan.get("review_confirmed"):
        return "plan_unconfirmed"
    preflight = record.get("preflight") or {}
    if not preflight.get("exists"):
        return "plan_confirmed"
    simulation = record.get("simulation") or {}
    if not simulation.get("exists"):
        return "preflight_ready"
    return "simulated"


def _latest_index_summary(index_inspection: dict[str, Any]) -> dict[str, str]:
    if not index_inspection.get("readable"):
        return {}
    index = index_inspection.get("index") or {}
    entries = sorted(
        list(index.get("entries") or []),
        key=lambda row: str(row.get("updated_at") or ""),
        reverse=True,
    )
    if not entries:
        return {}
    latest_id = str(index_inspection.get("latest_lifecycle_id") or entries[0].get("lifecycle_id") or "")
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import load_lifecycle_by_id

    record = load_lifecycle_by_id(latest_id) if latest_id else None
    if not record:
        record = load_latest_active_lifecycle()
    if not record:
        return {"latest_lifecycle_id": latest_id}
    return {
        "latest_repo": str(record.get("repo") or "—"),
        "latest_project_environment": f"{record.get('project') or '—'} / {record.get('environment') or '—'}",
        "latest_stage": _lifecycle_stage(record),
        "latest_lifecycle_id": latest_id or str(record.get("lifecycle_id") or "—"),
    }


def trace_railway_deployment_lifecycle_resolution(
    *,
    session_id: str,
    user_text: str = "",
) -> dict[str, Any]:
    """Trace resolver sources without persisting or materializing."""
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_sync import _merge_records
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import empty_lifecycle_record
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        extract_github_repo_target,
    )

    session_id = (session_id or "default").strip()
    attempts: list[dict[str, str]] = []
    candidates: list[dict[str, Any]] = []

    session_record = get_lifecycle_session(session_id=session_id)
    if session_record and session_record.get("repo"):
        attempts.append({"source": "current_session", "result": "hit"})
        candidates.append(session_record)
    else:
        attempts.append({"source": "current_session", "result": "miss"})

    repo_hint = extract_github_repo_target(user_text or "")
    by_repo = load_lifecycle_by_repo(repo_hint) if repo_hint else None
    if repo_hint:
        attempts.append(
            {
                "source": "repo_specific_global",
                "result": "hit" if by_repo else "miss",
                "repo": repo_hint,
            }
        )
        if by_repo:
            candidates.append(by_repo)
    else:
        attempts.append({"source": "repo_specific_global", "result": "skipped", "detail": "no repo in text"})

    latest = load_latest_active_lifecycle()
    attempts.append({"source": "latest_active_global", "result": "hit" if latest else "miss"})
    if latest:
        candidates.append(latest)

    legacy = _collect_legacy_lifecycle_parts(session_id=session_id, user_text=user_text)
    if legacy.get("repo"):
        attempts.append({"source": "legacy_stores", "result": "hit"})
        candidates.append(legacy)
    else:
        attempts.append({"source": "legacy_stores", "result": "miss"})

    trace_record = _load_lifecycle_from_route_trace(session_id=session_id)
    attempts.append({"source": "route_trace_fallback", "result": "hit" if trace_record else "miss"})
    if trace_record:
        candidates.append(trace_record)

    hydrated = False
    source = "none"
    merged: dict[str, Any] | None = None
    if candidates:
        merged = empty_lifecycle_record()
        for record in candidates:
            merged = _merge_records(merged, record)
        if session_record and session_record.get("repo"):
            merged = _merge_records(merged, session_record)
        if merged.get("repo"):
            hydrated = True
            if session_record and session_record.get("repo"):
                source = "current_session+merge"
            elif by_repo:
                source = "repo_specific_global"
            elif latest:
                source = "latest_active_global"
            elif legacy.get("repo"):
                source = "legacy_stores"
            elif trace_record:
                source = "route_trace_fallback"
            else:
                source = "merged_candidates"

    index_inspection = inspect_global_lifecycle_index()
    latest_summary = _latest_index_summary(index_inspection)

    return {
        "session_id": session_id,
        "session_file_exists": session_lifecycle_file_exists(session_id=session_id),
        "index": index_inspection,
        "latest_summary": latest_summary,
        "attempts": attempts,
        "hydrated": hydrated,
        "source": source,
        "lifecycle": merged,
        "plan_found": lifecycle_plan_snapshot(merged) is not None if merged else False,
        "preflight_found": lifecycle_preflight_snapshot(merged) is not None if merged else False,
        "simulation_found": lifecycle_simulation_snapshot(merged) is not None if merged else False,
        "stage": _lifecycle_stage(merged),
    }


def format_lifecycle_diagnostics_report(trace: dict[str, Any]) -> str:
    index = trace.get("index") or {}
    latest = trace.get("latest_summary") or {}
    lines = [
        "Railway deployment lifecycle diagnostics",
        "",
        "Session:",
        f"- session_id: `{trace.get('session_id', '—')}`",
        f"- session file exists: **{'yes' if trace.get('session_file_exists') else 'no'}**",
    ]
    if trace.get("session_file_exists"):
        session_record = get_lifecycle_session(session_id=str(trace.get("session_id") or "default"))
        if session_record:
            lines.append(f"- session repo: `{session_record.get('repo') or '—'}`")
            stage = _lifecycle_stage(session_record)
            lines.append(f"- session stage: **{stage}**")
            from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
                is_readiness_only_lifecycle,
            )

            if is_readiness_only_lifecycle(session_record):
                lines.append("- session lifecycle kind: **readiness-only (not a deployment plan)**")

    lines.extend(
        [
            "",
            "Global index:",
            f"- exists: **{'yes' if index.get('exists') else 'no'}**",
            f"- readable: **{'yes' if index.get('readable') else 'no'}**",
            f"- entries: **{index.get('entries', 0)}**",
        ]
    )
    if index.get("error"):
        lines.append(f"- index error: {index['error']}")
    if latest:
        lines.extend(
            [
                f"- latest repo: `{latest.get('latest_repo', '—')}`",
                f"- latest project/environment: `{latest.get('latest_project_environment', '—')}`",
                f"- latest stage: **{latest.get('latest_stage', '—')}**",
            ]
        )

    entries = inspect_all_global_lifecycle_entries()
    if entries:
        lines.append("")
        lines.extend(format_global_lifecycle_entry_lines(entries))

    lines.extend(["", "Resolver attempts:"])
    for idx, attempt in enumerate(trace.get("attempts") or [], start=1):
        label = str(attempt.get("source") or "unknown").replace("_", " ")
        result = str(attempt.get("result") or "miss")
        extra = ""
        if attempt.get("repo"):
            extra = f" (`{attempt['repo']}`)"
        elif attempt.get("detail"):
            extra = f" ({attempt['detail']})"
        lines.append(f"{idx}. {label}: **{result}**{extra}")

    lines.extend(
        [
            "",
            "Result:",
            f"- hydrated: **{'yes' if trace.get('hydrated') else 'no'}**",
            f"- source: `{trace.get('source', 'none')}`",
            f"- plan: **{'found' if trace.get('plan_found') else 'missing'}**",
            f"- preflight: **{'found' if trace.get('preflight_found') else 'missing'}**",
            f"- simulation: **{'found' if trace.get('simulation_found') else 'missing'}**",
        ]
    )
    lifecycle = trace.get("lifecycle")
    if lifecycle:
        from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
            is_readiness_only_lifecycle,
        )

        if is_readiness_only_lifecycle(lifecycle):
            lines.append("- resolved lifecycle kind: **readiness-only (not a deployment plan)**")
    lines.extend(["", "No mutation."])
    return "\n".join(lines)
