# SPDX-License-Identifier: Apache-2.0
"""Pick Railway project/environment/service targets from inventory + user text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_ENV_ALIASES = {
    "stage": "staging",
    "staging": "staging",
    "prod": "production",
    "production": "production",
    "dev": "development",
    "development": "development",
}

_ENV_RX = re.compile(r"\b(staging|stage|production|prod|development|dev)\b", re.I)
_ENV_PREFIX_RX = re.compile(
    r"^\s*(staging|stage|production|prod|development|dev)\s*:\s*(.+)$",
    re.I,
)
_SERVICE_NAME_RX = re.compile(r"\b([a-z0-9][a-z0-9._-]*(?:/[a-z0-9][a-z0-9._-]*)*)\b", re.I)
_BOTH_UI_API_RX = re.compile(
    r"\b(?:for\s+)?both\s+(?:the\s+)?(?:ui\s+and\s+api|api\s+and\s+ui)\b",
    re.I,
)
_UI_ONLY_RX = re.compile(r"\b(?:the\s+)?ui(?:\s+service|\s+changes?)?\b", re.I)
_API_ONLY_RX = re.compile(r"\b(?:the\s+)?api(?:\s+service|\s+changes?)?\b", re.I)
_PROJECT_SERVICE_RX = re.compile(
    r"\b([a-z0-9][a-z0-9._-]*)\s*/\s*([a-z0-9][a-z0-9._-]*)\b",
    re.I,
)


@dataclass(frozen=True)
class RailwayInventoryTarget:
    project: str
    environment: str
    service: str

    @property
    def path(self) -> str:
        return f"{self.project} / {self.environment} / {self.service}"


@dataclass
class RailwayTargetPickResult:
    targets: list[RailwayInventoryTarget] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    reason: str = "resolved"
    environment_hint: str = ""
    service_hints: list[str] = field(default_factory=list)


def normalize_environment(name: str) -> str:
    token = (name or "").strip().lower()
    return _ENV_ALIASES.get(token, token)


def extract_environment_hint(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    prefix = _ENV_PREFIX_RX.match(raw)
    if prefix:
        return normalize_environment(prefix.group(1))
    match = _ENV_RX.search(raw)
    if match:
        return normalize_environment(match.group(1))
    return ""


def looks_like_target_selection_reply(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if re.search(r"\b(?:railway|github|aethos|re-?deploy(?:ing|ment)?|git)\b", raw, re.I):
        return False
    if _ENV_PREFIX_RX.match(raw):
        return True
    if re.match(r"^\s*\d+\.", raw):
        return True
    if re.match(r"^\s*[^/]+\s*/\s*[^/]+\s*/\s*", raw):
        return True
    if "," in raw and not re.search(r"\b(?:changes|commits)\b", raw, re.I):
        return True
    return len(raw.split()) <= 5 and not re.search(r"\b(?:check)\b", raw, re.I)


def infer_redeploy_environment(text: str) -> str:
    env = extract_environment_hint(text)
    if env:
        return env
    lower = (text or "").lower()
    if re.search(r"\b(production|prod)\b", lower):
        return "production"
    if re.search(r"\b(staging|stage)\b", lower):
        return "staging"
    if any(token in lower for token in ("git", "latest changes", "new changes", "commits")):
        return "staging"
    return ""


def extract_project_hint(text: str, *, default: str = "pilotos") -> str:
    raw = (text or "").strip()
    if not raw:
        return default
    for match in _PROJECT_SERVICE_RX.finditer(raw):
        project = match.group(1).strip().lower()
        if project not in _ENV_ALIASES and project not in {"railway", "github", "vercel"}:
            return project
    if "pilotos" in raw.lower():
        return "pilotos"
    return default


def default_aethos_service_hints(*, project_hint: str = "pilotos") -> list[str]:
    hint = (project_hint or "").lower()
    if "pilot" in hint or "aethos" in hint:
        return ["aethos-api", "aethos-ui"]
    return []


def extract_service_hints(text: str, *, project_hint: str = "aethos") -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []

    if looks_like_target_selection_reply(raw):
        _, selection_services = parse_target_selection_reply(raw)
        if selection_services:
            return selection_services

    lower = raw.lower()
    prefix = _aethos_service_prefix(lower, project_hint)
    hints: list[str] = []

    if _BOTH_UI_API_RX.search(raw):
        return [f"{prefix}-ui", f"{prefix}-api"]

    for match in _PROJECT_SERVICE_RX.finditer(raw):
        service = match.group(2).strip().lower()
        if service and service not in _ENV_ALIASES:
            hints.append(service)

    if _UI_ONLY_RX.search(raw):
        ui_hint = f"{prefix}-ui"
        if ui_hint not in hints:
            hints.append(ui_hint)
    if _API_ONLY_RX.search(raw):
        api_hint = f"{prefix}-api"
        if api_hint not in hints:
            hints.append(api_hint)

    for match in _SERVICE_NAME_RX.finditer(raw):
        token = match.group(1).strip().lower()
        if token in _ENV_ALIASES or token in {"railway", "github", "vercel", "changes", "latest", "commits"}:
            continue
        if "/" in token:
            continue
        if token.count("-") >= 1 or token.count(".") >= 1:
            if token not in hints:
                hints.append(token)

    deduped: list[str] = []
    seen: set[str] = set()
    for hint in hints:
        norm = hint.lower()
        if norm and norm not in seen:
            seen.add(norm)
            deduped.append(norm)
    return deduped


def parse_target_selection_reply(text: str) -> tuple[str, list[str]]:
    raw = (text or "").strip()
    if not raw:
        return "", []

    env_hint = ""
    remainder = raw
    prefix = _ENV_PREFIX_RX.match(raw)
    if prefix:
        env_hint = normalize_environment(prefix.group(1))
        remainder = prefix.group(2).strip()

    path_match = re.match(r"^\s*([^/]+)\s*/\s*([^/]+)\s*/\s*(.+)$", remainder)
    if path_match:
        env_hint = env_hint or normalize_environment(path_match.group(2))
        remainder = path_match.group(3).strip()

    services = _split_service_tokens(remainder)
    return env_hint, services


def _split_service_tokens(text: str) -> list[str]:
    raw = (text or "").strip().strip(".")
    if not raw:
        return []
    parts = re.split(r"\s*,\s*|\s+and\s+", raw, flags=re.I)
    out: list[str] = []
    for part in parts:
        token = part.strip().strip('"').strip("'")
        if not token:
            continue
        indexed = re.match(r"^\d+\.\s*(.+)$", token)
        if indexed:
            token = indexed.group(1).strip()
        if token.lower() in {"redeploy", "redeploying", "latest", "changes", "please", "yes"}:
            continue
        out.append(token.lower())
    return out


def _aethos_service_prefix(lower_text: str, project_hint: str) -> str:
    if "aethos" in lower_text or project_hint.lower() == "aethos":
        return "aethos"
    return project_hint.lower() or "aethos"


def iter_inventory_triples(checks: dict[str, Any]) -> list[RailwayInventoryTarget]:
    inv = checks.get("inventory") or {}
    triples: list[RailwayInventoryTarget] = []
    for project in list(inv.get("projects") or []):
        pname = str(project.get("name") or project.get("id") or "")
        for env in list(project.get("environments") or []):
            ename = normalize_environment(str(env.get("name") or env.get("id") or "production"))
            for svc in list(env.get("services") or []):
                triples.append(
                    RailwayInventoryTarget(
                        project=pname,
                        environment=ename,
                        service=str(svc),
                    )
                )
    return triples


def build_selection_candidates(
    checks: dict[str, Any],
    user_text: str,
    *,
    project_hint: str = "aethos",
) -> list[dict[str, Any]]:
    env_hint = extract_environment_hint(user_text)
    service_hints = extract_service_hints(user_text, project_hint=project_hint)
    triples = iter_inventory_triples(checks)
    filtered = _filter_triples(
        triples,
        environment_hint=env_hint,
        service_hints=service_hints,
        project_hint=project_hint,
        strict_environment=bool(env_hint),
        strict_services=bool(service_hints),
    )
    if not filtered:
        filtered = _filter_triples(triples, project_hint=project_hint)
    rows: list[dict[str, Any]] = []
    for row in filtered[:12]:
        rows.append(
            {
                "project_name": row.project,
                "environment": row.environment,
                "service_name": row.service,
                "path": row.path,
            }
        )
    return rows


def pick_railway_targets(
    checks: dict[str, Any],
    user_text: str,
    *,
    default_hint: str = "aethos",
) -> RailwayTargetPickResult:
    triples = iter_inventory_triples(checks)
    if not triples:
        return RailwayTargetPickResult(reason="inventory_empty")

    env_hint = extract_environment_hint(user_text)
    service_hints = extract_service_hints(user_text, project_hint=default_hint)

    if service_hints:
        matched = _filter_triples(
            triples,
            environment_hint=env_hint,
            service_hints=service_hints,
            project_hint=default_hint,
            strict_environment=bool(env_hint),
            strict_services=True,
        )
        if matched:
            narrowed = _narrow_targets_by_environment(matched, user_text)
            return RailwayTargetPickResult(
                targets=narrowed,
                reason="resolved",
                environment_hint=env_hint or infer_redeploy_environment(user_text),
                service_hints=service_hints,
            )

    if env_hint:
        env_matches = _filter_triples(
            triples,
            environment_hint=env_hint,
            project_hint=default_hint,
            strict_environment=True,
        )
        if len(env_matches) == 1:
            return RailwayTargetPickResult(
                targets=env_matches,
                reason="resolved",
                environment_hint=env_hint,
                service_hints=service_hints,
            )

    hint_lower = default_hint.lower()
    fuzzy = [
        row
        for row in triples
        if hint_lower in row.service.lower() or hint_lower in row.project.lower()
    ]
    if env_hint:
        fuzzy = [row for row in fuzzy if row.environment == env_hint]
    if len(fuzzy) == 1:
        return RailwayTargetPickResult(
            targets=fuzzy,
            reason="resolved",
            environment_hint=env_hint,
            service_hints=service_hints,
        )

    if len(triples) == 1:
        return RailwayTargetPickResult(
            targets=triples,
            reason="resolved",
            environment_hint=env_hint,
            service_hints=service_hints,
        )

    candidate_rows = build_selection_candidates(checks, user_text, project_hint=default_hint)
    if not candidate_rows:
        candidate_rows = [
            {
                "project_name": row.project,
                "environment": row.environment,
                "service_name": row.service,
                "path": row.path,
            }
            for row in triples[:12]
        ]
    return RailwayTargetPickResult(
        candidates=candidate_rows,
        reason="ambiguous",
        environment_hint=env_hint,
        service_hints=service_hints,
    )


def _filter_triples(
    triples: list[RailwayInventoryTarget],
    *,
    environment_hint: str = "",
    service_hints: list[str] | None = None,
    project_hint: str = "",
    strict_environment: bool = False,
    strict_services: bool = False,
) -> list[RailwayInventoryTarget]:
    rows = list(triples)
    if environment_hint:
        env = normalize_environment(environment_hint)
        rows = [row for row in rows if row.environment == env]
        if strict_environment and not rows:
            return []

    if project_hint:
        hint = project_hint.lower()
        project_filtered = [row for row in rows if hint in row.project.lower() or hint in row.service.lower()]
        if project_filtered:
            rows = project_filtered

    if service_hints:
        matched: list[RailwayInventoryTarget] = []
        for hint in service_hints:
            hint_norm = hint.lower()
            for row in rows:
                if _service_matches_hint(row.service, hint_norm):
                    matched.append(row)
        if matched:
            deduped: list[RailwayInventoryTarget] = []
            seen: set[str] = set()
            for row in matched:
                key = row.path
                if key not in seen:
                    seen.add(key)
                    deduped.append(row)
            return deduped
        if strict_services:
            return []

    return rows


def _narrow_targets_by_environment(
    targets: list[RailwayInventoryTarget],
    user_text: str,
) -> list[RailwayInventoryTarget]:
    env = infer_redeploy_environment(user_text)
    if not env:
        return targets
    filtered = [row for row in targets if row.environment == env]
    if filtered:
        return filtered
    return targets


def _service_matches_hint(service: str, hint: str) -> bool:
    svc = service.lower()
    if svc == hint:
        return True
    if "-" in hint and "." not in hint:
        return svc == hint
    if hint in svc or svc in hint:
        return True
    return False


def pick_single_railway_target(
    checks: dict[str, Any],
    user_text: str,
    *,
    default_hint: str = "aethos",
) -> tuple[str, str, str] | None:
    result = pick_railway_targets(checks, user_text, default_hint=default_hint)
    if len(result.targets) == 1:
        row = result.targets[0]
        return row.project, row.environment, row.service
    return None
