# SPDX-License-Identifier: Apache-2.0
"""Unified mutation target resolution — registry first, exact inventory match only.

AethOS uses an explicit-config pattern (the deployment target registry) for all
governed mutations: stop, restart, redeploy, env — no fuzzy guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MutationTargetResolution:
    requested: str
    provider: str | None = None
    target_name: str | None = None
    status: str = "not_found"  # resolved | not_found | ambiguous
    match_source: str | None = None
    detail: str | None = None
    registry_row: dict[str, Any] | None = None
    candidates: list[dict[str, Any]] = field(default_factory=list)

    @property
    def resolved(self) -> bool:
        return self.status == "resolved" and bool(self.provider) and bool(self.target_name)


def _normalize_token(name: str) -> str:
    return (name or "").strip().lower().replace("_", "").replace("-", "")


def _from_registry_row(requested: str, row: dict[str, Any]) -> MutationTargetResolution:
    alias = str(row.get("alias") or requested)
    default_provider = str(row.get("default_provider") or "").strip().lower()
    railway_service = str(row.get("railway_service") or "").strip()
    vercel_project = str(row.get("vercel_project") or "").strip()
    railway_project = str(row.get("railway_project") or "").strip()

    if default_provider == "railway" or (railway_service and default_provider != "vercel"):
        target_name = railway_service or alias
        return MutationTargetResolution(
            requested=requested,
            provider="railway",
            target_name=target_name,
            status="resolved",
            match_source="deployment_target_registry",
            detail=f"Registry `{alias}` → Railway `{target_name}`.",
            registry_row=row,
        )

    if default_provider == "vercel" or vercel_project:
        target_name = vercel_project or alias
        return MutationTargetResolution(
            requested=requested,
            provider="vercel",
            target_name=target_name,
            status="resolved",
            match_source="deployment_target_registry",
            detail=f"Registry `{alias}` → Vercel `{target_name}`.",
            registry_row=row,
        )

    if railway_project:
        return MutationTargetResolution(
            requested=requested,
            provider="railway",
            target_name=alias,
            status="resolved",
            match_source="deployment_target_registry",
            detail=f"Registry `{alias}` → Railway project `{railway_project}`.",
            registry_row=row,
        )

    return MutationTargetResolution(
        requested=requested,
        status="not_found",
        match_source="deployment_target_registry",
        detail=(
            f"Registry target `{alias}` is missing `default_provider`, `vercel_project`, or `railway_service`. "
            "Register provider fields in Mission Control → Deployment Targets."
        ),
        registry_row=row,
    )


def _exact_vercel_project(requested: str) -> MutationTargetResolution | None:
    from aethos_core.operations.orchestration.provider_inference import find_target_in_vercel_inventory

    hit = find_target_in_vercel_inventory(requested)
    if not hit:
        return None
    name = str(hit.get("name") or requested)
    if _normalize_token(name) != _normalize_token(requested):
        return None
    return MutationTargetResolution(
        requested=requested,
        provider="vercel",
        target_name=name,
        status="resolved",
        match_source=str(hit.get("source") or "vercel_inventory_exact"),
    )


def _exact_railway_service(requested: str) -> MutationTargetResolution | None:
    from aethos_core.operations.orchestration.provider_inference import find_target_in_railway_inventory

    hit = find_target_in_railway_inventory(requested)
    if not hit or hit.get("provider") != "railway":
        return None
    name = str(hit.get("name") or hit.get("service_name") or requested)
    if _normalize_token(name) != _normalize_token(requested):
        return None
    return MutationTargetResolution(
        requested=requested,
        provider="railway",
        target_name=name,
        status="resolved",
        match_source=str(hit.get("source") or "railway_inventory_exact"),
    )


def resolve_mutation_target(
    requested: str,
    *,
    preferred_provider: str = "",
    user_text: str = "",
) -> MutationTargetResolution:
    """Resolve one mutation target. Registry wins; then exact provider inventory match."""
    from aethos_core.deployment_targets.registry import find_target_by_alias, match_aliases_in_text

    token = (requested or "").strip()
    if not token:
        return MutationTargetResolution(requested=requested, status="not_found", detail="Empty target name.")

    from aethos_core.chat.chat_intent_gate import token_is_safe_conversational

    if token_is_safe_conversational(token):
        return MutationTargetResolution(
            requested=token,
            status="not_found",
            detail="Conversational phrase — not a deployment target.",
        )

    row = find_target_by_alias(token)
    if row:
        resolved = _from_registry_row(token, row)
        if resolved.resolved:
            return resolved
        if resolved.detail:
            return resolved

    if user_text:
        alias_row = match_aliases_in_text(user_text)
        if alias_row and _normalize_token(str(alias_row.get("alias") or "")) == _normalize_token(token):
            resolved = _from_registry_row(token, alias_row)
            if resolved.resolved:
                return resolved

    provider_pref = (preferred_provider or "").strip().lower()
    if provider_pref == "vercel":
        vercel = _exact_vercel_project(token)
        if vercel:
            return vercel
    elif provider_pref == "railway":
        railway = _exact_railway_service(token)
        if railway:
            return railway
    else:
        vercel = _exact_vercel_project(token)
        if vercel:
            return vercel
        railway = _exact_railway_service(token)
        if railway:
            return railway

    return MutationTargetResolution(
        requested=token,
        status="not_found",
        detail=(
            f"`{token}` is not in the deployment target registry and has no exact match in connected "
            "Railway/Vercel inventory. Register it in Mission Control → Deployment Targets, then retry."
        ),
    )


def resolve_mutation_targets(
    names: list[str],
    *,
    preferred_provider: str = "",
    user_text: str = "",
) -> list[MutationTargetResolution]:
    return [
        resolve_mutation_target(name, preferred_provider=preferred_provider, user_text=user_text)
        for name in names
        if (name or "").strip()
    ]


def enrich_mutation_params(
    params: dict[str, Any],
    resolution: MutationTargetResolution,
) -> dict[str, Any]:
    """Attach registry metadata and resolved target fields to mutation job params."""
    if not resolution.resolved:
        return dict(params)

    out = dict(params)
    out["provider"] = resolution.provider
    out["target_name"] = resolution.target_name
    out["target"] = {
        "resolved": True,
        "service_name": resolution.target_name,
        "project_name": resolution.target_name,
    }
    out["target_hints"] = list(dict.fromkeys([*(out.get("target_hints") or []), resolution.requested]))
    if resolution.match_source:
        out["target_resolution_source"] = resolution.match_source
    row = resolution.registry_row
    if row:
        out["deployment_target_id"] = str(row.get("target_id") or "")
        out["deployment_target_alias"] = str(row.get("alias") or "")
        if str(row.get("vercel_project") or "").strip():
            out["vercel_project"] = str(row["vercel_project"]).strip()
        if str(row.get("railway_service") or "").strip():
            out["railway_service"] = str(row["railway_service"]).strip()
        if str(row.get("railway_project") or "").strip():
            out["railway_project"] = str(row["railway_project"]).strip()
        if str(row.get("railway_environment") or "").strip():
            out["railway_environment"] = str(row["railway_environment"]).strip()
    return out


def apply_target_resolution_to_params(
    params: dict[str, Any],
    *,
    user_text: str = "",
) -> tuple[dict[str, Any], MutationTargetResolution | None]:
    """Resolve target_name or first target_hint; return enriched params or original if unresolved."""
    hints = list(params.get("target_hints") or [])
    target_name = str(params.get("target_name") or "").strip()
    requested = target_name or (hints[0] if hints else "")
    if not requested:
        return dict(params), None

    provider = str(params.get("provider") or "").strip().lower()
    if provider in {"unknown", "auto", "cloud_provider_planned"}:
        provider = ""

    resolution = resolve_mutation_target(requested, preferred_provider=provider, user_text=user_text or str(params.get("user_request") or ""))
    if not resolution.resolved:
        return dict(params), resolution
    return enrich_mutation_params(params, resolution), resolution
