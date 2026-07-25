# SPDX-License-Identifier: Apache-2.0
"""Simple HTML comparison pages from persisted research replays."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ComparisonContext:
    query: str
    replay_id: str
    subject_a: str
    subject_b: str
    verdict: str
    lean: str
    sources: list[dict[str, str]]
    evidence_a: list[str]
    evidence_b: list[str]


def load_comparison_context(replay_id: str) -> ComparisonContext | None:
    from aethos_core.research.research_artifacts import get_research_artifact
    from aethos_core.research.research_runtime import get_research_replay

    replay = get_research_replay(replay_id)
    if not replay:
        return None
    payload = replay.get("payload") or {}
    plan = payload.get("plan") or {}
    subjects = plan.get("comparison_subjects")
    if not subjects or len(subjects) < 2:
        subjects = _subjects_from_query(str(payload.get("query") or ""))
    if not subjects:
        return None

    subject_a, subject_b = str(subjects[0]), str(subjects[1])
    query = str(payload.get("query") or "")
    artifact_ids = list(payload.get("artifact_ids") or [])

    evidence_rows: list[dict[str, Any]] = []
    synthesis: dict[str, Any] = {}
    for aid in artifact_ids:
        art = get_research_artifact(str(aid))
        if not art:
            continue
        if art.get("artifact_type") == "research_result_set":
            evidence_rows = list((art.get("payload") or {}).get("evidence") or [])
        if art.get("artifact_type") == "research_synthesis":
            synthesis = dict((art.get("payload") or {}).get("synthesis") or {})

    sources = [
        {
            "title": str(row.get("title") or "Source"),
            "url": str(row.get("url") or ""),
            "citation_id": str(row.get("citation_id") or ""),
        }
        for row in evidence_rows[:12]
        if row.get("url")
    ]

    bullets = list(synthesis.get("bullets") or [])
    lean = subject_a
    for b in bullets:
        if "Lean for this question:" in b:
            lean = b.split(":", 1)[-1].strip().strip("*")
            break

    verdict = _verdict_text(subject_a, subject_b, lean, bullets)
    ev_a, ev_b = _split_evidence_snippets(evidence_rows, subject_a, subject_b)

    return ComparisonContext(
        query=query,
        replay_id=replay_id,
        subject_a=subject_a,
        subject_b=subject_b,
        verdict=verdict,
        lean=lean,
        sources=sources,
        evidence_a=ev_a,
        evidence_b=ev_b,
    )


def build_comparison_html(ctx: ComparisonContext) -> str:
    a = html.escape(ctx.subject_a)
    b = html.escape(ctx.subject_b)
    q = html.escape(ctx.query)
    verdict = html.escape(ctx.verdict)
    lean = html.escape(ctx.lean)

    def li(items: list[str]) -> str:
        if not items:
            return "<li><em>No distinct snippet captured.</em></li>"
        return "".join(f"<li>{html.escape(x)}</li>" for x in items[:4])

    source_links = "".join(
        f'<li><a href="{html.escape(s["url"])}" target="_blank" rel="noopener">'
        f'[{html.escape(s["citation_id"] or "src")}] {html.escape(s["title"][:80])}</a></li>'
        for s in ctx.sources[:10]
    )

    def card_class(subject: str) -> str:
        lean_l = ctx.lean.lower()
        subj_l = subject.lower()
        if lean_l and lean_l not in ("depends on your workflow",):
            if lean_l in subj_l or subj_l in lean_l:
                return "card winner"
            if lean_l.split()[0][:6] in subj_l:
                return "card winner"
        return "card"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{a} vs {b}</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; background: #0f1115; color: #e8eaed; }}
    body {{ max-width: 920px; margin: 0 auto; padding: 24px; line-height: 1.5; }}
    h1 {{ font-size: 1.6rem; margin-bottom: 0.25rem; }}
    .muted {{ color: #9aa0a6; font-size: 0.95rem; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 24px 0; }}
    .card {{ background: #1a1d24; border: 1px solid #2a2f3a; border-radius: 12px; padding: 16px; }}
    .card h2 {{ margin: 0 0 8px; font-size: 1.1rem; }}
    .winner {{ border-color: #34d399; box-shadow: 0 0 0 1px #34d39944; }}
    .verdict {{ background: #152238; border: 1px solid #2563eb55; border-radius: 12px; padding: 16px; margin: 16px 0; }}
    ul {{ padding-left: 1.2rem; }}
    a {{ color: #7dd3fc; }}
    @media (max-width: 720px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <h1>Personal second brain comparison</h1>
  <p class="muted">{q}</p>
  <div class="verdict">
    <strong>Recommendation:</strong> {verdict}<br />
    <span class="muted">Lean → {lean}</span>
  </div>
  <div class="grid">
    <div class="{card_class(ctx.subject_a)}">
      <h2>{a}</h2>
      <p class="muted">Agent-style memory layer · opinionated brain for AI agents</p>
      <ul>{li(ctx.evidence_a)}</ul>
    </div>
    <div class="{card_class(ctx.subject_b)}">
      <h2>{b}</h2>
      <p class="muted">Curated wiki / reference notes · Karpathy-style LLM knowledge pattern</p>
      <ul>{li(ctx.evidence_b)}</ul>
    </div>
  </div>
  <h2>Sources</h2>
  <ul>{source_links or "<li><em>No sources stored.</em></li>"}</ul>
  <p class="muted">Replay: {html.escape(ctx.replay_id)}</p>
</body>
</html>"""


def persist_comparison_html(*, replay_id: str, html: str) -> dict[str, str]:
    """Write comparison page to disk under research artifacts."""
    from aethos_core.config import get_settings

    rid = (replay_id or "").strip()
    if not rid:
        return {"ok": "false", "error": "replay_id_required"}
    settings = get_settings()
    root = Path(settings.research_artifacts_dir).expanduser()
    out_dir = root / "comparisons"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"comparison-{rid}.html"
    path = out_dir / filename
    path.write_text(html, encoding="utf-8")
    public_path = _mirror_comparison_to_web_public(replay_id=rid, html=html)
    public_url = comparison_html_public_url(rid)
    return {
        "ok": "true",
        "filename": filename,
        "path": str(path),
        "replay_id": rid,
        "public_url": public_url,
        "web_public_path": public_path or "",
    }


def load_persisted_comparison_html_path(replay_id: str) -> Path | None:
    from aethos_core.config import get_settings

    rid = (replay_id or "").strip()
    if not rid:
        return None
    settings = get_settings()
    path = Path(settings.research_artifacts_dir).expanduser() / "comparisons" / f"comparison-{rid}.html"
    return path if path.is_file() else None


def comparison_html_public_url(replay_id: str) -> str:
    """Public URL for comparison page — CDN base when configured, else API path."""
    from aethos_core.config import get_settings

    rid = (replay_id or "").strip()
    if not rid:
        return ""
    settings = get_settings()
    base = (settings.comparison_html_public_base_url or "").strip().rstrip("/")
    if base:
        return f"{base}/comparisons/comparison-{rid}.html"
    return f"/api/v1/research/comparison-html/{rid}"


def _mirror_comparison_to_web_public(*, replay_id: str, html: str) -> str | None:
    from aethos_core.config import get_settings

    settings = get_settings()
    if not getattr(settings, "comparison_html_mirror_web_public", False):
        return None
    rid = (replay_id or "").strip()
    if not rid:
        return None
    out_dir = Path("web/public/comparisons").expanduser()
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"comparison-{rid}.html"
        path = out_dir / filename
        path.write_text(html, encoding="utf-8")
        return f"/comparisons/{filename}"
    except OSError:
        return None


def _subjects_from_query(query: str) -> tuple[str, str] | None:
    from aethos_core.research.planner import extract_comparison_subjects

    return extract_comparison_subjects(query)


def _split_evidence_snippets(
    rows: list[dict[str, Any]], subject_a: str, subject_b: str
) -> tuple[list[str], list[str]]:
    def score(row: dict[str, Any], phrase: str) -> int:
        blob = f"{row.get('title') or ''} {row.get('snippet') or ''}".lower()
        return sum(1 for t in phrase.lower().split() if len(t) > 2 and t in blob)

    ranked_a = sorted(rows, key=lambda r: score(r, subject_a), reverse=True)
    ranked_b = sorted(rows, key=lambda r: score(r, subject_b), reverse=True)
    a_snips: list[str] = []
    b_snips: list[str] = []
    used: set[str] = set()

    for row in ranked_a:
        if score(row, subject_a) < 1:
            break
        snip = (str(row.get("snippet") or row.get("title") or "")).strip()[:200]
        if snip and snip not in used:
            a_snips.append(snip)
            used.add(snip)
            break
    for row in ranked_b:
        if score(row, subject_b) < 1:
            break
        snip = (str(row.get("snippet") or row.get("title") or "")).strip()[:200]
        if snip and snip not in used:
            b_snips.append(snip)
            used.add(snip)
            break
    return a_snips, b_snips


def _verdict_text(subject_a: str, subject_b: str, lean: str, bullets: list[str]) -> str:
    if lean and lean not in ("depends on your workflow", subject_a, subject_b):
        if subject_a.lower() in lean.lower() or lean.lower() in subject_a.lower():
            return (
                f"For most personal second-brain workflows that prioritize an agent memory layer, "
                f"{subject_a} is the stronger fit based on source signal."
            )
        if subject_b.lower() in lean.lower() or lean.lower() in subject_b.lower():
            return (
                f"For curated reference notes and a wiki-first workflow, "
                f"{subject_b} aligns better with the evidence gathered."
            )
    return (
        f"Pick {subject_a} if you want agent-native memory and tooling; "
        f"pick {subject_b} if you prefer a structured wiki you maintain yourself."
    )
