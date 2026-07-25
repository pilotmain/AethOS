# SPDX-License-Identifier: Apache-2.0
"""Canonical source binding resolution — single source of truth for service → repo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.provider_topology.source_binding import SourceBinding
from aethos_core.provider_topology.topology_memory import get_binding, get_cached_graph


@dataclass
class SourceBindingResolution:
    provider: str
    project: str
    environment: str
    service_name: str
    github_repo: str | None = None
    verified: bool = False
    resolution_source: str = "none"
    service_id: str | None = None
    binding_key: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "project": self.project,
            "environment": self.environment,
            "service_name": self.service_name,
            "github_repo": self.github_repo,
            "verified": self.verified,
            "resolution_source": self.resolution_source,
            "service_id": self.service_id,
            "binding_key": self.binding_key,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SourceBindingResolution:
        return cls(
            provider=str(raw.get("provider") or "railway"),
            project=str(raw.get("project") or raw.get("project_name") or ""),
            environment=str(raw.get("environment") or "production"),
            service_name=str(raw.get("service_name") or raw.get("service") or ""),
            github_repo=raw.get("github_repo") or raw.get("repo"),
            verified=bool(raw.get("verified", False)),
            resolution_source=str(raw.get("resolution_source") or "none"),
            service_id=raw.get("service_id"),
            binding_key=str(raw.get("binding_key") or ""),
        )


@dataclass
class StaleBindingRegression:
    confirmed_repo: str
    attempted_repo: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "confirmed_repo": self.confirmed_repo,
            "attempted_repo": self.attempted_repo,
        }


def resolve_source_binding_for_service(
    *,
    provider: str,
    project: str,
    environment: str,
    service: str,
    service_id: str | None = None,
    session_id: str | None = None,
    job_params: dict[str, Any] | None = None,
    refresh: bool = False,
) -> SourceBindingResolution:
    provider = (provider or "railway").strip().lower()
    project = (project or "").strip()
    environment = (environment or "production").strip()
    service = (service or "").strip()
    job_params = dict(job_params or {})

    resolution = SourceBindingResolution(
        provider=provider,
        project=project,
        environment=environment,
        service_name=service,
        service_id=service_id,
    )

    confirmed = get_binding(provider=provider, project=project, environment=environment, service_name=service)
    if confirmed is not None and confirmed.github_repo and confirmed.source_verified:
        return _from_binding(confirmed, resolution_source="confirmed_binding")

    if session_id:
        pending_repo = _pending_action_repo(session_id=session_id, provider=provider, project=project, service=service)
        if pending_repo:
            resolution.github_repo = pending_repo
            resolution.verified = True
            resolution.resolution_source = "pending_action"
            resolution.binding_key = confirmed.key if confirmed else _binding_key(provider, project, environment, service)
            if confirmed and confirmed.service_id:
                resolution.service_id = confirmed.service_id
            return resolution

        pending_correction = _pending_correction_repo(session_id=session_id, provider=provider, project=project, service=service)
        if pending_correction:
            resolution.github_repo = pending_correction
            resolution.verified = True
            resolution.resolution_source = "pending_correction"
            resolution.binding_key = confirmed.key if confirmed else _binding_key(provider, project, environment, service)
            if confirmed and confirmed.service_id:
                resolution.service_id = confirmed.service_id
            return resolution

    if refresh and confirmed is not None and confirmed.github_repo:
        return _from_binding(confirmed, resolution_source="confirmed_binding")

    if confirmed is not None and confirmed.github_repo:
        return _from_binding(confirmed, resolution_source="confirmed_binding")

    graph_repo = _topology_graph_repo(provider=provider, project=project, environment=environment, service=service)
    if graph_repo:
        resolution.github_repo = graph_repo
        resolution.resolution_source = "topology_graph"
        resolution.binding_key = _binding_key(provider, project, environment, service)
        if confirmed and confirmed.service_id:
            resolution.service_id = confirmed.service_id
        return resolution

    inventory_binding = _inventory_binding(provider=provider, project=project, environment=environment, service=service)
    if inventory_binding is not None:
        if inventory_binding.github_repo:
            return _from_binding(inventory_binding, resolution_source="inventory")
        if inventory_binding.service_id:
            resolution.service_id = inventory_binding.service_id
            resolution.resolution_source = "inventory"
            resolution.binding_key = inventory_binding.key
            return resolution

    explicit = str(job_params.get("source_binding") or "").strip()
    if explicit:
        resolution.github_repo = explicit
        resolution.resolution_source = "explicit_param"
        resolution.verified = bool((job_params.get("source_binding_resolution") or {}).get("verified"))
        resolution.binding_key = _binding_key(provider, project, environment, service)
        if confirmed and confirmed.service_id:
            resolution.service_id = confirmed.service_id
        return resolution

    legacy = _legacy_repo_from_params(job_params)
    if legacy:
        resolution.github_repo = legacy
        resolution.resolution_source = "legacy_fallback"
        resolution.binding_key = _binding_key(provider, project, environment, service)
        if confirmed and confirmed.service_id:
            resolution.service_id = confirmed.service_id
        return resolution

    if confirmed is not None:
        return _from_binding(confirmed, resolution_source="confirmed_binding")

    resolution.binding_key = _binding_key(provider, project, environment, service)
    return resolution


def check_stale_binding_regression(
    resolution: SourceBindingResolution,
    attempted_repo: str | None,
) -> StaleBindingRegression | None:
    if not resolution.github_repo or not resolution.verified:
        return None
    attempted = (attempted_repo or "").strip()
    if not attempted:
        return None
    if attempted.lower() == resolution.github_repo.lower():
        return None
    return StaleBindingRegression(
        confirmed_repo=resolution.github_repo,
        attempted_repo=attempted,
    )


def compose_stale_binding_regression_reply(regression: StaleBindingRegression) -> str:
    return (
        "Blocked stale source binding regression.\n\n"
        "Confirmed binding:\n"
        f"- **{regression.confirmed_repo}**\n\n"
        "Attempted stale binding:\n"
        f"- **{regression.attempted_repo}**\n\n"
        "I refreshed the job context. Please retry the governed preflight."
    )


def attach_resolved_binding_to_params(
    params: dict[str, Any],
    resolution: SourceBindingResolution,
) -> dict[str, Any]:
    params = dict(params)
    if resolution.github_repo:
        params["source_binding"] = resolution.github_repo
    params["source_binding_resolution"] = resolution.to_dict()
    target = dict(params.get("target") or {})
    if resolution.service_id and not target.get("service_id"):
        target["service_id"] = resolution.service_id
    if target:
        params["target"] = target
    return params


def refresh_params_source_binding(
    params: dict[str, Any],
    *,
    session_id: str | None = None,
    block_stale_regression: bool = False,
) -> tuple[dict[str, Any], SourceBindingResolution, StaleBindingRegression | None]:
    target = dict(params.get("target") or {})
    provider = str(params.get("provider") or "railway")
    project = str(target.get("project_name") or params.get("project_name") or "")
    environment = str(target.get("environment") or params.get("environment") or "production")
    service = str(params.get("target_name") or target.get("service_name") or "")
    attempted = str(params.get("source_binding") or "")
    prior_resolution = params.get("source_binding_resolution")
    if isinstance(prior_resolution, dict):
        attempted = attempted or str(prior_resolution.get("github_repo") or "")

    resolution = resolve_source_binding_for_service(
        provider=provider,
        project=project,
        environment=environment,
        service=service,
        service_id=target.get("service_id"),
        session_id=session_id,
        job_params=params,
        refresh=True,
    )
    regression = check_stale_binding_regression(resolution, attempted or None) if block_stale_regression else None
    refreshed = attach_resolved_binding_to_params(params, resolution)
    return refreshed, resolution, regression


def _from_binding(binding: SourceBinding, *, resolution_source: str) -> SourceBindingResolution:
    return SourceBindingResolution(
        provider=binding.provider,
        project=binding.project,
        environment=binding.environment,
        service_name=binding.service_name,
        github_repo=binding.github_repo,
        verified=bool(binding.source_verified),
        resolution_source=resolution_source,
        service_id=binding.service_id,
        binding_key=binding.key,
    )


def _binding_key(provider: str, project: str, environment: str, service: str) -> str:
    from aethos_core.provider_topology.source_binding import binding_key

    return binding_key(provider=provider, project=project, environment=environment, service_name=service)


def _pending_action_repo(*, session_id: str, provider: str, project: str, service: str) -> str | None:
    from aethos_core.task_frame.pending_action import get_pending_action

    action = get_pending_action(session_id=session_id)
    if action is None:
        return None
    if action.provider != provider:
        return None
    if action.project != project or action.service != service:
        return None
    repo = str(action.source_binding or "").strip()
    return repo or None


def _pending_correction_repo(*, session_id: str, provider: str, project: str, service: str) -> str | None:
    from aethos_core.provider_topology.binding_update_flow import get_pending_correction

    pending = get_pending_correction(session_id=session_id)
    if pending is None:
        return None
    if pending.provider != provider or pending.project != project or pending.service_name != service:
        return None
    if not pending.access_verified:
        return None
    return str(pending.new_repo or "").strip() or None


def _topology_graph_repo(*, provider: str, project: str, environment: str, service: str) -> str | None:
    key = _binding_key(provider, project, environment, service)
    graph = get_cached_graph(key)
    if graph is None:
        return None
    repo = getattr(graph, "github_repo", None)
    return str(repo).strip() if repo else None


def _inventory_binding(*, provider: str, project: str, environment: str, service: str) -> SourceBinding | None:
    from aethos_core.provider_topology.topology_refresh import _binding_from_inventory

    return _binding_from_inventory(provider=provider, project=project, environment=environment, service_name=service)


def _legacy_repo_from_params(params: dict[str, Any]) -> str | None:
    for key in ("legacy_source_binding", "stored_github_repo"):
        val = str(params.get(key) or "").strip()
        if val and "/" in val:
            return val
    artifact = dict(params.get("mutation_execution") or {})
    for source in (artifact, params):
        err = str(source.get("error") or source.get("detail") or "")
        if "repo:" in err.lower():
            import re

            match = re.search(r"repo:\s*([a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*)", err, re.I)
            if match:
                return match.group(1)
    return None
