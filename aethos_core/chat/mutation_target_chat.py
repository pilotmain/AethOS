# SPDX-License-Identifier: Apache-2.0
"""Mutation target resolution chat + job update flows."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.providers.railway.target_resolver import (
    TARGET_APPROVAL_THRESHOLD,
    resolve_railway_provider_target,
)
from aethos_core.runtime.authority import authority

_TARGET_UPDATE_RX = re.compile(
    r"\b(?:the\s+)?target\s+is\s+(.+)$|"
    r"\b(?:use|set)\s+(?:target|service)\s+(?:to\s+)?(.+)$",
    re.I,
)
_WHY_CANT_APPROVE_RX = re.compile(
    r"\bwhy\s+(?:can'?t|cannot)\s+i\s+approve\b|\bwhy\s+is\s+(?:it|this)\s+not\s+approvable\b",
    re.I,
)
_CREDENTIAL_GUIDANCE_RX = re.compile(
    r"\b("
    r"why\s+(?:can'?t|cannot)\s+i\s+approve"
    r"|why\s+is\s+(?:it|this)\s+not\s+approvable"
    r"|what\s+credential\s+(?:is\s+)?missing"
    r"|how\s+(?:do\s+i|to)\s+(?:fix|set\s*up|configure)\s+credentials?"
    r"|what\s+do\s+i\s+need\s+(?:to\s+)?restart"
    r")\b",
    re.I,
)
_JOB_ID_RX = re.compile(r"\b((?:job|dj)-[a-f0-9]+)\b", re.I)


def _format_candidates(candidates: list[dict[str, Any]]) -> str:
    if not candidates:
        return "No Railway service candidates are available yet."
    lines = []
    for idx, row in enumerate(candidates[:8], start=1):
        path = row.get("path")
        if path:
            lines.append(f"{idx}. {path}")
            continue
        name = row.get("service_name") or row.get("name") or "unknown"
        project = row.get("project_name")
        environment = row.get("environment") or "production"
        if project:
            lines.append(f"{idx}. {project} / {environment} / {name}")
        else:
            lines.append(f"{idx}. {name}")
    return "\n".join(lines)


def compose_railway_target_clarification(*, user_request: str, target_hints: list[str] | None = None) -> str | None:
    target = resolve_railway_provider_target(
        user_request=user_request,
        target_hints=target_hints,
        operation_type="restart",
    )
    if target.resolved and target.confidence >= TARGET_APPROVAL_THRESHOLD:
        return None
    if target.reason == "provider_inventory_unavailable":
        return (
            "I need to refresh Railway inventory before choosing a target.\n\n"
            "Say **What Railway services do I have?** or check **Provider status**, "
            "then tell me the exact service to restart.\n\n"
            "No mutation preflight has been created yet."
        )
    if target.reason in {"missing_target_phrase", "ambiguous_api_match", "ambiguous_inventory_match"}:
        op = "restart"
        if "redeploy" in user_request.lower():
            op = "redeploy"
        return (
            f"Which Railway service should I {op}?\n\n"
            f"I found these possible targets:\n{_format_candidates(target.candidates)}\n\n"
            "No mutation preflight has been created yet."
        )
    phrase = target.service_name or user_request
    return (
        f"I could not confirm a Railway service matching **{phrase}**.\n\n"
        "No restart preflight was created.\n\n"
        "Please choose a visible Railway service from **Provider status**, "
        "or tell me the exact Railway service name."
    )


def compose_target_update_reply(text: str, *, session_id: str = "default") -> tuple[str, str, dict[str, str]] | None:
    match = _TARGET_UPDATE_RX.search(text.strip())
    if not match:
        return None
    target_phrase = (match.group(1) or match.group(2) or "").strip().strip('"').strip("'")
    if not target_phrase:
        return None

    from aethos_core.runtime.jobs import job_store

    job_id_match = _JOB_ID_RX.search(text)
    job = None
    if job_id_match:
        job = job_store.get(job_id_match.group(1))
    if job is None:
        for row in job_store.list_all():
            if row.job_type != "mutation_preflight":
                continue
            if str(getattr(row, "session_id", "") or "") != session_id:
                continue
            status = str(row.params.get("preflight_status") or "")
            if status == "needs_information":
                job = row
                break
    if job is None:
        return (
            "I couldn't find a mutation preflight waiting for target resolution in this session.",
            "mutation_target_update",
            {},
        )

    target = resolve_railway_provider_target(user_request=f"Railway {target_phrase}", operation_type="restart")
    if not target.resolved or target.confidence < TARGET_APPROVAL_THRESHOLD:
        return (
            f"I couldn't confirm Railway service **{target_phrase}**.\n\n"
            f"{_format_candidates(target.candidates)}\n\n"
            "The preflight target was not updated.",
            "mutation_target_update",
            {"job_id": job.id},
        )

    job.params["target_name"] = target.service_name
    job.params["target"] = target.to_dict()
    job.params["target_resolved"] = True
    job.params["target_status"] = "resolved"
    from aethos_core.jobs.target_resolution import _apply_preflight_outcome

    _apply_preflight_outcome(job_id=job.id)

    return (
        f"Got it — I updated the preflight target to **{target.service_name}** and rechecked the restart plan.\n\n"
        f"The job is now ready for approval in **{mutation_approval_surface()}**.\n\n"
        "**No restart has been performed yet.**",
        "mutation_target_update",
        {"job_id": job.id, "service_name": str(target.service_name or "")},
    )


def compose_why_not_approvable_reply(text: str, *, session_id: str = "default") -> tuple[str, str, dict[str, str]] | None:
    if not _WHY_CANT_APPROVE_RX.search(text) and not _CREDENTIAL_GUIDANCE_RX.search(text):
        return None

    from aethos_core.credentials.credential_guidance import (
        compose_missing_credential_reply,
        find_latest_credential_blocked_preflight,
    )
    from aethos_core.jobs.job_approval_guidance import get_job_approval_guidance
    from aethos_core.runtime.jobs import job_store

    job_id_match = _JOB_ID_RX.search(text)
    job_id: str | None = job_id_match.group(1) if job_id_match else None
    preflight: dict[str, Any] | None = None

    if job_id:
        job = job_store.get(job_id)
        if not job:
            return None
        pf = dict(job.params.get("mutation_preflight") or {})
        preflight = {**pf, **dict(job.params or {})}
        preflight.setdefault("preflight_status", pf.get("preflight_status") or job.params.get("preflight_status"))
    else:
        latest = find_latest_credential_blocked_preflight(session_id=session_id)
        if latest:
            job_id, preflight = latest

    if preflight:
        status = str(preflight.get("preflight_status") or "")
        if status in ("needs_credential", "needs_credential_repair"):
            reply = (
                preflight.get("credential_requirements_reply")
                or compose_missing_credential_reply(preflight)
            )
            if reply:
                return (
                    reply,
                    "credential_requirement_guidance",
                    {"job_id": job_id or "", "preflight_status": status},
                )

    if not job_id:
        return None

    job = job_store.get(job_id)
    guidance = get_job_approval_guidance(job_id, session_id=session_id)
    if not job or not guidance.found:
        return None

    pf = dict(job.params.get("mutation_preflight") or {})
    status = str(job.params.get("preflight_status") or pf.get("preflight_status") or "")
    target_name = pf.get("target_name") or job.params.get("target_name")
    requested = str(job.params.get("user_request") or pf.get("user_request") or "")

    if status == "needs_information" or not target_name:
        phrase = extract_requested_service_phrase(requested)
        return (
            "The job is blocked because the Railway target is unresolved.\n\n"
            f"I know the requested operation is **restart on Railway**, but I could not confirm the exact service target"
            + (f' for **{phrase}**.' if phrase else ".")
            + "\n\n**No restart has been performed.**\n\n"
            f"To continue, resolve the target in **{mutation_approval_surface()}**, "
            "or tell me the exact Railway service name.",
            "mutation_target_blocked",
            {"job_id": job_id},
        )
    return None


def extract_requested_service_phrase(requested: str) -> str | None:
    from aethos_core.providers.railway.target_resolver import extract_railway_service_phrase

    return extract_railway_service_phrase(requested)


def gate_railway_mutation_preflight(
    *,
    text: str,
    params: dict[str, Any],
    operation_type: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (enriched params, clarification reply) — clarification blocks job creation."""
    if str(params.get("provider") or "") != "railway":
        return params, None
    if operation_type not in {"restart", "redeploy"}:
        return params, None
    if params.get("target_resolved") and params.get("target_name"):
        return params, None

    target = resolve_railway_provider_target(
        user_request=text,
        target_hints=list(params.get("target_hints") or []),
        operation_type=operation_type,
    )
    if target.resolved and target.confidence >= TARGET_APPROVAL_THRESHOLD:
        enriched = {
            **params,
            "target_name": target.service_name,
            "target": target.to_dict(),
            "target_resolved": True,
            "target_status": "resolved",
        }
        return enriched, None

    clarification = compose_railway_target_clarification(
        user_request=text,
        target_hints=list(params.get("target_hints") or []),
    )
    return None, clarification
