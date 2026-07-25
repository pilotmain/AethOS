# SPDX-License-Identifier: Apache-2.0
"""Multi-source research provider registry — normalized retrieval."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Protocol

from aethos_core.research.evidence_contract import ResearchEvidenceItem, normalize_search_hit
from aethos_core.research.planner import ResearchPlan


class ResearchSourceProvider(Protocol):
    provider_id: str

    def retrieve(self, plan: ResearchPlan) -> list[ResearchEvidenceItem]: ...


class TavilySourceProvider:
    provider_id = "tavily"

    def retrieve(self, plan: ResearchPlan) -> list[ResearchEvidenceItem]:
        from aethos_core.research.provider_factory import build_search_provider

        search = build_search_provider()
        queries = plan.search_queries or [plan.query]
        items: list[ResearchEvidenceItem] = []
        seen_urls: set[str] = set()
        per_query = max(2, min(plan.max_results, 6))
        for q in queries[:5]:
            result = search.search(q, max_results=per_query)
            if not result.ok:
                continue
            for r in result.results:
                url = (r.url or "").strip()
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                items.append(
                    normalize_search_hit(
                        provider=self.provider_id,
                        title=r.title,
                        url=url,
                        snippet=r.snippet,
                        source_type="web",
                        metadata={"search_provider": result.provider, "query": q},
                    )
                )
                if len(items) >= plan.max_results * 2:
                    break
            if len(items) >= plan.max_results * 2:
                break
        return items[: plan.max_results * 2]


class DocGroundingSourceProvider:
    """Augment retrieval with official doc-site scoped queries."""

    provider_id = "doc_grounding"

    _SITE_HINTS: dict[str, list[str]] = {
        "railway": ["site:docs.railway.app", "site:railway.app"],
        "vercel": ["site:vercel.com/docs"],
        "github": ["site:docs.github.com", "site:github.com"],
        "next.js": ["site:nextjs.org/docs"],
        "nextjs": ["site:nextjs.org/docs"],
    }

    def retrieve(self, plan: ResearchPlan) -> list[ResearchEvidenceItem]:
        from aethos_core.research.provider_factory import build_search_provider

        q_lower = plan.query.lower()
        hints: list[str] = []
        for token, sites in self._SITE_HINTS.items():
            if token in q_lower:
                hints.extend(sites)
        if not hints:
            return []

        search = build_search_provider()
        items: list[ResearchEvidenceItem] = []
        for hint in hints[:2]:
            scoped = f"{plan.query} {hint}"
            result = search.search(scoped, max_results=min(3, plan.max_results))
            if not result.ok:
                continue
            for r in result.results:
                items.append(
                    normalize_search_hit(
                        provider=self.provider_id,
                        title=r.title,
                        url=r.url,
                        snippet=r.snippet,
                        source_type="docs",
                        metadata={"scope_hint": hint},
                    )
                )
        return items


_REGISTRY: dict[str, ResearchSourceProvider] = {
    "tavily": TavilySourceProvider(),
    "doc_grounding": DocGroundingSourceProvider(),
}


def list_registered_providers() -> list[dict[str, Any]]:
    return [
        {
            "provider_id": p.provider_id,
            "role": _provider_role(p.provider_id),
            "status": "active",
        }
        for p in _REGISTRY.values()
    ]


def retrieve_parallel(plan: ResearchPlan) -> tuple[list[ResearchEvidenceItem], list[dict[str, Any]]]:
    """Run providers in parallel; return evidence + provider call log."""
    targets = [pid for pid in plan.providers if pid in _REGISTRY]
    if not targets:
        targets = ["tavily"]

    evidence: list[ResearchEvidenceItem] = []
    calls: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=min(4, len(targets))) as pool:
        futures = {pool.submit(_REGISTRY[pid].retrieve, plan): pid for pid in targets}
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                rows = fut.result()
                evidence.extend(rows)
                calls.append({"provider": pid, "ok": True, "count": len(rows)})
            except Exception as exc:
                calls.append({"provider": pid, "ok": False, "error": exc.__class__.__name__})

    return evidence, calls


def _provider_role(provider_id: str) -> str:
    roles = {
        "tavily": "primary web search",
        "doc_grounding": "official docs grounding",
        "browser": "visual verification",
    }
    return roles.get(provider_id, "research source")
