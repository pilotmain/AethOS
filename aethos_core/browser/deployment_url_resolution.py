# SPDX-License-Identifier: Apache-2.0
"""Canonical public deployment URL resolution — no guessed domains."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

_DEPLOYMENT_EVIDENCE_RX = re.compile(
    r"\b(capture|take|show)\b.*\b(deployment\s+evidence|browser\s+evidence)\b|"
    r"\bdeployment\s+evidence\b",
    re.I,
)


@dataclass
class DeploymentUrlResolution:
    resolved: bool
    provider: str
    target: str
    public_url: str | None = None
    resolution_source: str | None = None
    fallback_available: bool = False
    failure_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolved": self.resolved,
            "provider": self.provider,
            "target": self.target,
            "public_url": self.public_url,
            "resolution_source": self.resolution_source,
            "fallback_available": self.fallback_available,
            "failure_reason": self.failure_reason,
            "metadata": dict(self.metadata),
        }


def is_deployment_evidence_prompt(text: str) -> bool:
    return bool(_DEPLOYMENT_EVIDENCE_RX.search((text or "").strip()))


def is_guessed_service_com_url(url: str, target: str) -> bool:
    host = urlparse(url).netloc.lower()
    slug = (target or "").strip().lower().replace("_", "-")
    if not slug or not host:
        return False
    return host == f"{slug}.com" or host == f"www.{slug}.com"


def normalize_public_url(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    if text.startswith(("http://", "https://")):
        return text
    if "." in text and " " not in text:
        return f"https://{text}"
    return ""


def _looks_like_railway_public_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return bool(host) and ("up.railway.app" in host or host.endswith(".railway.app"))


def _service_row_from_inventory(target: str, inventory_context: dict[str, Any] | None) -> dict[str, Any] | None:
    if inventory_context and isinstance(inventory_context.get("service"), dict):
        return inventory_context["service"]
    from aethos_core.operations.orchestration.provider_inference import find_target_in_railway_inventory

    hit = find_target_in_railway_inventory(target)
    if not hit:
        return None
    return hit


def _railway_token() -> str | None:
    from aethos_core.operations.orchestration.provider_runtime import get_provider_api_token, resolve_execution_auth

    auth = resolve_execution_auth(provider="railway", operation_type="read_projects", params={})
    token = get_provider_api_token(provider="railway", auth=auth)
    return token or None


def _resolve_railway_public_url(*, target: str, inventory_context: dict[str, Any] | None) -> DeploymentUrlResolution:
    row = _service_row_from_inventory(target, inventory_context) or {}
    metadata: dict[str, Any] = {
        "service_id": row.get("service_id"),
        "service_name": row.get("service_name") or row.get("name") or target,
        "project_name": row.get("project_name"),
        "domains": list(row.get("domains") or []),
    }
    token = _railway_token()
    candidates: list[tuple[str, str]] = []

    for domain in metadata.get("domains") or []:
        url = normalize_public_url(str(domain))
        if url and not is_guessed_service_com_url(url, target):
            candidates.append((url, "railway_custom_domain"))

    for key in ("public_url", "url", "production_url"):
        url = normalize_public_url(str(row.get(key) or ""))
        if url and not is_guessed_service_com_url(url, target):
            source = "railway_service_domain" if _looks_like_railway_public_url(url) else "railway_inventory_url"
            candidates.append((url, source))

    service_id = str(row.get("service_id") or "")
    if token and service_id:
        from aethos_core.providers.railway.api_client import list_service_deployments

        deployments = list_service_deployments(token, service_id=service_id, limit=5)
        metadata["deployments"] = deployments[:5]
        metadata["latest_deployment_state"] = (
            str(deployments[0].get("state") or "") if deployments else None
        )
        for dep in deployments:
            url = normalize_public_url(str(dep.get("url") or ""))
            if url and not is_guessed_service_com_url(url, target):
                candidates.append((url, "railway_deployment_url"))
    elif service_id:
        metadata["deployments"] = metadata.get("deployments") or []

    if not row and token:
        from aethos_core.providers.railway.api_client import find_service_by_name, list_service_deployments

        live = find_service_by_name(token, target)
        if live:
            metadata.update(
                {
                    "service_id": live.get("service_id"),
                    "service_name": live.get("service_name"),
                    "project_name": live.get("project_name"),
                }
            )
            deployments = list_service_deployments(token, service_id=str(live.get("service_id") or ""), limit=5)
            metadata["deployments"] = deployments[:5]
            for dep in deployments:
                url = normalize_public_url(str(dep.get("url") or ""))
                if url and not is_guessed_service_com_url(url, target):
                    candidates.append((url, "railway_deployment_url"))

    for url, source in candidates:
        if url:
            return DeploymentUrlResolution(
                resolved=True,
                provider="railway",
                target=target,
                public_url=url,
                resolution_source=source,
                fallback_available=True,
                metadata=metadata,
            )

    return DeploymentUrlResolution(
        resolved=False,
        provider="railway",
        target=target,
        fallback_available=True,
        failure_reason="no_public_url",
        metadata=metadata,
    )


def _resolve_vercel_public_url(*, target: str, inventory_context: dict[str, Any] | None) -> DeploymentUrlResolution:
    from aethos_core.runtime.latest_inventory_store import get_latest_project_state

    state = (inventory_context or {}).get("project") if inventory_context else None
    if not state:
        state = get_latest_project_state(target) or {}
    url = normalize_public_url(str(state.get("production_url") or ""))
    metadata = {
        "project_name": state.get("name") or target,
        "production_url_source": state.get("production_url_source"),
        "latest_deployment_state": state.get("latest_deployment_state"),
        "operator_status": state.get("operator_status"),
    }
    if url and not is_guessed_service_com_url(url, target):
        return DeploymentUrlResolution(
            resolved=True,
            provider="vercel",
            target=target,
            public_url=url,
            resolution_source=str(state.get("source") or "vercel_production_url"),
            fallback_available=True,
            metadata=metadata,
        )
    return DeploymentUrlResolution(
        resolved=False,
        provider="vercel",
        target=target,
        fallback_available=True,
        failure_reason="no_public_url",
        metadata=metadata,
    )


def resolve_public_deployment_url(
    *,
    provider: str,
    target: str,
    inventory_context: dict[str, Any] | None = None,
) -> DeploymentUrlResolution:
    normalized_target = (target or "").strip()
    normalized_provider = (provider or "").strip().lower()
    if not normalized_target:
        return DeploymentUrlResolution(
            resolved=False,
            provider=normalized_provider or "unknown",
            target="",
            failure_reason="missing_target",
            fallback_available=False,
        )

    if normalized_provider == "railway":
        return _resolve_railway_public_url(target=normalized_target, inventory_context=inventory_context)
    if normalized_provider == "vercel":
        return _resolve_vercel_public_url(target=normalized_target, inventory_context=inventory_context)

    from aethos_core.operations.orchestration.provider_inference import infer_provider_for_hints

    inferred = infer_provider_for_hints([normalized_target])
    if inferred.get("status") == "resolved":
        return resolve_public_deployment_url(
            provider=str(inferred.get("provider") or ""),
            target=str(inferred.get("target_name") or normalized_target),
            inventory_context=inventory_context,
        )
    if inferred.get("status") == "ambiguous":
        return DeploymentUrlResolution(
            resolved=False,
            provider="unknown",
            target=normalized_target,
            failure_reason="ambiguous_provider",
            fallback_available=False,
            metadata={"matches": inferred.get("matches") or []},
        )
    return DeploymentUrlResolution(
        resolved=False,
        provider=normalized_provider or "unknown",
        target=normalized_target,
        failure_reason="provider_unknown",
        fallback_available=True,
        metadata={},
    )


def resolve_deployment_evidence_target(text: str) -> tuple[str, str] | None:
    """Return (provider, target) for deployment evidence prompts."""
    from aethos_core.operations.intents import extract_target_hints
    from aethos_core.operations.orchestration.provider_inference import infer_provider_for_hints

    hints = extract_target_hints(text)
    if not hints:
        return None
    target = hints[0]
    inferred = infer_provider_for_hints(hints)
    if inferred.get("status") == "resolved":
        return str(inferred.get("provider") or ""), str(inferred.get("target_name") or target)
    if inferred.get("status") == "ambiguous":
        return None
    return "unknown", target
