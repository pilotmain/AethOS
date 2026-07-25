# SPDX-License-Identifier: Apache-2.0
"""Dynamic target resolution from provider inventory."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.provider_discovery.provider_inventory import ProviderInventory
from aethos_core.provider_discovery.provider_topology import format_service_path
from aethos_core.provider_discovery.target_catalog import build_target_catalog, search_catalog

TARGET_APPROVAL_THRESHOLD = 0.75

_RESTART_TARGET_RX = re.compile(
    r"\b(?:restart|redeploy|re-?deploy)\s+(?:the\s+)?(?:railway\s+)?([a-z0-9][a-z0-9._-]*(?:\s+[a-z0-9][a-z0-9._-]*)*)(?:\s+service)?\b",
    re.I,
)
_RAILWAY_SERVICE_PHRASE_RX = re.compile(
    r"\brailway\s+(?:the\s+)?((?:[a-z0-9][a-z0-9._-]*(?:\s+[a-z0-9][a-z0-9._-]*)*))(?:\s+service|\s+app|\s+project|\s+deployment)?\b",
    re.I,
)
_WHY_FAILING_RX = re.compile(
    r"\bwhy\s+(?:is|did)\s+(?:the\s+)?(?:railway\s+)?([a-z0-9][a-z0-9._-]*(?:\s+[a-z0-9][a-z0-9._-]*)*)\s+(?:failing|fail|down)\b",
    re.I,
)


def normalize_target_phrase(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


@dataclass
class DynamicTargetResolution:
    provider: str
    resolved: bool = False
    confidence: float = 0.0
    service_name: str | None = None
    project_name: str | None = None
    environment: str | None = None
    service_id: str | None = None
    candidates: list[dict[str, Any]] = field(default_factory=list)
    reason: str | None = None
    source: str = "provider_inventory"

    def to_provider_target_dict(self) -> dict[str, Any]:
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


def extract_service_phrase(user_request: str) -> str | None:
    raw = (user_request or "").strip()
    path_match = re.search(
        r"\b([a-z0-9][a-z0-9._-]*(?:\s*/\s*[a-z0-9][a-z0-9._-]*){2,})\b",
        raw,
        re.I,
    )
    if path_match:
        return normalize_target_phrase(path_match.group(1).replace(" / ", " / "))
    for rx in (_RAILWAY_SERVICE_PHRASE_RX, _RESTART_TARGET_RX, _WHY_FAILING_RX):
        match = rx.search(raw)
        if match:
            phrase = normalize_target_phrase(match.group(1))
            skip = {
                "restart",
                "redeploy",
                "re deploy",
                "the",
                "my",
                "service",
                "app",
                "project",
                "railway",
                "happen",
                "happened",
                "happens",
                "actually",
                "really",
                "work",
                "worked",
                "succeed",
                "succeeded",
            }
            tokens = [t for t in phrase.split() if t not in skip]
            if tokens:
                return " ".join(tokens)
    return None


def resolve_target_from_inventory(
    *,
    inventory: ProviderInventory | None,
    user_request: str,
    target_hints: list[str] | None = None,
) -> DynamicTargetResolution:
    provider = str(getattr(inventory, "provider", None) or "railway")
    phrase = extract_service_phrase(user_request)
    hints = list(target_hints or [])
    if not phrase and hints:
        phrase = normalize_target_phrase(hints[0])

    if inventory is None or not inventory.projects:
        return DynamicTargetResolution(
            provider=provider,
            resolved=False,
            reason="provider_inventory_unavailable",
            source="provider_inventory",
        )

    catalog = build_target_catalog(inventory)
    if not phrase:
        return DynamicTargetResolution(
            provider=provider,
            resolved=False,
            candidates=[{**row, "service_name": row.get("service_name"), "path": row.get("path")} for row in catalog[:8]],
            reason="missing_target_phrase",
            source="provider_inventory",
        )

    matches = search_catalog(catalog, phrase=phrase)
    if not matches:
        return DynamicTargetResolution(
            provider=provider,
            service_name=phrase,
            resolved=False,
            candidates=catalog[:8],
            reason="service_not_found",
            source="provider_inventory",
        )

    if len(matches) == 1:
        row = matches[0]
        return DynamicTargetResolution(
            provider=provider,
            resolved=True,
            confidence=0.94,
            service_name=str(row.get("service_name") or ""),
            project_name=str(row.get("project_name") or ""),
            environment=str(row.get("environment") or "production"),
            service_id=str(row.get("service_id") or ""),
            candidates=[row],
            source="provider_inventory",
        )

    top = matches[0]
    if normalize_target_phrase(str(top.get("service_name") or "")) == normalize_target_phrase(phrase):
        unique_targets = {str(row.get("service_id") or row.get("path") or "") for row in matches[:6]}
        unique_targets.discard("")
        if len(unique_targets) <= 1:
            row = top
            return DynamicTargetResolution(
                provider=provider,
                resolved=True,
                confidence=0.92,
                service_name=str(row.get("service_name") or ""),
                project_name=str(row.get("project_name") or ""),
                environment=str(row.get("environment") or "production"),
                service_id=str(row.get("service_id") or ""),
                candidates=matches[:6],
                source="provider_inventory",
            )

    # Ambiguous when multiple distinct services score similarly
    distinct = {str(row.get("service_id") or row.get("path") or "") for row in matches[:6]}
    if len(distinct) > 1:
        candidates = []
        for row in matches[:6]:
            candidates.append(
                {
                    **row,
                    "service_name": row.get("service_name"),
                    "project_name": row.get("project_name"),
                    "environment": row.get("environment"),
                    "service_id": row.get("service_id"),
                    "path": row.get("path")
                    or format_service_path(
                        project=str(row.get("project_name") or ""),
                        environment=str(row.get("environment") or "production"),
                        service=str(row.get("service_name") or ""),
                    ),
                }
            )
        return DynamicTargetResolution(
            provider=provider,
            resolved=False,
            candidates=candidates,
            reason="ambiguous_inventory_match",
            source="provider_inventory",
        )

    row = top
    return DynamicTargetResolution(
        provider=provider,
        resolved=True,
        confidence=0.88,
        service_name=str(row.get("service_name") or ""),
        project_name=str(row.get("project_name") or ""),
        environment=str(row.get("environment") or "production"),
        service_id=str(row.get("service_id") or ""),
        candidates=matches[:6],
        source="provider_inventory",
    )
