# SPDX-License-Identifier: Apache-2.0
"""Repair Railway deployment lifecycle by materializing global index into session stores."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_materialization import (
    force_materialize_latest_global_lifecycle,
    format_global_lifecycle_entry_lines,
    inspect_all_global_lifecycle_entries,
    load_best_global_lifecycle_record,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    inspect_global_lifecycle_index,
)


def repair_railway_deployment_lifecycle(*, session_id: str) -> dict[str, Any]:
    """Materialize latest active lifecycle from global index into current session stores."""
    session_id = (session_id or "default").strip()
    index = inspect_global_lifecycle_index()
    if not index.get("exists"):
        return {"ok": False, "reason": "global lifecycle index does not exist", "session_id": session_id}
    if not index.get("readable"):
        return {
            "ok": False,
            "reason": f"global lifecycle index is not readable: {index.get('error') or 'unknown error'}",
            "session_id": session_id,
        }
    if int(index.get("entries") or 0) < 1:
        return {"ok": False, "reason": "global lifecycle index has no entries", "session_id": session_id}

    record, diag = load_best_global_lifecycle_record()
    if not record:
        result = {
            "ok": False,
            "reason": str(diag.get("reason") or "no_active_lifecycle"),
            "detail": str(diag.get("detail") or ""),
            "session_id": session_id,
            "entries": list(diag.get("entries") or inspect_all_global_lifecycle_entries()),
        }
        return result

    materialized = force_materialize_latest_global_lifecycle(session_id=session_id)
    if not materialized.get("ok"):
        return {
            "ok": False,
            "reason": str(materialized.get("reason") or "materialization_failed"),
            "detail": str(materialized.get("detail") or ""),
            "session_id": session_id,
            "entries": inspect_all_global_lifecycle_entries(),
        }

    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
        get_deployment_plan_context,
    )

    plan = get_deployment_plan_context(session_id=session_id)
    return {
        "ok": bool(plan and plan.get("repo")),
        "session_id": session_id,
        "lifecycle": materialized.get("lifecycle"),
        "plan_found": bool(plan and plan.get("repo")),
        "preflight_found": bool(materialized.get("preflight_found")),
        "simulation_found": bool(materialized.get("simulation_found")),
        "materialized": dict(materialized.get("materialized") or {}),
        "reason": "" if plan and plan.get("repo") else "plan_context_missing_after_repair",
        "detail": "" if plan and plan.get("repo") else "Repair wrote lifecycle artifacts but plan context is still missing.",
    }


def format_lifecycle_repair_report(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        reason = str(result.get("reason") or "repair failed")
        detail = str(result.get("detail") or "").strip()
        lines = [
            "Could not repair Railway deployment lifecycle.",
            "",
            f"Reason: {reason}",
        ]
        if detail:
            lines.append(f"Detail: {detail}")
        entries = list(result.get("entries") or [])
        if entries:
            lines.append("")
            lines.extend(format_global_lifecycle_entry_lines(entries))
        if reason == "stale_index":
            lines.extend(
                [
                    "This index is stale.",
                    "",
                    "Try:",
                    "`clear stale railway lifecycle index`",
                    "or recreate the lifecycle with deployment plan commands.",
                ]
            )
        elif reason == "readiness_only_no_plan":
            lines.extend(
                [
                    "",
                    "Readiness exists globally, but no deployment plan snapshot is stored yet.",
                    "Repair cannot recover a plan from readiness-only lifecycle data.",
                    "",
                    "Try:",
                    "`create railway deployment plan for <repo> in <project> / <environment>`",
                ]
            )
        elif reason == "plan_snapshot_missing":
            lines.extend(
                [
                    "",
                    "Try:",
                    "`create railway deployment plan for <repo> in <project> / <environment>`",
                    "`complete the railway deployment plan`",
                    "`confirm railway deployment plan`",
                ]
            )
        else:
            lines.extend(
                [
                    "",
                    "Try:",
                    "`show railway deployment lifecycle`",
                ]
            )
        lines.extend(["", "No mutation has been performed."])
        return "\n".join(lines)

    lifecycle = result.get("lifecycle") or {}
    repo = str(lifecycle.get("repo") or "—")
    project = str(lifecycle.get("project") or "—")
    environment = str(lifecycle.get("environment") or "—")
    materialized = dict(result.get("materialized") or {})
    return "\n".join(
        [
            "Repaired Railway deployment lifecycle.",
            "",
            f"Repo: `{repo}`",
            f"Project/environment: `{project}` / `{environment}`",
            "",
            "Materialized:",
            f"- deployment plan: **{'yes' if result.get('plan_found') else 'no'}**",
            f"- service creation preflight: **{'yes' if result.get('preflight_found') else 'no'}**",
            f"- simulation: **{'yes' if result.get('simulation_found') else 'no'}**",
            "",
            "Current session can now run:",
            "`simulate railway service creation`",
            "",
            "No mutation has been performed.",
        ]
    )
