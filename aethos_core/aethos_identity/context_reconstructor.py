# SPDX-License-Identifier: Apache-2.0
"""Reconstruct operational context from jobs, topology, and prompt cues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_JOB_ID_RX = re.compile(r"\b(job-[a-f0-9]{8,}|dj-[a-f0-9]{8,})\b", re.I)
_FOR_RESOURCE_RX = re.compile(
    r"\b(?:for|on|of|about|with)\s+(?:the\s+)?([a-z0-9][a-z0-9._-]+(?:\s*/\s*[a-z0-9][a-z0-9._-]+)*)\b",
    re.I,
)
_RESOURCE_SUFFIX_RX = re.compile(
    r"\b([a-z0-9][a-z0-9._-]+)\s+(?:service|api|worker|app|deployment)\b",
    re.I,
)
_OPERATIONAL_NAME_RX = re.compile(
    r"\b([a-z0-9][a-z0-9._-]{2,62})\b",
    re.I,
)
_SKIP_TOKENS = frozenset(
    {
        "aethos",
        "railway",
        "vercel",
        "github",
        "docker",
        "kubernetes",
        "aws",
        "the",
        "can",
        "you",
        "check",
        "top",
        "latest",
        "recent",
        "logs",
        "log",
        "timestamp",
        "timestamps",
        "status",
        "restart",
        "redeploy",
        "deploy",
        "what",
        "were",
        "we",
        "doing",
        "with",
        "and",
        "its",
        "for",
        "me",
        "please",
        "show",
        "give",
        "read",
        "tell",
        "did",
        "happen",
        "happened",
        "actually",
        "after",
        "before",
        "approval",
        "production",
        "service",
    }
)


@dataclass
class ProviderTargetMatch:
    provider: str
    service_name: str
    project_name: str | None = None
    environment: str | None = "production"
    service_id: str | None = None
    confidence: float = 0.0
    source: str = "topology"
    path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "service_name": self.service_name,
            "project_name": self.project_name,
            "environment": self.environment,
            "service_id": self.service_id,
            "confidence": self.confidence,
            "source": self.source,
            "path": self.path,
        }


@dataclass
class TopologySearchResult:
    phrase: str
    matches: list[ProviderTargetMatch] = field(default_factory=list)
    ambiguous: bool = False
    resolved: ProviderTargetMatch | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "phrase": self.phrase,
            "matches": [m.to_dict() for m in self.matches],
            "ambiguous": self.ambiguous,
            "resolved": self.resolved.to_dict() if self.resolved else None,
        }


@dataclass
class ReconstructedContext:
    session_id: str
    source: str
    thread: Any | None = None
    execution_job: Any | None = None
    target: ProviderTargetMatch | None = None
    confidence: str = "moderate"
    meta: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "source": self.source,
            "thread": getattr(self.thread, "to_dict", lambda: None)() if self.thread else None,
            "execution_job_id": str(getattr(self.execution_job, "id", "") or ""),
            "target": self.target.to_dict() if self.target else None,
            "confidence": self.confidence,
            "meta": dict(self.meta),
        }


def _is_plausible_service_phrase(phrase: str) -> bool:
    p = (phrase or "").strip().lower()
    if not p or p in _SKIP_TOKENS:
        return False
    if "/" in p:
        return True
    tokens = [t for t in re.split(r"[\s/]+", p) if t]
    if not tokens:
        return False
    if all(t in _SKIP_TOKENS for t in tokens):
        return False
    for token in tokens:
        if token in _SKIP_TOKENS:
            continue
        if "-" in token or token.endswith("-api") or len(token) >= 6:
            return True
    return False


def extract_operational_resource_phrase(user_text: str) -> str | None:
    raw = (user_text or "").strip()
    if not raw:
        return None

    from aethos_core.provider_discovery.target_resolution import extract_service_phrase

    phrase = extract_service_phrase(raw)
    if phrase and _is_plausible_service_phrase(phrase):
        return phrase

    job_match = _JOB_ID_RX.search(raw)
    if job_match:
        return job_match.group(1).lower()

    for_match = _FOR_RESOURCE_RX.search(raw)
    if for_match:
        candidate = for_match.group(1).strip().lower()
        if candidate and candidate not in _SKIP_TOKENS:
            return candidate.replace(" / ", "/")

    suffix_match = _RESOURCE_SUFFIX_RX.search(raw)
    if suffix_match:
        from aethos_core.chat.local_system_guidance import is_local_aethos_api_restart_intent

        if is_local_aethos_api_restart_intent(raw):
            return None
        candidate = suffix_match.group(1).lower()
        if candidate not in _SKIP_TOKENS:
            return candidate

    if _looks_operational(raw):
        tokens = [t.lower() for t in _OPERATIONAL_NAME_RX.findall(raw) if t.lower() not in _SKIP_TOKENS]
        for token in reversed(tokens):
            if "-" in token or token.endswith("-api") or len(token) >= 6:
                return token
    return phrase


def search_provider_targets(phrase: str) -> TopologySearchResult:
    phrase = (phrase or "").strip().lower()
    result = TopologySearchResult(phrase=phrase)
    if not phrase or phrase.startswith("job-") or phrase.startswith("dj-"):
        return result

    from aethos_core.operations.orchestration.provider_inference import infer_provider_for_hints

    inferred = infer_provider_for_hints([phrase])
    status = str(inferred.get("status") or "")
    for row in inferred.get("matches") or []:
        match = ProviderTargetMatch(
            provider=str(row.get("provider") or "unknown"),
            service_name=str(row.get("service_name") or row.get("name") or phrase),
            project_name=row.get("project_name"),
            environment=str(row.get("environment") or "production"),
            service_id=row.get("service_id"),
            confidence=0.9 if status == "resolved" else 0.75,
            source=str(row.get("source") or "inventory"),
        )
        if match.project_name and match.service_name:
            match.path = f"{match.project_name} / {match.environment} / {match.service_name}"
        result.matches.append(match)

    if not result.matches:
        result.matches.extend(_search_railway_inventory(phrase))

    providers = {m.provider for m in result.matches}
    if len(providers) > 1:
        result.ambiguous = True
    elif len(result.matches) == 1:
        result.resolved = result.matches[0]
    elif len(result.matches) > 1:
        names = {m.service_name.lower() for m in result.matches}
        if len(names) == 1:
            result.resolved = result.matches[0]
        else:
            result.ambiguous = True
    return result


def _search_railway_inventory(phrase: str) -> list[ProviderTargetMatch]:
    from aethos_core.provider_discovery.discovery_runtime import get_provider_inventory
    from aethos_core.provider_discovery.target_resolution import resolve_target_from_inventory

    inventory = get_provider_inventory(provider="railway")
    resolution = resolve_target_from_inventory(inventory=inventory, user_request=phrase, target_hints=[phrase])
    if not resolution.resolved:
        return []
    return [
        ProviderTargetMatch(
            provider="railway",
            service_name=str(resolution.service_name or phrase),
            project_name=resolution.project_name,
            environment=str(resolution.environment or "production"),
            service_id=resolution.service_id,
            confidence=float(resolution.confidence or 0.88),
            source=str(resolution.source or "provider_inventory"),
            path=f"{resolution.project_name} / {resolution.environment} / {resolution.service_name}",
        )
    ]


def maybe_reconstruct_active_thread(*, session_id: str, user_text: str = "") -> ReconstructedContext | None:
    from aethos_core.aethos_identity.identity_contract_loader import load_identity_contracts
    from aethos_core.continuity_intelligence.continuity_recall_engine import recall_operational_memory

    load_identity_contracts()

    recall = recall_operational_memory(session_id=session_id, user_text=user_text)
    if recall is None or recall.thread is None:
        from aethos_core.operational_thread_memory.thread_persistence import get_active_thread, is_thread_expired

        existing = get_active_thread(session_id=session_id)
        if existing is not None and not is_thread_expired(existing):
            return ReconstructedContext(session_id=session_id, source="active_thread", thread=existing, confidence="high")
        if existing is not None:
            return ReconstructedContext(session_id=session_id, source="expired_thread", thread=existing, confidence="low")
        return None

    source_map = {
        "active_operational_thread": "active_thread",
        "semantic_execution_job": "execution_job",
        "recent_operational_timeline": "execution_job",
        "topology_match": "provider_topology",
        "operational_focus": "operational_focus",
        "expired_operational_thread": "expired_thread",
    }
    return ReconstructedContext(
        session_id=session_id,
        source=source_map.get(recall.source, recall.source),
        thread=recall.thread,
        execution_job=recall.execution_job,
        target=recall.target,
        confidence="high" if recall.confidence >= 0.8 else "moderate" if recall.confidence >= 0.5 else "low",
        meta={
            **recall.meta,
            "execution_job_id": recall.execution_job_id,
            "provider": recall.provider,
            "service": recall.service,
        },
    )


def reconstruct_context_summary(*, session_id: str, user_text: str) -> str | None:
    ctx = maybe_reconstruct_active_thread(session_id=session_id, user_text=user_text)
    if ctx is None or ctx.thread is None:
        return None
    path = ctx.thread.service_path()
    op = str(getattr(ctx.thread, "operation", "") or "operation").replace("_", " ")
    return (
        f"I reconstructed the recent **{ctx.thread.provider}** **{op}** context for **{path}**.\n\n"
        f"Latest stored result: **{ctx.thread.status}** — {ctx.thread.last_system_result or 'execution updated'}.\n\n"
        f"Source: {ctx.source.replace('_', ' ')}."
    )


def _looks_operational(text: str) -> bool:
    lower = text.lower()
    markers = (
        "log",
        "timestamp",
        "restart",
        "redeploy",
        "deploy",
        "status",
        "check",
        "verify",
        "what were we",
        "top ",
        "latest ",
    )
    return any(marker in lower for marker in markers)
