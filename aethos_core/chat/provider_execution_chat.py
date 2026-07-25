# SPDX-License-Identifier: Apache-2.0
"""Provider execution chat — logs, diagnosis, fix plans, operation truth."""

from __future__ import annotations

import re

from aethos_core.mission_control.visible_navigation_registry import resolve_visible_navigation_path, INTERNAL_SURFACE_MUTATION_APPROVAL

_LOGS_RX = re.compile(r"\b(check\s+logs|show\s+logs|read\s+logs|what\s+do\s+the\s+logs\s+say)\b", re.I)
_WHY_FAIL_RX = re.compile(r"\b(why\s+(?:did\s+it\s+fail|is\s+.+\s+failing|didn't\s+it\s+work)|why\s+is\s+.+\s+(?:down|unhealthy|failing))\b", re.I)
_FIX_RX = re.compile(r"\b(can\s+you\s+fix\s+it|fix\s+it|apply\s+(?:the\s+)?fix)\b", re.I)
_REDEPLOY_RX = re.compile(r"\b(redeploy\s+(?:the\s+)?(?:railway\s+)?|redeploy\s+it)\b", re.I)
_WHAT_CHANGED_RX = re.compile(r"\b(what\s+changed|what\s+happened\s+after\s+(?:approval|redeploy|restart))\b", re.I)


def is_provider_execution_intent(text: str) -> bool:
    t = text or ""
    return bool(
        _LOGS_RX.search(t)
        or _WHY_FAIL_RX.search(t)
        or _FIX_RX.search(t)
        or _REDEPLOY_RX.search(t)
        or _WHAT_CHANGED_RX.search(t)
    )


def _runtime_path() -> str:
    return resolve_visible_navigation_path(internal_surface=INTERNAL_SURFACE_MUTATION_APPROVAL, mode="operator")


def _latest_railway_execution(session_id: str):
    from aethos_core.runtime.jobs import job_store

    for row in reversed(job_store.list_all()):
        if row.job_type != "mutation_execution":
            continue
        if str(getattr(row, "session_id", "") or "") != session_id:
            continue
        if str(row.params.get("provider") or "") == "railway":
            return row
    return None


def compose_provider_execution_reply(text: str, *, session_id: str = "default") -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if master_router_has_priority_route(text, session_id=session_id):
        return None

    if not is_provider_execution_intent(text):
        return None

    job = _latest_railway_execution(session_id)
    if job is None and (
        _LOGS_RX.search(text) or _WHY_FAIL_RX.search(text) or _FIX_RX.search(text) or _WHAT_CHANGED_RX.search(text)
    ):
        return None
    if job is None:
        return (
            f"I couldn't find a Railway execution job in this session yet. Check **{_runtime_path()}**.",
            "provider_execution",
            {},
        )

    target = str(job.params.get("target_name") or "unknown")
    bundle = job.params.get("provider_evidence_bundle") or {}
    if not isinstance(bundle, dict):
        exec_art = job.params.get("mutation_execution") or {}
        bundle = exec_art.get("provider_evidence_bundle") if isinstance(exec_art, dict) else {}
    if not isinstance(bundle, dict):
        bundle = {}

    if _LOGS_RX.search(text):
        logs = bundle.get("logs_excerpt") or []
        if logs:
            tail = logs[-3:]
            lines = [f"- {str(row.get('message') or row.get('msg') or row)[:200]}" for row in tail]
            return (
                f"Recent Railway logs for **{target}**:\n\n" + "\n".join(lines) + f"\n\nReview full evidence in **{_runtime_path()}**.",
                "provider_execution_logs",
                {"job_id": job.id},
            )
        return (
            f"I don't have Railway log excerpts stored for **{target}** yet. Try again after execution completes or use diagnostics.\n\n"
            f"Job `{job.id}` in **{_runtime_path()}**.",
            "provider_execution_logs",
            {"job_id": job.id},
        )

    if _WHY_FAIL_RX.search(text):
        from aethos_core.provider_skills.runtime import diagnose_provider_job

        diag = diagnose_provider_job(job_id=job.id)
        diagnosis = diag.get("diagnosis") or {}
        if diagnosis.get("ok"):
            return (
                f"The service is running, but logs indicate **{diagnosis.get('summary')}** for **{target}**.\n\n"
                f"Most likely cause: {diagnosis.get('likely_cause')}\n\n"
                "I can prepare a governed fix plan — approval is required before any mutation.",
                "provider_execution_diagnosis",
                {"job_id": job.id, "category": str(diagnosis.get("category") or "")},
            )
        return (
            f"I couldn't diagnose **{target}** yet — log evidence is insufficient. Check **{_runtime_path()}** for execution artifacts.",
            "provider_execution_diagnosis",
            {"job_id": job.id},
        )

    if _FIX_RX.search(text):
        from aethos_core.provider_skills.runtime import fix_plan_for_job

        plan = fix_plan_for_job(job_id=job.id)
        fix = plan.get("fix_plan") or {}
        if fix.get("ok"):
            changes = fix.get("proposed_changes") or []
            change_lines = "\n".join(f"- {c}" for c in changes[:5])
            return (
                f"I've prepared a governed fix plan for **{target}**:\n\n{fix.get('summary')}\n\n{change_lines}\n\n"
                "**Approval is required before I apply any mutation.** "
                f"Review in **{_runtime_path()}** or approve a new governed preflight.",
                "provider_execution_fix_plan",
                {"job_id": job.id},
            )
        return (
            f"I can't propose a fix for **{target}** without stronger log evidence. Ask **why is the api failing?** first.",
            "provider_execution_fix_plan",
            {"job_id": job.id},
        )

    if _REDEPLOY_RX.search(text):
        return (
            f"Redeploy requires a governed preflight and approval for **{target}**.\n\n"
            "Say **Redeploy the Railway atlas-trader api service** to create a preflight, then approve in "
            f"**{_runtime_path()}**. Redeploy verification requires new deployment evidence.",
            "provider_execution_redeploy",
            {"job_id": job.id},
        )

    if _WHAT_CHANGED_RX.search(text):
        verification = bundle.get("verification") or {}
        evidence = bundle.get("evidence") or {}
        command = bundle.get("command") or job.params.get("command") or "unknown"
        return (
            f"Provider command: `{command}`\n\n"
            f"Command submitted: **{bundle.get('command_submitted', job.params.get('restart_command_submitted'))}**\n"
            f"Log activity after approval: **{evidence.get('log_activity_after_approval', False)}**\n"
            f"Deployment transition: **{evidence.get('deployment_transition_detected', False)}**\n"
            f"Health confirmed: **{evidence.get('health_confirmed', False)}**\n"
            f"Verification: **{verification.get('status') or job.params.get('restart_verification_state')}**\n\n"
            f"Full evidence: job `{job.id}` in **{_runtime_path()}**.",
            "provider_execution_changes",
            {"job_id": job.id},
        )

    return None
