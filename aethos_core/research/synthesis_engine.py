# SPDX-License-Identifier: Apache-2.0
"""Research synthesis — evidence-grounded operational answers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.research.confidence_engine import ConfidenceAnalysis
from aethos_core.research.evidence_contract import ResearchEvidenceItem


@dataclass
class ResearchSynthesis:
    query: str
    summary: str
    bullets: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "summary": self.summary,
            "bullets": self.bullets,
            "citations": self.citations,
            "limitations": self.limitations,
        }


def synthesize_research(
    query: str,
    evidence: list[ResearchEvidenceItem],
    analysis: ConfidenceAnalysis,
) -> ResearchSynthesis:
    if not evidence:
        return ResearchSynthesis(
            query=query,
            summary="No evidence retrieved — cannot synthesize claims without sources.",
            limitations=["No search results returned from configured providers."],
        )

    ranked = sorted(evidence, key=lambda e: (e.confidence, e.freshness_score), reverse=True)
    bullets: list[str] = []
    citations: list[str] = []
    for item in ranked[:5]:
        snippet = (item.snippet or item.title or "No snippet").strip()
        if len(snippet) > 220:
            snippet = snippet[:217] + "..."
        bullets.append(f"{snippet} `[{item.citation_id}]`")
        citations.append(item.citation_id)

    conf_label = "high" if analysis.overall_confidence >= 0.75 else "medium" if analysis.overall_confidence >= 0.5 else "low"
    summary = (
        f"Evidence-backed research synthesis for **{query}** "
        f"(overall confidence: **{conf_label}** / {analysis.overall_confidence:.2f})."
    )

    limitations: list[str] = []
    if analysis.contradictions:
        limitations.append(f"{len(analysis.contradictions)} contradiction(s) detected across sources.")
    if analysis.overall_confidence < 0.5:
        limitations.append("Low source agreement — treat guidance as provisional.")
    limitations.append("Synthesis references citation IDs only; no claims without evidence.")

    return ResearchSynthesis(
        query=query,
        summary=summary,
        bullets=bullets,
        citations=citations,
        limitations=limitations,
    )


def format_synthesis_markdown(
    synthesis: ResearchSynthesis,
    analysis: ConfidenceAnalysis,
    *,
    replay_id: str = "",
    artifact_ids: list[str] | None = None,
    browser_verifications: list[dict[str, Any]] | None = None,
) -> str:
    lines = [
        "# Research synthesis",
        "",
        synthesis.summary,
        "",
        "## Key findings",
    ]
    if synthesis.bullets:
        for b in synthesis.bullets:
            lines.append(f"- {b}")
    else:
        lines.append("- _No evidence bullets available._")

    lines.extend(
        [
            "",
            "## Confidence",
            f"- Overall: **{analysis.overall_confidence:.2f}**",
            f"- Freshness: **{analysis.freshness_score:.2f}**",
            f"- Source agreement: **{analysis.source_agreement:.2f}**",
        ]
    )

    if analysis.contradictions:
        lines.append("")
        lines.append("## Contradictions")
        for c in analysis.contradictions[:4]:
            lines.append(f"- `{c.get('citation_a')}` vs `{c.get('citation_b')}` — {c.get('reason')}")

    if browser_verifications:
        lines.append("")
        lines.append("## Browser verification")
        for v in browser_verifications[:2]:
            lines.append(f"- `{v.get('url')}` — artifact `{v.get('artifact_id', '—')}`")

    if synthesis.limitations:
        lines.append("")
        lines.append("## Limitations")
        for lim in synthesis.limitations:
            lines.append(f"- {lim}")

    lines.append("")
    lines.append("## Sources")
    for row in analysis.scored_evidence[:6]:
        lines.append(
            f"- `[{row.get('citation_id')}]` **{row.get('title')}** "
            f"(conf {row.get('confidence'):.2f}, fresh {row.get('freshness_score'):.2f}) — {row.get('url')}"
        )

    if artifact_ids:
        lines.append("")
        lines.append("## Artifacts")
        for aid in artifact_ids:
            lines.append(f"- `{aid}`")
    if replay_id:
        lines.append(f"- Replay: `{replay_id}`")

    return "\n".join(lines)


def _mention_score(item: ResearchEvidenceItem, phrase: str) -> int:
    blob = f"{item.title or ''} {item.snippet or ''}".lower()
    tokens = [t for t in phrase.lower().split() if len(t) > 2]
    return sum(1 for t in tokens if t in blob)


def synthesize_comparison_research(
    query: str,
    subject_a: str,
    subject_b: str,
    evidence: list[ResearchEvidenceItem],
    analysis: ConfidenceAnalysis,
) -> ResearchSynthesis:
    if not evidence:
        return ResearchSynthesis(
            query=query,
            summary="No sources found for this comparison.",
            limitations=["Enable web research and try rephrasing, or switch search provider in Settings."],
        )

    a_items = sorted(evidence, key=lambda e: _mention_score(e, subject_a), reverse=True)[:4]
    b_items = sorted(evidence, key=lambda e: _mention_score(e, subject_b), reverse=True)[:4]
    citations = list(dict.fromkeys([i.citation_id for i in a_items + b_items if i.citation_id]))

    a_count = sum(_mention_score(e, subject_a) for e in evidence)
    b_count = sum(_mention_score(e, subject_b) for e in evidence)
    if a_count > b_count * 1.25:
        lean = subject_a
    elif b_count > a_count * 1.25:
        lean = subject_b
    else:
        lean = "depends on your workflow"

    summary = (
        f"Comparison wiki for **{subject_a}** vs **{subject_b}** "
        f"({len(evidence)} sources, confidence {analysis.overall_confidence:.2f})."
    )
    bullets = [
        f"**{subject_a}** — {len(a_items)} primary source(s), signal weight {a_count}",
        f"**{subject_b}** — {len(b_items)} primary source(s), signal weight {b_count}",
        f"**Lean for this question:** {lean}",
    ]
    limitations = []
    if analysis.contradictions:
        limitations.append(f"{len(analysis.contradictions)} conflicting source pair(s) — read both sides below.")
    if analysis.overall_confidence < 0.55:
        limitations.append("Source agreement is weak — treat the verdict as directional, not definitive.")

    return ResearchSynthesis(
        query=query,
        summary=summary,
        bullets=bullets,
        citations=citations,
        limitations=limitations,
    )


def format_comparison_wiki_markdown(
    *,
    query: str,
    subject_a: str,
    subject_b: str,
    synthesis: ResearchSynthesis,
    analysis: ConfidenceAnalysis,
    evidence: list[ResearchEvidenceItem],
    replay_id: str = "",
    artifact_ids: list[str] | None = None,
) -> str:
    a_short, b_short = subject_a[:48], subject_b[:48]
    a_snip = _best_snippet(evidence, subject_a)
    b_snip = _best_snippet(evidence, subject_b, exclude={a_snip} if a_snip != "—" else None)

    lines = [
        f"# Comparison wiki",
        "",
        f"**Question:** {query}",
        "",
        synthesis.summary,
        "",
        "## Side by side",
        "",
        f"| | {a_short} | {b_short} |",
        f"| --- | --- | --- |",
        f"| Focus | Personal AI / second brain tooling | Knowledge wiki / LLM reference model |",
        f"| Source signal | {_mention_score_total(evidence, subject_a)} matching snippets | {_mention_score_total(evidence, subject_b)} matching snippets |",
        f"| Best snippet | {a_snip} | {b_snip} |",
        "",
        "## Verdict",
    ]

    for bullet in synthesis.bullets:
        lines.append(f"- {bullet}")

    lines.extend(
        [
            "",
            "### For a personal second brain",
            _second_brain_verdict(subject_a, subject_b, evidence, analysis),
            "",
            "## Sources",
        ]
    )
    for row in analysis.scored_evidence[:12]:
        lines.append(f"- `[{row.get('citation_id')}]` [{row.get('title')}]({row.get('url')})")

    if synthesis.limitations:
        lines.append("")
        lines.append("## Limitations")
        for lim in synthesis.limitations:
            lines.append(f"- {lim}")

    lines.extend(
        [
            "",
            "---",
            f"**Saved to Research** · `{replay_id}` · open **Mission Control → Research** for timeline and replay.",
        ]
    )
    return "\n".join(lines)


def _best_snippet(evidence: list[ResearchEvidenceItem], subject: str, *, exclude: set[str] | None = None) -> str:
    exclude = exclude or set()
    ranked = sorted(evidence, key=lambda e: _mention_score(e, subject), reverse=True)
    for row in ranked:
        if _mention_score(row, subject) < 1:
            break
        snip = (row.snippet or row.title or "—").strip()
        if snip in exclude:
            continue
        return snip[:160] + ("…" if len(snip) > 160 else "")
    return "—"


def _mention_score_total(evidence: list[ResearchEvidenceItem], subject: str) -> int:
    return sum(_mention_score(e, subject) for e in evidence)


def _second_brain_verdict(
    subject_a: str,
    subject_b: str,
    evidence: list[ResearchEvidenceItem],
    analysis: ConfidenceAnalysis,
) -> str:
    blob = " ".join(f"{e.title} {e.snippet}" for e in evidence).lower()
    wiki_signals = sum(1 for k in ("wiki", "knowledge base", "reference", "notes", "markdown") if k in blob)
    agent_signals = sum(1 for k in ("agent", "assistant", "memory", "personal", "second brain", "gbrain") if k in blob)
    a_count = _mention_score_total(evidence, subject_a)
    b_count = _mention_score_total(evidence, subject_b)
    if agent_signals > wiki_signals + 1 or a_count > b_count * 1.5:
        return (
            f"**{subject_a}** fits better for a personal second brain if you want agent-native memory, "
            "structured capture, and tooling built for AI agents (GBrain extends the Karpathy wiki idea with execution)."
        )
    if wiki_signals > agent_signals + 1 or b_count > a_count * 1.5:
        return (
            f"**{subject_b}** fits better if you prefer a lightweight wiki you curate yourself — "
            "minimal agent overhead, maximum control over notes and structure."
        )
    return (
        "Sources are mixed — neither clearly wins for every personal workflow. "
        "Use the side-by-side table and source links above, then pick based on whether you prioritize "
        "**active assistant behavior** vs **curated reference notes**."
    )
