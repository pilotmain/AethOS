# SPDX-License-Identifier: Apache-2.0
"""Universal research runtime — planner → retrieval → confidence → synthesis."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.research.confidence_engine import analyze_evidence
from aethos_core.research.evidence_contract import ResearchEvidenceItem, collapse_duplicate_evidence
from aethos_core.research.planner import ResearchPlan, extract_research_query, plan_research
from aethos_core.research.provider_registry import retrieve_parallel
from aethos_core.research.research_artifacts import get_research_artifact, store_research_artifact
from aethos_core.research.research_config import build_research_status, format_incomplete_config_message, is_research_search_configured
from aethos_core.research.synthesis_engine import (
    format_comparison_wiki_markdown,
    format_synthesis_markdown,
    synthesize_comparison_research,
    synthesize_research,
)


def new_replay_id() -> str:
    return f"rrun-{uuid4().hex[:12]}"


@dataclass
class ResearchRunResult:
    ok: bool
    query: str
    replay_id: str
    reply: str = ""
    intent: str = "research_synthesis"
    artifact_ids: list[str] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)
    configured: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "query": self.query,
            "replay_id": self.replay_id,
            "reply": self.reply,
            "artifact_ids": self.artifact_ids,
            "timeline": self.timeline,
            "meta": self.meta,
            "configured": self.configured,
        }


def run_research_query(
    user_text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> ResearchRunResult:
    from aethos_core.config import get_settings

    settings = get_settings()
    query = extract_research_query(user_text)
    try:
        from aethos_core.research_entity_alignment.entity_alignment import align_research_entity

        alignment = align_research_entity(query=query or user_text, session_id=session_id)
        if alignment.get("grounded"):
            query = str(alignment.get("aligned_query") or query)
    except Exception:
        pass
    replay_id = new_replay_id()
    timeline: list[dict[str, Any]] = []
    artifact_ids: list[str] = []

    def _step(step: str, detail: str = "", **extra: Any) -> None:
        timeline.append({"at": time(), "step": step, "detail": detail, **extra})

    if not is_research_search_configured(settings):
        _step("config_check", "research not configured")
        if settings.web_research_enabled:
            reply = format_incomplete_config_message(settings)
        else:
            reply = (
                "**Web research is disabled.** Enable `WEB_RESEARCH_ENABLED=true` and configure Tavily, then restart API."
            )
        art = store_research_artifact(
            artifact_type="research_query",
            intent="research_query",
            channel=channel,
            confidence="low",
            payload={"query": query, "replay_id": replay_id, "configured": False, "timeline": timeline},
        )
        artifact_ids.append(art["artifact_id"])
        _persist_replay(replay_id, query, timeline, artifact_ids, channel)
        return ResearchRunResult(
            ok=False,
            query=query,
            replay_id=replay_id,
            reply=reply,
            intent="research_not_configured",
            artifact_ids=artifact_ids,
            timeline=timeline,
            configured=False,
            meta=_meta(channel, replay_id, artifact_ids, configured="false"),
        )

    plan = plan_research(query, max_results=settings.web_research_max_results)
    _step("plan", plan.mode.value, plan=plan.to_dict())

    query_art = store_research_artifact(
        artifact_type="research_query",
        intent="research_query",
        channel=channel,
        confidence="medium",
        payload={"query": query, "replay_id": replay_id, "plan": plan.to_dict(), "timeline": timeline},
    )
    artifact_ids.append(query_art["artifact_id"])

    evidence, provider_calls = retrieve_parallel(plan)
    evidence = collapse_duplicate_evidence(evidence)
    _step("retrieve", f"{len(evidence)} evidence items", providers=provider_calls)

    result_art = store_research_artifact(
        artifact_type="research_result_set",
        intent="research_query",
        channel=channel,
        confidence="medium",
        payload={
            "query": query,
            "replay_id": replay_id,
            "evidence": [e.to_dict() for e in evidence],
            "provider_calls": provider_calls,
        },
    )
    artifact_ids.append(result_art["artifact_id"])

    browser_verifications: list[dict[str, Any]] = []
    if plan.browser_verification and evidence:
        browser_verifications = _optional_browser_verification(
            evidence[:2],
            session_id=session_id,
            channel=channel,
            replay_id=replay_id,
        )
        if browser_verifications:
            artifact_ids.extend(v["artifact_id"] for v in browser_verifications if v.get("artifact_id"))
            _step("browser_verify", f"{len(browser_verifications)} URL(s) verified")

    analysis = analyze_evidence(evidence, freshness_required=plan.freshness_required)
    conf_art = store_research_artifact(
        artifact_type="research_confidence_analysis",
        intent="research_query",
        channel=channel,
        confidence="high" if analysis.overall_confidence >= 0.7 else "medium",
        payload={"query": query, "replay_id": replay_id, "analysis": analysis.to_dict()},
    )
    artifact_ids.append(conf_art["artifact_id"])
    _step("confidence", f"overall={analysis.overall_confidence}", contradictions=len(analysis.contradictions))

    if analysis.contradictions:
        contra_art = store_research_artifact(
            artifact_type="research_contradiction_report",
            intent="research_query",
            channel=channel,
            confidence="medium",
            payload={"query": query, "replay_id": replay_id, "contradictions": analysis.contradictions},
        )
        artifact_ids.append(contra_art["artifact_id"])
        _step("contradictions", f"{len(analysis.contradictions)} detected")

    comparison = plan.comparison_subjects
    if comparison:
        subject_a, subject_b = comparison
        synthesis = synthesize_comparison_research(query, subject_a, subject_b, evidence, analysis)
        raw_reply = format_comparison_wiki_markdown(
            query=query,
            subject_a=subject_a,
            subject_b=subject_b,
            synthesis=synthesis,
            analysis=analysis,
            evidence=evidence,
            replay_id=replay_id,
            artifact_ids=artifact_ids,
        )
    else:
        synthesis = synthesize_research(query, evidence, analysis)
        raw_reply = format_synthesis_markdown(
            synthesis,
            analysis,
            replay_id=replay_id,
            artifact_ids=artifact_ids,
            browser_verifications=browser_verifications,
        )

    synth_art = store_research_artifact(
        artifact_type="research_synthesis",
        intent="research_query",
        channel=channel,
        confidence="high" if analysis.overall_confidence >= 0.7 else "medium",
        payload={
            "query": query,
            "replay_id": replay_id,
            "synthesis": synthesis.to_dict(),
            "citations": synthesis.citations,
            "comparison": bool(comparison),
        },
    )
    artifact_ids.append(synth_art["artifact_id"])
    _step("synthesis", "complete", citation_count=len(synthesis.citations), source_count=len(evidence))
    # The real polisher returns a dict ({"reply": ...}); polish_compat's stub takes a single
    # positional `reply` and returns a string, so importing it here raised TypeError.
    from aethos_core.conversation.synthesis_pkg.synthesis_runtime import polish_research_reply

    polished = polish_research_reply(
        query=query,
        synthesis=synthesis,
        analysis=analysis,
        evidence=evidence,
        raw_markdown=raw_reply,
        mode="engineering" if plan.mode.value in ("operational", "technical", "deep_synthesis") else "casual",
        comparison=bool(comparison),
    )
    reply = polished.get("reply") or raw_reply
    store_research_artifact(
        artifact_type="research_synthesis_engineering",
        intent="research_query",
        channel=channel,
        confidence="medium",
        payload={
            "query": query,
            "replay_id": replay_id,
            "raw_markdown": raw_reply,
            "polished": polished,
        },
    )
    _step("conversational_polish", "complete", tier=polished.get("qualification_tier", ""))
    _step("complete", "research run finished")
    _persist_replay(replay_id, query, timeline, artifact_ids, channel, plan=plan.to_dict())
    _remember_session_research(
        session_id=session_id,
        replay_id=replay_id,
        query=query,
        comparison=comparison,
    )

    return ResearchRunResult(
        ok=bool(evidence),
        query=query,
        replay_id=replay_id,
        reply=reply,
        intent="research_synthesis",
        artifact_ids=artifact_ids,
        timeline=timeline,
        meta=_meta(channel, replay_id, artifact_ids, configured="true", mode=plan.mode.value, comparison=str(bool(comparison)).lower()),
    )


def _remember_session_research(
    *,
    session_id: str,
    replay_id: str,
    query: str,
    comparison: tuple[str, str] | None,
) -> None:
    from aethos_core.research.research_session_memory import remember_research_run

    remember_research_run(
        session_id=session_id,
        replay_id=replay_id,
        query=query,
        comparison=bool(comparison),
        subjects=comparison,
    )


def get_research_replay(replay_id: str) -> dict[str, Any] | None:
    art = get_research_artifact(replay_id)
    if art and art.get("artifact_type") == "research_replay":
        return art
    for row in _load_replay_index():
        if row.get("replay_id") == replay_id:
            path_art = get_research_artifact(row.get("artifact_id", ""))
            if path_art:
                return path_art
    return None


def _optional_browser_verification(
    evidence: list[ResearchEvidenceItem],
    *,
    session_id: str,
    channel: str,
    replay_id: str,
) -> list[dict[str, Any]]:
    from aethos_core.runtime.authority import authority

    if not authority.capabilities.get("browser_automation_enabled"):
        return []

    from aethos_core.browser.runtime.browser_runtime import run_browser_evidence_capture

    rows: list[dict[str, Any]] = []
    for item in evidence:
        url = (item.url or "").strip()
        if not url.startswith("http"):
            continue
        capture = run_browser_evidence_capture(
            url=url,
            capture_type="metadata",
            session_id=session_id,
            user_request=f"research verify {url}",
            approved=True,
        )
        browser_ids = [a.get("artifact_id") for a in capture.get("artifacts") or [] if a.get("artifact_id")]
        art = store_research_artifact(
            artifact_type="research_browser_verification",
            intent="research_query",
            channel=channel,
            confidence="medium",
            payload={
                "replay_id": replay_id,
                "url": url,
                "citation_id": item.citation_id,
                "capture_ok": capture.get("ok"),
                "browser_artifact_ids": browser_ids,
                "metadata": capture.get("metadata") or {},
            },
        )
        rows.append({"url": url, "artifact_id": art["artifact_id"], "citation_id": item.citation_id})
    return rows


def _persist_replay(
    replay_id: str,
    query: str,
    timeline: list[dict[str, Any]],
    artifact_ids: list[str],
    channel: str,
    *,
    plan: dict[str, Any] | None = None,
) -> None:
    store_research_artifact(
        artifact_type="research_replay",
        intent="research_replay",
        channel=channel,
        confidence="medium",
        payload={
            "replay_id": replay_id,
            "query": query,
            "plan": plan or {},
            "timeline": timeline,
            "artifact_ids": artifact_ids,
        },
        artifact_id=replay_id,
    )


def _meta(channel: str, replay_id: str, artifact_ids: list[str], **extra: str) -> dict[str, str]:
    meta = {
        "lane": "web_intelligence",
        "web_intelligence": "true",
        "research_runtime": "true",
        "channel": channel,
        "research_replay_id": replay_id,
        "research_artifact_id": artifact_ids[-1] if artifact_ids else "",
        "mission_control_view": "deep-research",
    }
    meta.update({k: str(v) for k, v in extra.items() if v})
    return meta


def _load_replay_index() -> list[dict[str, Any]]:
    from aethos_core.research.research_artifacts import list_research_artifacts

    return [a for a in list_research_artifacts(limit=200) if a.get("artifact_type") == "research_replay"]
