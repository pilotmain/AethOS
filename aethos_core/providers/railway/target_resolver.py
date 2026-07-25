# SPDX-License-Identifier: Apache-2.0
"""Railway service target resolution — aliases, inventory, and provider API."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

TARGET_APPROVAL_THRESHOLD = 0.75

_RAILWAY_SERVICE_PHRASE_RX = re.compile(
    r"\brailway\s+(?:the\s+)?((?:[a-z0-9][a-z0-9._-]*(?:\s+[a-z0-9][a-z0-9._-]*)*))(?:\s+service|\s+app|\s+project|\s+deployment)?\b",
    re.I,
)


@dataclass
class ProviderTarget:
    provider: str
    service_name: str | None = None
    project_name: str | None = None
    environment: str | None = None
    service_id: str | None = None
    confidence: float = 0.0
    resolved: bool = False
    candidates: list[dict[str, Any]] = field(default_factory=list)
    source: str = "unknown"
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "service_name": self.service_name,
            "project_name": self.project_name,
            "environment": self.environment,
            "service_id": self.service_id,
            "confidence": round(self.confidence, 3),
            "resolved": self.resolved,
            "candidates": list(self.candidates),
            "source": self.source,
            "reason": self.reason,
        }


def _aliases_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "provider_aliases" / "railway.json"


def load_railway_aliases() -> dict[str, dict[str, Any]]:
    path = _aliases_path()
    if not path.is_file():
        return {}
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return {}


def normalize_alias_key(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def extract_railway_service_phrase(user_request: str) -> str | None:
    from aethos_core.provider_discovery.target_resolution import extract_service_phrase

    phrase = extract_service_phrase(user_request)
    if phrase:
        return phrase
    raw = (user_request or "").strip()
    match = _RAILWAY_SERVICE_PHRASE_RX.search(raw)
    if not match:
        return None
    phrase = normalize_alias_key(match.group(1))
    skip = {"restart", "redeploy", "re deploy", "the", "my", "service", "app", "project"}
    tokens = [t for t in phrase.split() if t not in skip]
    if not tokens:
        return None
    return " ".join(tokens)


def _alias_match(phrase: str) -> ProviderTarget | None:
    aliases = load_railway_aliases()
    key = normalize_alias_key(phrase)
    if key in aliases:
        row = aliases[key]
        return ProviderTarget(
            provider="railway",
            service_name=str(row.get("service_name") or key),
            project_name=row.get("project_name"),
            environment=row.get("environment"),
            service_id=row.get("service_id"),
            confidence=0.95,
            resolved=True,
            source="alias_map",
        )
    for alias_key, row in aliases.items():
        if normalize_alias_key(alias_key) == key:
            return ProviderTarget(
                provider="railway",
                service_name=str(row.get("service_name") or alias_key),
                project_name=row.get("project_name"),
                environment=row.get("environment"),
                service_id=row.get("service_id"),
                confidence=0.94,
                resolved=True,
                source="alias_map",
            )
    compact = key.replace(" ", "-")
    compact_spaced = key.replace("-", " ")
    for variant in (compact, compact_spaced):
        if variant in aliases:
            row = aliases[variant]
            return ProviderTarget(
                provider="railway",
                service_name=str(row.get("service_name") or variant),
                project_name=row.get("project_name"),
                environment=row.get("environment"),
                service_id=row.get("service_id"),
                confidence=0.93,
                resolved=True,
                source="alias_map",
            )
    return None


def list_railway_inventory_services() -> list[dict[str, Any]]:
    from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory

    inventory = get_provider_inventory(provider="railway")
    if inventory.projects:
        return [
            {
                "service_name": row.get("service_name"),
                "project_name": row.get("project_name"),
                "environment": row.get("environment") or "production",
                "service_id": row.get("service_id"),
                "source": "provider_inventory",
                "path": f"{row.get('project_name')} / {row.get('environment')} / {row.get('service_name')}",
            }
            for row in inventory.all_services()
        ]

    from aethos_core.runtime.latest_inventory_store import get_latest_railway_inventory_job

    latest = get_latest_railway_inventory_job()
    if not latest:
        return []
    rows: list[dict[str, Any]] = []
    for row in (latest.get("services_by_name") or {}).values():
        name = str(row.get("name") or row.get("service_name") or "").strip()
        if not name:
            continue
        rows.append(
            {
                "service_name": name,
                "project_name": row.get("project_name"),
                "environment": row.get("environment") or "production",
                "service_id": row.get("service_id"),
                "source": "railway_inventory",
            }
        )
    return rows


def _discovery_match(phrase: str) -> ProviderTarget | None:
    from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory
    from aethos_core.provider_discovery.target_resolution import (
        TARGET_APPROVAL_THRESHOLD as DISCOVERY_THRESHOLD,
        resolve_target_from_inventory,
    )

    inventory = get_provider_inventory(provider="railway")
    resolution = resolve_target_from_inventory(inventory=inventory, user_request=f"Railway {phrase}", target_hints=[phrase])
    if resolution.resolved and resolution.confidence >= DISCOVERY_THRESHOLD:
        return ProviderTarget(
            provider="railway",
            service_name=resolution.service_name,
            project_name=resolution.project_name,
            environment=resolution.environment,
            service_id=resolution.service_id,
            confidence=resolution.confidence,
            resolved=True,
            candidates=resolution.candidates,
            source="provider_inventory",
        )
    if resolution.reason == "ambiguous_inventory_match":
        return ProviderTarget(
            provider="railway",
            confidence=0.0,
            resolved=False,
            candidates=resolution.candidates,
            source="provider_inventory",
            reason="ambiguous_inventory_match",
        )
    if resolution.reason == "provider_inventory_unavailable":
        return None
    if resolution.reason == "service_not_found":
        return ProviderTarget(
            provider="railway",
            service_name=phrase,
            confidence=0.0,
            resolved=False,
            candidates=resolution.candidates,
            source="provider_inventory",
            reason="service_not_found",
        )
    return None


def _memory_match(phrase: str) -> ProviderTarget | None:
    from aethos_core.operations.orchestration.provider_inference import find_target_in_operational_memory

    hit = find_target_in_operational_memory(phrase)
    if not hit:
        return None
    if hit.get("provider") != "railway":
        return None
    return ProviderTarget(
        provider="railway",
        service_name=str(hit.get("service_name") or hit.get("name") or phrase),
        project_name=hit.get("project_name"),
        service_id=hit.get("service_id"),
        confidence=0.91,
        resolved=True,
        source=str(hit.get("source") or "operational_memory"),
    )


def _inventory_match(phrase: str) -> ProviderTarget | None:
    norm = normalize_alias_key(phrase)
    matches: list[dict[str, Any]] = []
    for row in list_railway_inventory_services():
        name = normalize_alias_key(str(row.get("service_name") or ""))
        if name == norm:
            return ProviderTarget(
                provider="railway",
                service_name=row["service_name"],
                project_name=row.get("project_name"),
                environment=row.get("environment"),
                service_id=row.get("service_id"),
                confidence=0.92,
                resolved=True,
                source="railway_inventory",
            )
        if norm in name or name in norm:
            matches.append(row)
    if len(matches) == 1:
        row = matches[0]
        return ProviderTarget(
            provider="railway",
            service_name=row["service_name"],
            project_name=row.get("project_name"),
            environment=row.get("environment"),
            service_id=row.get("service_id"),
            confidence=0.86,
            resolved=True,
            candidates=matches,
            source="railway_inventory",
        )
    if len(matches) > 1:
        return ProviderTarget(
            provider="railway",
            confidence=0.0,
            resolved=False,
            candidates=matches,
            source="railway_inventory",
            reason="ambiguous_inventory_match",
        )
    return None


def _api_match(phrase: str) -> ProviderTarget | None:
    from aethos_core.providers.railway.auth import RailwayAuthAdapter
    from aethos_core.providers.railway.api_client import find_service_by_name, list_services

    auth = RailwayAuthAdapter().resolve_best_auth_method(operation="read_projects")
    if not auth.get("credential_id"):
        return ProviderTarget(
            provider="railway",
            confidence=0.0,
            resolved=False,
            source="provider_api",
            reason="provider_inventory_unavailable",
        )
    token = RailwayAuthAdapter().get_api_token(str(auth["credential_id"]))
    services = list_services(token)
    names = [str(s.get("service_name") or "") for s in services if s.get("service_name")]
    candidates = [
        {
            "service_name": str(s.get("service_name") or ""),
            "project_name": s.get("project_name"),
            "environment": s.get("environment") or "production",
            "service_id": s.get("service_id"),
            "source": "provider_api",
        }
        for s in services
        if s.get("service_name")
    ]
    if not phrase:
        if len(names) == 1:
            row = candidates[0]
            return ProviderTarget(
                provider="railway",
                service_name=row["service_name"],
                project_name=row.get("project_name"),
                environment=row.get("environment"),
                service_id=row.get("service_id"),
                confidence=0.80,
                resolved=True,
                candidates=candidates[:8],
                source="provider_api",
            )
        return ProviderTarget(
            provider="railway",
            confidence=0.0,
            resolved=False,
            candidates=candidates[:8],
            source="provider_api",
            reason="missing_target_phrase",
        )
    if find_service_by_name(token, phrase):
        for row in candidates:
            if normalize_alias_key(row["service_name"]) == normalize_alias_key(phrase):
                return ProviderTarget(
                    provider="railway",
                    service_name=row["service_name"],
                    project_name=row.get("project_name"),
                    environment=row.get("environment"),
                    service_id=row.get("service_id"),
                    confidence=0.90,
                    resolved=True,
                    candidates=candidates[:8],
                    source="provider_api",
                )
    partial = [
        row
        for row in candidates
        if phrase.lower() in row["service_name"].lower() or row["service_name"].lower() in phrase.lower()
    ]
    if len(partial) == 1:
        row = partial[0]
        return ProviderTarget(
            provider="railway",
            service_name=row["service_name"],
            project_name=row.get("project_name"),
            environment=row.get("environment"),
            service_id=row.get("service_id"),
            confidence=0.85,
            resolved=True,
            candidates=partial,
            source="provider_api",
        )
    if len(partial) > 1:
        return ProviderTarget(
            provider="railway",
            confidence=0.0,
            resolved=False,
            candidates=partial,
            source="provider_api",
            reason="ambiguous_api_match",
        )
    return ProviderTarget(
        provider="railway",
        service_name=phrase,
        confidence=0.0,
        resolved=False,
        candidates=candidates[:8],
        source="provider_api",
        reason="service_not_found",
    )


def resolve_railway_provider_target(
    *,
    user_request: str,
    target_hints: list[str] | None = None,
    operation_type: str = "restart",
) -> ProviderTarget:
    _ = operation_type
    from aethos_core.operations.intents import extract_target_hints

    phrase = extract_railway_service_phrase(user_request)
    hints = list(target_hints or []) + extract_target_hints(user_request)
    if not phrase and hints:
        phrase = hints[0]
    if phrase:
        for matcher in (_memory_match, _discovery_match, _alias_match, _inventory_match, _api_match):
            result = matcher(phrase)
            if result and result.resolved:
                return result
            if result and result.reason in {"ambiguous_inventory_match", "ambiguous_api_match"}:
                return result
        inv = _inventory_match(phrase)
        if inv and not inv.resolved and inv.candidates:
            return inv
        api = _api_match(phrase)
        if api:
            return api
        return ProviderTarget(
            provider="railway",
            service_name=phrase,
            confidence=0.0,
            resolved=False,
            candidates=api.candidates if api else [],
            source="provider_api",
            reason="service_not_found",
        )
    api = _api_match("")
    if api.reason == "provider_inventory_unavailable" and not list_railway_inventory_services():
        return api
    candidates = api.candidates or list_railway_inventory_services()
    if not candidates:
        return ProviderTarget(
            provider="railway",
            confidence=0.0,
            resolved=False,
            source="railway_inventory",
            reason="provider_inventory_unavailable",
        )
    return ProviderTarget(
        provider="railway",
        confidence=0.0,
        resolved=False,
        candidates=candidates[:8],
        source=api.source,
        reason="missing_target_phrase",
    )


def list_railway_target_candidates(*, limit: int = 20) -> list[dict[str, Any]]:
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for row in list_railway_inventory_services():
        name = str(row.get("service_name") or "")
        if name and name not in seen:
            seen.add(name)
            rows.append(row)
    if not rows:
        api = _api_match("")
        for row in list(api.candidates or []):
            name = str(row.get("service_name") or "")
            if name and name not in seen:
                seen.add(name)
                rows.append(row)
    return rows[:limit]
