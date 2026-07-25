# SPDX-License-Identifier: Apache-2.0
"""Resolve operational targets from Vercel memory and user hints."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.operations.vercel_operation_capabilities import (
    browser_runtime_required,
    is_api_capable,
)
from aethos_core.runtime.operational_memory import operational_memory


@dataclass
class TargetResolution:
    status: str  # resolved | ambiguous | missing | blocked_by_browser_runtime | not_applicable
    target_name: str | None = None
    matches: list[str] = field(default_factory=list)
    memory: dict[str, Any] | None = None
    message: str = ""
    source: str = "memory"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "target_name": self.target_name,
            "matches": list(self.matches),
            "memory": dict(self.memory) if self.memory else None,
            "message": self.message,
            "source": self.source,
        }


def _normalize(name: str) -> str:
    return (name or "").strip().lower().replace("_", "-")


def _score_match(hint: str, known: str) -> int:
    h = _normalize(hint)
    k = _normalize(known)
    if not h or not k:
        return 0
    if h == k:
        return 100
    if h in k or k in h:
        return 80
    h_parts = set(h.split("-"))
    k_parts = set(k.split("-"))
    overlap = len(h_parts & k_parts)
    if overlap:
        return 50 + overlap * 10
    return 0


def _extract_token_candidates(text: str, known: set[str]) -> list[str]:
    raw = (text or "").lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9._-]{2,48}", raw)
    hits: list[tuple[int, str]] = []
    for t in tokens:
        if t in {"vercel", "redeploy", "restart", "deployment", "application", "service", "domains", "domain"}:
            continue
        for k in known:
            sc = _score_match(t, k)
            if sc >= 50:
                hits.append((sc, k))
    hits.sort(key=lambda x: (-x[0], x[1]))
    out: list[str] = []
    seen: set[str] = set()
    for _, name in hits:
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def _collect_target_hints(*, user_request: str, target_hints: list[str] | None) -> list[str]:
    from aethos_core.operations.intents import extract_target_hints

    hints: list[str] = []
    seen: set[str] = set()
    for h in list(target_hints or []) + extract_target_hints(user_request):
        key = _normalize(h)
        if key and key not in seen:
            seen.add(key)
            hints.append(h.strip())
    return hints


def _memory_from_api_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(record.get("name") or "").lower(),
        "production_url": record.get("production_url"),
        "known_repo": record.get("repo_link"),
        "known_domains": list(record.get("domains") or []),
        "latest_deployment_state": record.get("latest_production_state") or "unknown",
        "latest_deployment_scope": "production",
        "last_health": record.get("latest_production_state") or "unknown",
        "evidence": ["source:vercel_api", f"api_project_id:{record.get('id')}"],
        "resolution_source": "provider_api",
    }


def _resolve_via_api(
    *,
    user_request: str,
    target_hints: list[str] | None,
) -> TargetResolution | None:
    from aethos_core.providers.vercel.api_client import find_project_by_name, parse_project_record
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    resolved_auth = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
    if resolved_auth.get("method") != "api_token":
        return None
    credential_id = str(resolved_auth.get("credential_id") or "")
    token = VercelAuthAdapter().get_api_token(credential_id)
    if not token:
        return None

    hints = _collect_target_hints(user_request=user_request, target_hints=target_hints)
    if not hints:
        return None

    matches: list[str] = []
    resolved_memory: dict[str, Any] | None = None
    for hint in hints:
        project = find_project_by_name(token, hint)
        if not project:
            continue
        record = parse_project_record(project)
        name = str(record.get("name") or hint).lower()
        matches.append(name)
        resolved_memory = _memory_from_api_record(record)

    if len(matches) == 1:
        name = matches[0]
        return TargetResolution(
            status="resolved",
            target_name=name,
            matches=matches,
            memory=resolved_memory,
            message=f"Resolved target `{name}` via Vercel API.",
            source="provider_api",
        )
    if len(matches) > 1:
        return TargetResolution(
            status="ambiguous",
            matches=matches,
            message=(
                "Multiple possible Vercel project matches via API: "
                + ", ".join(f"`{m}`" for m in matches[:6])
                + ". Please specify one target."
            ),
            source="provider_api",
        )

    primary = hints[0]
    return TargetResolution(
        status="missing",
        message=f"Project `{primary}` was not found via Vercel API.",
        source="provider_api",
    )


def _api_token_available() -> bool:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    return VercelAuthAdapter().resolve_best_auth_method(operation="read_projects").get("method") == "api_token"


def _runtime_blocked_resolution(
    *,
    detail: str,
    operation_type: str = "",
) -> TargetResolution | None:
    if _api_token_available() and is_api_capable(operation_type):
        return None
    if not browser_runtime_required(operation_type, api_token_available=_api_token_available()):
        return None

    from aethos_core.runtime.browser_runtime import browser_inventory_refresh_blocked_reason
    from aethos_core.runtime.vercel_readonly_jobs import latest_saved_vercel_profile

    blocked, reason = browser_inventory_refresh_blocked_reason(probe_launch=False)
    saved = latest_saved_vercel_profile()
    if not blocked and not saved:
        return None
    if blocked or saved:
        msg = detail
        if saved:
            msg += f" Your saved Vercel session (`{saved.profile_id}`) still exists on disk,"
        else:
            msg += " Your saved Vercel session still exists,"
        if blocked:
            msg += f" but browser execution is currently blocked. {reason}"
        else:
            msg += (
                " but operational memory is empty — approve `show my Vercel apps` "
                "to refresh inventory before this operation."
            )
        return TargetResolution(
            status="blocked_by_browser_runtime" if blocked else "missing",
            message=msg,
            source="browser",
        )
    return None


def resolve_vercel_target(
    *,
    user_request: str,
    target_hints: list[str] | None = None,
    operation_type: str = "",
) -> TargetResolution:
    op = operation_type or ""
    api_first = _api_token_available() and is_api_capable(op)

    memory_map = operational_memory.get_vercel_project_memory()
    known = set(memory_map.keys())

    if not known:
        if api_first:
            api_res = _resolve_via_api(user_request=user_request, target_hints=target_hints)
            if api_res is not None:
                return api_res
        blocked = _runtime_blocked_resolution(
            detail="Latest Vercel inventory is unavailable.",
            operation_type=op,
        )
        if blocked:
            return blocked
        if api_first:
            hints = _collect_target_hints(user_request=user_request, target_hints=target_hints)
            if hints:
                return TargetResolution(
                    status="missing",
                    message=f"Project `{hints[0]}` was not found via Vercel API.",
                    source="provider_api",
                )
        return TargetResolution(
            status="missing",
            message=(
                "No Vercel projects in operational memory. "
                "Run `show my Vercel apps` first, add a Vercel API token, or name the project explicitly."
            ),
            source="memory",
        )

    candidates: list[str] = []
    for h in target_hints or []:
        best = None
        best_sc = 0
        for k in known:
            sc = _score_match(h, k)
            if sc > best_sc:
                best_sc = sc
                best = k
        if best and best_sc >= 50:
            candidates.append(best)

    for k in _extract_token_candidates(user_request, known):
        if k not in candidates:
            candidates.append(k)

    if len(candidates) == 1:
        name = candidates[0]
        return TargetResolution(
            status="resolved",
            target_name=name,
            matches=candidates,
            memory=memory_map.get(name),
            message=f"Resolved target `{name}` from Vercel inventory memory.",
            source="memory",
        )

    if len(candidates) > 1:
        return TargetResolution(
            status="ambiguous",
            matches=candidates,
            message=(
                "Multiple possible Vercel project matches: "
                + ", ".join(f"`{m}`" for m in candidates[:6])
                + ". Please specify one target."
            ),
            source="memory",
        )

    if api_first:
        api_res = _resolve_via_api(user_request=user_request, target_hints=target_hints)
        if api_res is not None:
            return api_res

    blocked = _runtime_blocked_resolution(
        detail="I could not resolve that project because the latest Vercel inventory is unavailable.",
        operation_type=op,
    )
    if blocked:
        return blocked

    return TargetResolution(
        status="missing",
        message=(
            "I do not see that project in the saved Vercel inventory. "
            "Run `show my Vercel apps` first or name the project explicitly."
        ),
        source="memory",
    )
