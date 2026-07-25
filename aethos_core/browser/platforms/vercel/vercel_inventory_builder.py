# SPDX-License-Identifier: Apache-2.0
"""Build Vercel inventory artifacts and operator-facing summaries."""

from __future__ import annotations

import json
from typing import Any

from aethos_core.browser.platforms.vercel.vercel_dom_parser import (
    ParseProjectsResult,
    build_extraction_debug,
    parse_projects_from_page,
)
from aethos_core.browser.platforms.vercel.vercel_entities import (
    HealthState,
    VercelInventoryArtifact,
    VercelProject,
)
from aethos_core.browser.platforms.vercel.vercel_health_classifier import (
    display_attention_label,
    enrich_inventory,
    operator_display_label,
)


def build_inventory_from_page(
    page: Any,
    *,
    known_projects: list[str] | None = None,
    memory_context: dict[str, dict] | None = None,
    page_url: str = "",
    page_title: str = "",
    visible_text: str = "",
    drilldown: bool = True,
) -> tuple[VercelInventoryArtifact, str]:
    parsed: ParseProjectsResult = parse_projects_from_page(
        page,
        known_projects=known_projects,
        memory_context=memory_context,
        page_url=page_url,
        page_title=page_title,
    )
    projects = list(parsed.projects)
    if drilldown and projects and not parsed.memory_fallback:
        from aethos_core.browser.platforms.vercel.vercel_detail_inspector import (
            enrich_projects_from_detail_pages,
        )

        projects = enrich_projects_from_detail_pages(
            page,
            projects,
            page_url=page_url,
            max_visits=5,
        )
        parsed.projects = projects
    debug = build_extraction_debug(
        page_url=page_url,
        page_title=page_title,
        parsed=parsed,
        visible_text_excerpt=visible_text,
        known_memory_projects=list(known_projects or []),
    )
    artifact = build_inventory_artifact(
        parsed.projects,
        extraction_method=parsed.extraction_method,
        ignored_labels=parsed.ignored_labels,
        low_confidence_count=parsed.low_confidence_count,
        likely_project_names=[p.name for p in parsed.likely_projects],
        memory_fallback=parsed.memory_fallback,
        extraction_debug=debug,
    )
    return artifact, parsed.extraction_method


def build_inventory_artifact(
    projects: list[VercelProject],
    *,
    extraction_method: str,
    ignored_labels: list[str] | None = None,
    low_confidence_count: int = 0,
    likely_project_names: list[str] | None = None,
    memory_fallback: bool = False,
    extraction_debug: dict[str, Any] | None = None,
) -> VercelInventoryArtifact:
    artifact = VercelInventoryArtifact(
        projects=projects,
        extraction_method=extraction_method,
        ignored_labels=list(ignored_labels or []),
        low_confidence_count=low_confidence_count,
        likely_project_names=list(likely_project_names or []),
        memory_fallback=memory_fallback,
        extraction_debug=extraction_debug,
    )
    return enrich_inventory(artifact)


def inventory_confidence_lines(artifact: VercelInventoryArtifact) -> list[str]:
    """Consistent confirmed/likely terminology for chat + Mission Control."""
    n = len(artifact.projects)
    if n == 0:
        return []

    if artifact.memory_fallback:
        return [
            f"Using **{n}** project{'s' if n != 1 else ''} **known from memory** "
            "(page re-extraction failed)",
        ]

    confirmed = sum(1 for p in artifact.projects if (p.environment or "") != "likely")
    likely_n = len(artifact.likely_project_names)
    if likely_n == 0 and confirmed < n:
        likely_n = n - confirmed

    if confirmed == n and likely_n == 0:
        return [f"Found **{n}** confirmed Vercel project{'s' if n != 1 else ''}"]

    lines = [f"Found **{n}** Vercel project{'s' if n != 1 else ''}:"]
    if confirmed:
        lines.append(f"- **{confirmed}** confirmed from project-specific signals")
    if likely_n:
        lines.append(f"- **{likely_n}** likely from dashboard links")
    if artifact.low_confidence_count:
        lines.append(
            f"- **{artifact.low_confidence_count}** low confidence (excluded from inventory)"
        )
    if artifact.ignored_labels:
        lines.append(f"- **{len(artifact.ignored_labels)}** ignored UI labels")
    return lines


def build_operational_summary(artifact: VercelInventoryArtifact) -> str:
    """Human operator summary — transparent when extraction is weak."""
    n = len(artifact.projects)

    if artifact.memory_fallback and n:
        lines = [
            "I could not confidently re-extract projects from the current Vercel page, "
            f"but I have **{n}** previously confirmed project{'s' if n != 1 else ''} in memory:",
            "",
            "**Known Vercel projects (memory — stale until next successful inspection):**",
        ]
        for p in artifact.projects[:20]:
            lines.append(f"- {p.name}")
        if n > 20:
            lines.append(f"- …and {n - 20} more")
        lines.append("")
        lines.append(
            "_Source: operational memory fallback · Freshness: stale until next successful inspection_"
        )
        lines.append("")
        lines.append("Open **Mission Control → Jobs** for extraction debug and pipeline counts.")
        return "\n".join(lines).strip()

    if n == 0:
        return _empty_extraction_summary(artifact)

    conf_lines = inventory_confidence_lines(artifact)
    lines = conf_lines + [""] if conf_lines else [f"I found **{n}** Vercel project{'s' if n != 1 else ''}.", ""]

    if not artifact.memory_fallback and not conf_lines:
        lines = [f"I found **{n}** Vercel project{'s' if n != 1 else ''}.", ""]

    if artifact.memory_fallback:
        pass
    elif len(conf_lines) == 1 and conf_lines[0].startswith("Found") and "likely" not in conf_lines[0]:
        pass
    elif any("likely" in ln for ln in conf_lines):
        lines.append(
            "Reply with `yes these are projects` to confirm likely names, "
            "or name corrections (e.g. `cdn is not a project`)."
        )
        lines.append("")

    if artifact.low_confidence_count and not any("low confidence" in ln for ln in conf_lines):
        lines.append(
            f"I ignored **{artifact.low_confidence_count}** low-confidence Vercel UI labels "
            "(navigation, metrics, product areas)."
        )
        lines.append("")

    hs = artifact.health_summary
    by_name = {p.name: p for p in artifact.projects}

    strict_healthy = [n for n in hs.healthy if n not in hs.likely_healthy]
    if strict_healthy:
        lines.append("**Healthy:**")
        for name in strict_healthy[:15]:
            p = by_name.get(name)
            url = f" ({p.production_url})" if p and p.production_url else ""
            lines.append(f"- {name}{url}")
        if len(strict_healthy) > 15:
            lines.append(f"- …and {len(strict_healthy) - 15} more")
        lines.append("")

    if hs.likely_healthy:
        lines.append("**Likely healthy:**")
        for name in hs.likely_healthy[:12]:
            p = by_name.get(name)
            url = f" ({p.production_url})" if p and p.production_url else ""
            lines.append(f"- {name}{url}")
        lines.append("")

    if hs.unknown:
        lines.append("**Production status unclear:**")
        for name in hs.unknown[:15]:
            p = by_name.get(name)
            label = display_attention_label(p) if p else "production status not confirmed"
            lines.append(f"- {name} ({label})")
        if len(hs.unknown) > 15:
            lines.append(f"- …and {len(hs.unknown) - 15} more")
        lines.append("")

    needs: list[str] = []
    seen: set[str] = set()
    for p in artifact.projects:
        if p.operator_status == "needs_attention" or p.health in (
            HealthState.FAILED,
            HealthState.LIKELY_DEGRADED,
            HealthState.DEGRADED,
        ):
            line = operator_display_label(p)
            if line not in seen:
                seen.add(line)
                needs.append(line)

    if needs:
        lines.append("**Needs attention:**")
        for line in needs[:12]:
            lines.append(f"- {line}")
        if len(needs) > 12:
            lines.append(f"- …and {len(needs) - 12} more")
        lines.append("")

    delta = artifact.memory_delta or {}
    not_visible = delta.get("known_not_visible") or []
    if not_visible:
        lines.append("**Known but not visible this run:**")
        for name in not_visible[:12]:
            lines.append(f"- {name}")
        if len(not_visible) > 12:
            lines.append(f"- …and {len(not_visible) - 12} more")
        lines.append("")

    newly = delta.get("newly_detected_this_run") or []
    if newly:
        lines.append("**Newly detected this run:**")
        for name in newly[:12]:
            lines.append(f"- {name}")
        lines.append("")

    if artifact.ignored_labels:
        sample = ", ".join(f"`{x}`" for x in artifact.ignored_labels[:8])
        extra = f" (+{len(artifact.ignored_labels) - 8} more)" if len(artifact.ignored_labels) > 8 else ""
        lines.append(f"_Ignored low-confidence labels:_ {sample}{extra}")
        lines.append("")

    lines.append("Open **Mission Control → Jobs** for deployment metadata and optional debug extraction.")
    return "\n".join(lines).strip()


def _empty_extraction_summary(artifact: VercelInventoryArtifact) -> str:
    dbg = artifact.extraction_debug or {}
    pipeline = dbg.get("pipeline") or {}
    lines = [
        "I reached the Vercel dashboard, but I could not confidently identify project cards on this page.",
        "",
        "**Possible reasons:**",
        "- dashboard still loading",
        "- saved session lacks access to the team project list",
        "- Vercel layout changed",
        "- AethOS is on the wrong page (not the Projects grid)",
        "",
    ]
    if pipeline:
        lines.append("**Extraction pipeline:**")
        lines.append(f"- Raw links: {pipeline.get('raw_links_seen', 0)}")
        lines.append(f"- Project-like links: {pipeline.get('project_like_links_seen', 0)}")
        lines.append(f"- Candidates: {pipeline.get('candidate_names_seen', 0)}")
        lines.append(f"- After confidence: {pipeline.get('candidates_after_confidence', 0)}")
        if not pipeline.get("dashboard_ready"):
            lines.append("- Dashboard ready signal: not detected")
        lines.append("")

    known = dbg.get("known_memory_projects") or []
    if known:
        lines.append(
            f"_Memory has {len(known)} known projects but DOM extraction returned none on this page._"
        )
        lines.append("")

    lines.append(
        "Try opening the Vercel **Projects** page in a supervised browser session, then run inspection again."
    )
    lines.append("")
    lines.append("Open **Mission Control → Jobs** for the collapsed extraction debug artifact.")
    return "\n".join(lines).strip()


def build_chat_summary_bullets(artifact: VercelInventoryArtifact) -> str:
    n = len(artifact.projects)
    if n == 0:
        return (
            "- Could not identify Vercel projects on this page\n"
            "- See Mission Control → Jobs for why (extraction debug)"
        )
    if artifact.memory_fallback:
        lines = [
            f"- Using **{n}** known projects from memory (page re-extraction failed)",
            "- Freshness: stale until next successful inspection",
        ]
        preview = ", ".join(p.name for p in artifact.projects[:6])
        if preview:
            extra = f" (+{n - 6} more)" if n > 6 else ""
            lines.append(f"- {preview}{extra}")
        lines.append("- Open Mission Control → Jobs for debug details")
        return "\n".join(lines)

    conf_lines = inventory_confidence_lines(artifact)
    lines: list[str] = []
    for ln in conf_lines:
        bullet = ln.replace("**", "")
        if not bullet.startswith("- "):
            bullet = f"- {bullet}"
        lines.append(bullet)

    if not lines:
        lines = [f"- Found {n} Vercel project{'s' if n != 1 else ''}"]
    hs = artifact.health_summary
    if hs.healthy:
        lines.append(f"- {len(hs.healthy)} healthy (confirmed production)")
    if hs.likely_healthy:
        lines.append(f"- {len(hs.likely_healthy)} likely healthy")
    if hs.unknown:
        lines.append(f"- {len(hs.unknown)} production status unclear")
    needs_n = sum(1 for p in artifact.projects if p.operator_status == "needs_attention")
    if needs_n:
        lines.append(f"- {needs_n} need attention (preview/latest deploy — not necessarily production down)")
    if artifact.failing_count:
        lines.append(f"- {artifact.failing_count} production down / failed")
    if hs.likely_degraded or artifact.degraded_count:
        d = len(hs.likely_degraded) or artifact.degraded_count
        lines.append(f"- {d} likely need attention")
    preview = ", ".join(p.name for p in artifact.projects[:6])
    if preview:
        extra = f" (+{n - 6} more)" if n > 6 else ""
        lines.append(f"- {preview}{extra}")
    lines.append("- Open Mission Control → Jobs for the full structured report")
    return "\n".join(lines)


def build_full_inventory_report(
    *,
    title: str,
    job_type: str,
    profile_id: str,
    site: str,
    page_title: str,
    url: str,
    artifact: VercelInventoryArtifact,
    login_wall: bool,
    debug_excerpt: str | None = None,
    known_projects: list[str] | None = None,
    auth_method: str = "Saved browser session",
    tool_used: str = "vercel_readonly_inspector",
    platform: str = "vercel_semantic",
    browser_used: bool | None = None,
    provider_used: str = "none",
    masked_credential: str | None = None,
) -> str:
    if browser_used is None:
        browser_used = auth_method.lower().find("api token") < 0 and tool_used != "vercel_api"
    credential_ref = masked_credential or profile_id
    lines = [
        f"# {title}",
        "",
        f"- **Tool:** `{tool_used}`",
        f"- **Platform:** `{platform}`",
        f"- **Auth method:** {auth_method}",
        f"- **Credential:** `{credential_ref}`",
        f"- **Browser used:** {'yes' if browser_used else 'no'}",
        f"- **Provider used:** {provider_used}",
        f"- **Inspection type:** `{job_type}`",
        f"- **Site:** `{site}`",
        f"- **Extraction:** `{artifact.extraction_method}`",
        f"- **Project count:** {len(artifact.projects)}",
    ]
    if artifact.memory_fallback:
        lines.append("- **Source:** operational memory fallback")
        lines.append("- **Freshness:** stale until next successful inspection")
    if known_projects:
        lines.append(f"- **Known projects (memory):** {len(known_projects)}")
    delta = artifact.memory_delta or {}
    not_visible = delta.get("known_not_visible") or []
    if not_visible:
        preview = ", ".join(not_visible[:6])
        extra = f" (+{len(not_visible) - 6} more)" if len(not_visible) > 6 else ""
        lines.append(
            f"- **Known but not visible this run:** {len(not_visible)} ({preview}{extra})"
        )
    if delta.get("newly_detected_this_run"):
        lines.append(
            f"- **Newly detected:** {', '.join(delta['newly_detected_this_run'][:8])}"
        )
    lines.append("")

    if login_wall:
        lines.extend(["## Session status", "", "Saved session appears expired or logged out.", ""])
        return "\n".join(lines)

    if artifact.extraction_method == "vercel_api" and artifact.extraction_debug:
        api_projects = artifact.extraction_debug.get("api_projects") or []
        if api_projects:
            lines.extend(["## API-backed project records", ""])
            for rec in api_projects[:50]:
                lines.append(
                    f"- **{rec.get('name')}** · id `{rec.get('id')}` · framework `{rec.get('framework') or '—'}` · "
                    f"targets {', '.join(rec.get('targets') or []) or '—'} · "
                    f"production `{rec.get('latest_production_state')}` · "
                    f"repo `{rec.get('repo_link') or '—'}`"
                )
            lines.append("")

    if artifact.extraction_debug and artifact.extraction_method != "vercel_api":
        dbg = artifact.extraction_debug
        pl = dbg.get("pipeline") or {}
        lines.extend(
            [
                "## Extraction pipeline",
                "",
                f"- Raw links: {pl.get('raw_links_seen', 0)}",
                f"- Project-like links: {pl.get('project_like_links_seen', 0)}",
                f"- Candidate names: {pl.get('candidate_names_seen', 0)}",
                f"- After nav filter: {pl.get('candidates_after_nav_filter', 0)}",
                f"- After confidence: {pl.get('candidates_after_confidence', 0)}",
                f"- Confirmed: {pl.get('confirmed_projects', 0)}",
                f"- Likely: {pl.get('likely_projects', 0)}",
                f"- Low confidence ignored: {pl.get('low_confidence_ignored', 0)}",
                f"- Memory matches: {pl.get('known_memory_matches', 0)}",
                f"- Dashboard ready: {pl.get('dashboard_ready', False)}"
                + (f" ({pl.get('dashboard_ready_signal')})" if pl.get("dashboard_ready_signal") else ""),
                "",
            ]
        )

    hs = artifact.health_summary
    lines.extend(
        [
            "## Operational health",
            "",
            f"- **Healthy:** {len([n for n in hs.healthy if n not in hs.likely_healthy])}",
            f"- **Likely healthy:** {len(hs.likely_healthy)}",
            f"- **Unknown / unclear:** {len(hs.unknown)}",
            f"- **Needs attention:** {len(hs.needs_attention)}",
            f"- **Failed:** {len(hs.failed)}",
            f"- **Likely degraded:** {len(hs.likely_degraded)}",
            "",
            "## Project inventory",
            "",
            "| Project | Operator | Prod health | Latest deploy | URL type | Production | Note |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if artifact.projects:
        for p in artifact.projects:
            note = display_attention_label(p) or ("memory fallback" if artifact.memory_fallback else "—")
            latest = f"{p.latest_deployment_state}/{p.latest_deployment_scope}"
            lines.append(
                f"| {p.name} | {p.operator_status} | {p.production_health} | {latest} | "
                f"{p.url_type} | {p.production_url or '—'} | {note} |"
            )
    else:
        lines.append("| (none) | — | — | — | — | — |")

    lines.extend(
        [
            "",
            f"- **Page title:** {page_title or '(empty)'}",
            f"- **URL:** {url}",
            "",
            "## Safety",
            "",
            "Read-only inspection — mutations are not enabled.",
        ]
    )

    if len(artifact.projects) == 0 or artifact.extraction_debug:
        lines.extend(
            [
                "",
                "## Extraction debug",
                "",
                "_Collapsed in Mission Control. Diagnostic JSON for zero/low extraction._",
                "",
                "```json",
                json.dumps(artifact.extraction_debug or {}, indent=2)[:6000],
                "```",
            ]
        )

    if debug_excerpt and debug_excerpt.strip():
        lines.extend(
            [
                "",
                "## Debug extraction",
                "",
                "_Collapsed in Mission Control. Raw page text for troubleshooting only._",
                "",
                "```",
                debug_excerpt.strip()[:4000],
                "```",
            ]
        )
    return "\n".join(lines)
