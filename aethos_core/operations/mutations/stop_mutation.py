# SPDX-License-Identifier: Apache-2.0
"""Cross-provider stop mutations — registry-first target resolution, governed preflights."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.operations.mutations.taxonomy import CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE
from aethos_core.runtime.authority import authority

_STOP_INTRO_RX = re.compile(
    r"\b(?:stop|shutdown|shut\s+down|kill|pause)\b(?:\s+the\s+following\s+(?:project|service|apps?|services?|projects?)?s?)?\s*[:\-]?\s*",
    re.I,
)
_NAME_TOKEN_RX = re.compile(r"^[a-z0-9][a-z0-9._-]{1,62}$", re.I)
_SKIP_TOKENS = frozenset(
    {
        "stop",
        "stopped",
        "stopping",
        "the",
        "following",
        "project",
        "projects",
        "service",
        "services",
        "please",
        "operational",
        "report",
        "did",
        "you",
        "were",
        "was",
        "have",
        "they",
        "any",
    }
)

_STOP_OUTCOME_RX = re.compile(
    r"^\s*(?:did|were|was|have)\s+(?:you|the|they|it|i)\b.*\bstop(?:ped|ping)?\b",
    re.I,
)


@dataclass
class StopTargetResolution:
    requested: str
    provider: str | None = None
    target_name: str | None = None
    status: str = "not_found"  # resolved | not_found | not_stoppable
    match_source: str | None = None
    suggestion: str | None = None
    detail: str | None = None


@dataclass
class StopBatchResolution:
    targets: list[StopTargetResolution] = field(default_factory=list)

    @property
    def resolved(self) -> list[StopTargetResolution]:
        return [row for row in self.targets if row.status == "resolved"]

    @property
    def suggested(self) -> list[StopTargetResolution]:
        return [row for row in self.targets if row.status == "suggested"]


def extract_stop_target_names(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    names: list[str] = []
    seen: set[str] = set()

    def add(name: str) -> None:
        cleaned = (name or "").strip().strip("`'\".,;")
        if not cleaned:
            return
        low = cleaned.lower()
        if low in _SKIP_TOKENS:
            return
        if not _NAME_TOKEN_RX.match(cleaned):
            return
        key = low.replace("-", "").replace("_", "")
        if key in seen:
            return
        seen.add(key)
        names.append(cleaned)

    body = _STOP_INTRO_RX.sub("", raw, count=1).strip() or raw
    for line in re.split(r"[\n,;]+", body):
        chunk = line.strip()
        if not chunk:
            continue
        for token in chunk.split():
            add(token)

    if not names:
        from aethos_core.operations.intents import extract_target_hints

        for hint in extract_target_hints(raw):
            add(hint)
    return names


def is_stop_outcome_question(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_STOP_OUTCOME_RX.search(raw))


def _to_stop_resolution(row: Any) -> StopTargetResolution:
    return StopTargetResolution(
        requested=row.requested,
        provider=row.provider,
        target_name=row.target_name,
        status=row.status,
        match_source=row.match_source,
        detail=row.detail,
    )


def resolve_stop_target(
    requested: str,
    *,
    preferred_provider: str = "",
    user_text: str = "",
) -> StopTargetResolution:
    from aethos_core.deployment_targets.mutation_resolver import resolve_mutation_target

    return _to_stop_resolution(
        resolve_mutation_target(requested, preferred_provider=preferred_provider, user_text=user_text)
    )


def resolve_stop_targets(
    names: list[str],
    *,
    preferred_provider: str = "",
    user_text: str = "",
) -> StopBatchResolution:
    return StopBatchResolution(
        targets=[
            resolve_stop_target(name, preferred_provider=preferred_provider, user_text=user_text)
            for name in names
        ]
    )


def compose_stop_mutation_preflight_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if is_stop_outcome_question(text):
        return None

    from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent

    intent = detect_explicit_mutation_intent(text, session_id=session_id)
    if intent is None or intent.operation != "stop":
        return None

    names = extract_stop_target_names(text)
    if len(names) <= 1 and intent.target_phrase:
        names = [intent.target_phrase]
    if not names:
        return None

    provider_hint = str(intent.provider or "").strip().lower()
    batch = resolve_stop_targets(names, preferred_provider=provider_hint, user_text=text)
    if not batch.resolved:
        lines = [
            "I couldn't resolve those names to registered deployment targets.",
            "",
            "**Requested:** " + ", ".join(f"`{n}`" for n in names),
            "",
            "Register each target in **Mission Control → Deployment Targets** "
            "(alias, default_provider, vercel_project or railway_service), then retry.",
            "",
            "No stop preflight has been created yet.",
        ]
        for row in batch.targets:
            if row.detail:
                lines.append(f"- {row.detail}")
        return ("\n".join(lines), "mutation_target_clarification", {"operation": "stop", "ambiguous": "true"})

    created: list[dict[str, Any]] = []
    notes: list[str] = []
    for row in batch.resolved:
        if not row.provider or not row.target_name:
            continue
        from aethos_core.deployment_targets.mutation_resolver import enrich_mutation_params, resolve_mutation_target

        resolution = resolve_mutation_target(row.requested, preferred_provider=provider_hint, user_text=text)
        params: dict[str, Any] = enrich_mutation_params(
            {
                "user_request": text,
                "provider": row.provider,
                "operation_type": "stop",
                "target_name": row.target_name,
                "target_hints": [row.requested],
                "session_id": session_id,
            },
            resolution,
        )
        if row.provider == "railway":
            from aethos_core.providers.railway.target_resolver import resolve_railway_provider_target

            railway = resolve_railway_provider_target(
                user_request=f"stop railway {params['target_name']}",
                target_hints=[row.requested, params["target_name"]],
                operation_type="stop",
            )
            if railway.resolved and railway.target:
                params["target"] = railway.target
                params["target_name"] = str(railway.target.get("service_name") or params["target_name"])

        job = authority.create_job(
            title=f"{row.provider.title()} stop mutation preflight — {params['target_name']}",
            job_type=CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
            params=params,
            source="chat",
            session_id=session_id,
            auto_run=True,
        )
        from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_preflight

        sync_thread_from_preflight(job=job, user_request=text)
        created.append({"job_id": job.id, "provider": row.provider, "target_name": params["target_name"]})

    if not created:
        return None

    approval_path = mutation_approval_surface()
    lines = [
        f"Prepared **{len(created)} governed stop preflight(s)** (**nothing has been stopped yet**).",
        "",
    ]
    for row in created:
        lines.append(f"- `{row['job_id']}` · **{row['provider']}** · `{row['target_name']}`")
    if notes:
        lines.append("")
        lines.extend(notes)
    lines.extend(
        [
            "",
            f"Review blast radius and rollback plan in **{approval_path}**, then approve each stop.",
            "",
            "**Stop** halts active compute: Railway `deploymentStop`; Vercel cancels in-flight builds "
            "or **pauses** live production (503). Use **restart**, **unpause**, or **redeploy** to bring it back.",
        ]
    )
    meta = {
        "proposed_job_id": created[0]["job_id"],
        "proposed_job_ids": ",".join(row["job_id"] for row in created),
        "proposed_job_type": CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
        "operation_type": "stop",
        "stop_preflight_count": str(len(created)),
    }
    return ("\n".join(lines), "mutation_preflight_job_created", meta)
