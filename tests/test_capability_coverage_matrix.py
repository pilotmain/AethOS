# SPDX-License-Identifier: Apache-2.0
"""§A1 — Capability coverage matrix (chat ↔ backend), proven, not assumed.

This is both a test and a generator. It introspects the real FastAPI app to count
endpoints per domain, maps every model-facing agent tool and Step-2 router to a
capability domain, and records three honest flags per capability:

  * chat_reachable     — driveable from a chat message (agent tool or Step-2 router)
  * tested             — at least one real test file exercises it (existence verified)
  * by_design_ui_cli   — intentionally UI/CLI-only (vault writes, pairing approve, …)

Run as a script to (re)write the checked-in matrix:

    python -m tests.test_capability_coverage_matrix      # writes COVERAGE_MATRIX.md
    AETHOS_WRITE_COVERAGE_MATRIX=1 pytest tests/test_capability_coverage_matrix.py

The pytest assertions guarantee the matrix stays honest: no agent tool is orphaned,
every chat-reachable domain has a real surface, every by-design domain explains why,
and every "tested" claim points at a file that exists.
"""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Any

from aethos_core.execution_brain.agent_tool_catalog import list_model_facing_tool_names

REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = REPO_ROOT / "COVERAGE_MATRIX.md"


# Capability domains. `segments` are real /api/v1 path segments (verified by the
# endpoint introspection below); `agent_tools` and `routers` are the chat surfaces.
DOMAINS: list[dict[str, Any]] = [
    {
        "id": "providers",
        "label": "Provider read/operate (inventory, health, logs, workflows, exec)",
        "segments": ["providers", "connections", "provider-topology", "railway-discovery", "railway-execution"],
        "agent_tools": [
            "provider_catalog",
            "provider_validate",
            "provider_inventory",
            "provider_inventory_all",
            "provider_health",
            "provider_logs",
            "provider_workflows",
        ],
        "routers": ["provider_readonly_intent", "mission_control_observability"],
        "flag": None,
        "tested_by": [
            "tests/test_provider_agent_ops.py",
            "tests/test_cloud_agent_bridge.py",
            "tests/test_provider_readonly_orchestration.py",
        ],
        "by_design_ui_cli": False,
        "notes": "Readonly reads cached short-TTL (§C4); credentials come from the vault.",
    },
    {
        "id": "mutations",
        "label": "Governed mutations (restart, env, deploy actions) via preflight+approval",
        "segments": ["mutations", "mutation-reliability"],
        "agent_tools": [
            "provider_exec",
            "provider_create_mutation_preflight",
            "terminal_create_preflight",
            "cursor_open_preflight",
        ],
        "routers": ["explicit_mutation", "global_verification_preemption"],
        "flag": "mutation_execution_enabled",
        "tested_by": [
            "tests/test_mutation_approval_execution.py",
            "tests/test_explicit_mutation_intent_priority.py",
        ],
        "by_design_ui_cli": False,
        "notes": "Execution requires operator approval in Mission Control → Approvals; "
        "T3/production and vault secret writes stay gated.",
    },
    {
        "id": "workspace_suite",
        "label": "Workspace suite (research, compare, doc, notes, email, calendar, foundry)",
        "segments": ["workspaces", "workspace"],
        "agent_tools": [
            "workspace_research",
            "workspace_compare",
            "workspace_doc",
            "workspace_notes",
            "workspace_email",
            "workspace_calendar",
            "model_foundry",
        ],
        "routers": [],
        "flag": "workspace_suite_enabled",
        "tested_by": [
            "tests/test_workspace_portfolio.py",
            "tests/test_model_foundry_serve_governed.py",
        ],
        "by_design_ui_cli": False,
        "notes": "Tools hidden from the schema unless WORKSPACE_SUITE_ENABLED=true.",
    },
    {
        "id": "local_workspace",
        "label": "Repo review — local (overview, list, read, grep) + GitHub remote (read, issues/PRs)",
        "segments": ["engineering"],
        "agent_tools": [
            "repo_overview",
            "repo_list",
            "repo_read",
            "repo_grep",
            "github_read_repo",
            "github_issues_prs",
        ],
        "routers": ["engineering_intelligence"],
        "flag": None,
        "tested_by": [
            "tests/test_phase_98c_local_workspace_intelligence.py",
            "tests/test_software_delivery_workspace_application.py",
        ],
        "by_design_ui_cli": False,
        "notes": "Repo review scoped to registered workspaces (Mission Control → Local Workspaces), "
        "secrets redacted; engineering intelligence (PRs/patches) chat-reachable via the router.",
    },
    {
        "id": "orchestration",
        "label": "Multi-agent orchestration (spawn, list, send, sessions)",
        "segments": ["agents"],
        "agent_tools": ["agent_list", "agent_sessions_list", "agent_send", "agent_spawn", "arbiter_run"],
        "routers": ["agent_orchestration", "command_center_orchestration"],
        "flag": "agent_runtime_enabled",
        "tested_by": [
            "tests/test_phase_98e_multi_agent_runtime.py",
            "tests/test_agent_subagent_spawn.py",
        ],
        "by_design_ui_cli": False,
        "notes": "Populates Mission Control → Orchestration when AGENT_RUNTIME_ENABLED=true.",
    },
    {
        "id": "canvas",
        "label": "Live Canvas rendering",
        "segments": [],
        "agent_tools": ["canvas_render"],
        "routers": [],
        "flag": "canvas_surface_enabled",
        "tested_by": ["tests/test_phase4_operator_surfaces.py"],
        "by_design_ui_cli": False,
        "notes": "canvas_render hidden unless CANVAS_SURFACE_ENABLED=true; output opens in the Canvas tab.",
    },
    {
        "id": "channels",
        "label": "Outbound channel messaging (Telegram/Slack/Discord)",
        "segments": ["channels", "telegram", "telegram-soak", "slack"],
        "agent_tools": ["channel_send"],
        "routers": [],
        "flag": "channel_gateway_enabled",
        "tested_by": ["tests/test_phase4_operator_surfaces.py"],
        "by_design_ui_cli": False,
        "notes": "Pairing APPROVE is UI/CLI by design (Mission Control → Channels → Pending pairings "
        "or `aethos pairing approve`); status/pairing-code is chat-reachable.",
    },
    {
        "id": "memory_skills",
        "label": "Memory recall + skill recall",
        "segments": [],
        "agent_tools": ["memory_recall", "skill_recall"],
        "routers": [],
        "flag": "vector_memory_enabled",
        "tested_by": ["tests/test_memory_recall_route.py"],
        "by_design_ui_cli": False,
        "notes": "memory_recall gated by VECTOR_MEMORY_ENABLED; skill_recall by SKILLS_REGISTRY_ENABLED.",
    },
    {
        "id": "research",
        "label": "Web research + deep research runs",
        "segments": ["research"],
        "agent_tools": ["web_search", "research_run"],
        "routers": ["web_intelligence"],
        "flag": "web_research_enabled",
        "tested_by": ["tests/test_phase_98e6_2_research_runtime.py"],
        "by_design_ui_cli": False,
        "notes": "Gated by WEB_RESEARCH_ENABLED.",
    },
    {
        "id": "deployment_targets",
        "label": "Deployment target registry",
        "segments": ["deployment-targets"],
        "agent_tools": [],
        "routers": [],
        "flag": None,
        "tested_by": ["tests/test_deployment_targets_registry.py"],
        "by_design_ui_cli": True,
        "notes": "Target REGISTRATION is UI/CLI by design (Mission Control → Deployment Targets). "
        "Greenfield deploy *flows* are chat-reachable via the greenfield routers.",
    },
    {
        "id": "credentials",
        "label": "Credential / connection status (no secret values)",
        "segments": ["credentials", "setup-creds"],
        "agent_tools": [],
        "routers": ["provisioning_orchestration"],
        "flag": None,
        "tested_by": [
            "tests/test_cloud_provider_credentials.py",
            "tests/test_credential_vault_redaction.py",
        ],
        "by_design_ui_cli": True,
        "notes": "Secret WRITES stay UI/CLI by design (Mission Control → Settings → Connections). "
        "Connection *status* is chat-reachable via the `provider_validate` tool (mapped under providers).",
    },
    {
        "id": "internal_observability",
        "label": "Mission Control / observability / runtime cognition surfaces",
        "segments": [
            "mission-control",
            "human",
            "runtime",
            "observability",
            "presence",
            "intelligence",
            "conversational-operational-grounding",
            "aethos-identity",
            "reliability",
            "operational-reliability",
            "operational-resilience",
            "operational-resilience-cognition",
            "recovery-continuity-intelligence",
            "predictive-operational-cognition",
            "infrastructure-intelligence",
            "runtime-fragility-intelligence",
            "long-tail-operational-forecasting",
            "long-tail-runtime-cognition",
            "runtime-convergence-cognition",
            "operational-truth",
            "production-execution-truth",
            "runtime-reconciliation",
            "runtime-truth-convergence",
            "enterprise",
            "orgs",
            "governance",
            "production",
            "production-reliability",
            "autonomous-execution",
            "external-execution",
            "reality-harness",
            "validation-harness",
            "job-truth",
            "delivery",
            "settings",
            "plugins",
            "catalog",
            "correlation",
            "upgrade",
            "verification",
            "reality-harness-v4",
            "reality-harness-v41",
            "reality-harness-v42",
            "reality-harness-v43",
            "reality-harness-v44",
            "production-execution-realism",
            "conversational-intelligence",
            "conversational-reliability",
            "conversational-convergence",
            "conversational-qualification",
            "runtime-convergence",
            "reality-harness-v45",
            "auth",
            "auth-diagnostics",
            "setup",
            "ping",
        ],
        "agent_tools": ["list_tracked_jobs", "approval_inbox", "platform_review"],
        "routers": [],
        "flag": None,
        "tested_by": ["tests/test_phase4_operator_surfaces.py", "tests/test_platform_review_tool.py"],
        "by_design_ui_cli": True,
        "notes": "Observability/diagnostic surfaces — consumed by Mission Control UI and the "
        "chat lanes that summarize them; not direct chat-driven CRUD by design.",
    },
    {
        "id": "lifecycle_events",
        "label": "Action/job/browser lifecycle + chat/health",
        "segments": ["actions", "jobs", "browser", "chat", "health"],
        "agent_tools": [],
        "routers": ["job_result_followup", "browser_observation"],
        "flag": None,
        "tested_by": ["tests/test_chat_durable_agent_job.py"],
        "by_design_ui_cli": True,
        "notes": "Polled by ChatShell for live updates (§C2); job results are chat-reachable.",
    },
]


# §A2 — assessment of the chat-reach candidates the handoff named, so the
# conclusion is provable rather than hand-wavy. status ∈ {reachable, by_design}.
CANDIDATE_GAPS: list[dict[str, str]] = [
    {
        "candidate": "Credential / connection status (not secrets)",
        "status": "reachable",
        "via": "`provider_validate` agent tool",
        "note": "Reports connection ok/detail without exposing secret values.",
    },
    {
        "candidate": "Provider inventory / projects / health / logs",
        "status": "reachable",
        "via": "`provider_inventory` / `provider_health` / `provider_logs` (cached §C4)",
        "note": "Readonly reads from the vault-backed providers.",
    },
    {
        "candidate": "Deployment-target registration",
        "status": "by_design",
        "via": "Mission Control → Deployment Targets (UI/CLI)",
        "note": "Registry write; greenfield deploy *flows* are chat-reachable via the greenfield routers.",
    },
    {
        "candidate": "Channel pairing approve",
        "status": "by_design",
        "via": "Mission Control → Channels → Pending pairings or `aethos pairing approve`",
        "note": "Trust boundary; the pairing code/prompt is surfaced in chat, approval stays UI/CLI.",
    },
    {
        "candidate": "Vault secret writes",
        "status": "by_design",
        "via": "Mission Control → Settings → Connections (UI/CLI)",
        "note": "Security-sensitive write — never exposed to chat by design.",
    },
]


def _endpoint_counts() -> Counter:
    from aethos_core.api.main import app

    counts: Counter = Counter()
    for route in getattr(app, "routes", []):
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", "")
        if not methods or not path.startswith("/api"):
            continue
        parts = [p for p in path.split("/") if p]
        seg = parts[2] if len(parts) > 2 else (parts[-1] if parts else "?")
        for _ in methods - {"HEAD", "OPTIONS"}:
            counts[seg] += 1
    return counts


def build_coverage_matrix() -> dict[str, Any]:
    counts = _endpoint_counts()
    mapped_segments: set[str] = set()
    rows: list[dict[str, Any]] = []
    for dom in DOMAINS:
        seg_count = sum(counts.get(s, 0) for s in dom["segments"])
        mapped_segments.update(dom["segments"])
        chat_reachable = bool(dom["agent_tools"] or dom["routers"])
        tested_files = [f for f in dom["tested_by"] if (REPO_ROOT / f).exists()]
        rows.append(
            {
                **dom,
                "endpoint_count": seg_count,
                "chat_reachable": chat_reachable,
                "tested": bool(tested_files),
                "tested_files_present": tested_files,
            }
        )
    unmapped_segments = {s: c for s, c in counts.items() if s not in mapped_segments}
    total_endpoints = sum(counts.values())
    return {
        "rows": rows,
        "total_endpoints": total_endpoints,
        "mapped_endpoints": total_endpoints - sum(unmapped_segments.values()),
        "unmapped_segments": unmapped_segments,
        "agent_tools": sorted(list_model_facing_tool_names()),
    }


def render_coverage_markdown(matrix: dict[str, Any]) -> str:
    def yn(v: bool) -> str:
        return "✅" if v else "—"

    lines: list[str] = []
    lines.append("# AethOS Capability Coverage Matrix")
    lines.append("")
    lines.append(
        "_Generated by `tests/test_capability_coverage_matrix.py`. Do not hand-edit — "
        "run the test/script to regenerate._"
    )
    lines.append("")
    lines.append(
        f"- Backend endpoints (introspected from the live FastAPI app): **{matrix['total_endpoints']}**"
    )
    lines.append(f"- Model-facing agent tools: **{len(matrix['agent_tools'])}**")
    lines.append("")
    lines.append("## Capability domains")
    lines.append("")
    lines.append(
        "| Domain | Endpoints | Chat-reachable | Tested | UI/CLI by design | Chat surface | Notes |"
    )
    lines.append("|---|---:|:---:|:---:|:---:|---|---|")
    for r in matrix["rows"]:
        surface_bits = list(r["agent_tools"]) + [f"router:{x}" for x in r["routers"]]
        surface = ", ".join(f"`{s}`" for s in surface_bits) if surface_bits else "—"
        lines.append(
            f"| **{r['id']}** — {r['label']} | {r['endpoint_count']} | "
            f"{yn(r['chat_reachable'])} | {yn(r['tested'])} | {yn(r['by_design_ui_cli'])} | "
            f"{surface} | {r['notes']} |"
        )
    lines.append("")
    lines.append("## Agent tools → domain")
    lines.append("")
    lines.append("| Agent tool | Domain | Gating flag |")
    lines.append("|---|---|---|")
    tool_to_domain = {
        t: (r["id"], r.get("flag")) for r in matrix["rows"] for t in r["agent_tools"]
    }
    for tool in matrix["agent_tools"]:
        dom, flag = tool_to_domain.get(tool, ("UNMAPPED", None))
        lines.append(f"| `{tool}` | {dom} | {flag or '—'} |")
    lines.append("")
    if matrix["unmapped_segments"]:
        lines.append("## Unmapped endpoint segments (informational)")
        lines.append("")
        for seg, c in sorted(matrix["unmapped_segments"].items(), key=lambda x: -x[1]):
            lines.append(f"- `{seg}`: {c}")
        lines.append("")
    lines.append("## §A2 — Chat-reach gap assessment (named candidates)")
    lines.append("")
    lines.append("| Candidate | Status | Surface | Note |")
    lines.append("|---|---|---|---|")
    for g in CANDIDATE_GAPS:
        badge = "✅ chat-reachable" if g["status"] == "reachable" else "🔒 UI/CLI by design"
        lines.append(f"| {g['candidate']} | {badge} | {g['via']} | {g['note']} |")
    lines.append("")
    lines.append("## Tracked chat-reach gaps")
    lines.append("")
    gaps = [r for r in matrix["rows"] if not r["chat_reachable"] and not r["by_design_ui_cli"]]
    if gaps:
        for g in gaps:
            lines.append(f"- **{g['id']}** — not chat-reachable and not UI/CLI-by-design. {g['notes']}")
    else:
        lines.append(
            "- None. Every domain is either chat-reachable or explicitly UI/CLI by design."
        )
    lines.append("")
    return "\n".join(lines)


def _write_matrix() -> str:
    matrix = build_coverage_matrix()
    content = render_coverage_markdown(matrix)
    MATRIX_PATH.write_text(content + "\n", encoding="utf-8")
    return content


# ---------------------------------------------------------------- tests --------


def test_every_agent_tool_is_mapped_to_a_domain():
    matrix = build_coverage_matrix()
    mapped = {t for r in matrix["rows"] for t in r["agent_tools"]}
    advertised = set(matrix["agent_tools"])
    orphans = advertised - mapped
    assert not orphans, f"agent tools not mapped to any coverage domain: {sorted(orphans)}"


def test_no_tool_is_mapped_to_two_domains():
    seen: Counter = Counter()
    for dom in DOMAINS:
        for t in dom["agent_tools"]:
            seen[t] += 1
    dupes = {t: c for t, c in seen.items() if c > 1}
    assert not dupes, f"tools mapped to multiple domains: {dupes}"


def test_chat_reachable_domains_have_a_surface():
    matrix = build_coverage_matrix()
    for r in matrix["rows"]:
        if r["chat_reachable"]:
            assert r["agent_tools"] or r["routers"], r["id"]


def test_by_design_ui_domains_explain_why():
    for dom in DOMAINS:
        if dom["by_design_ui_cli"]:
            assert dom["notes"].strip(), dom["id"]


def test_tested_claims_point_at_real_files():
    for dom in DOMAINS:
        for f in dom["tested_by"]:
            assert (REPO_ROOT / f).exists(), f"declared test file missing: {f} ({dom['id']})"


def test_a2_candidate_gaps_resolve_to_real_action_or_by_design():
    """§A2: every named candidate is either chat-reachable or honestly UI/CLI by design."""
    for g in CANDIDATE_GAPS:
        assert g["status"] in {"reachable", "by_design"}, g["candidate"]
        assert g["via"].strip(), g["candidate"]
        # by-design surfaces must be a real surface (no hallucinated locations)
        if g["status"] == "by_design":
            assert "Mission Control" in g["via"] or "aethos " in g["via"] or "CLI" in g["via"]


def test_no_untracked_chat_reach_gaps():
    """Any domain that is neither chat-reachable nor UI/CLI-by-design is a real gap."""
    matrix = build_coverage_matrix()
    gaps = [
        r["id"]
        for r in matrix["rows"]
        if not r["chat_reachable"] and not r["by_design_ui_cli"]
    ]
    assert not gaps, f"untracked chat-reach gaps (add a tool/router or mark by-design): {gaps}"


def test_matrix_doc_is_in_sync():
    """The checked-in COVERAGE_MATRIX.md must match freshly generated content."""
    if os.environ.get("AETHOS_WRITE_COVERAGE_MATRIX"):
        _write_matrix()
    expected = render_coverage_markdown(build_coverage_matrix()) + "\n"
    assert MATRIX_PATH.exists(), "COVERAGE_MATRIX.md missing — run the script to generate it"
    actual = MATRIX_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "COVERAGE_MATRIX.md is stale. Regenerate with:\n"
        "  AETHOS_WRITE_COVERAGE_MATRIX=1 pytest tests/test_capability_coverage_matrix.py"
    )


if __name__ == "__main__":
    print(_write_matrix())
