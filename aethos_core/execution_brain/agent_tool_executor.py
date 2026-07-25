# SPDX-License-Identifier: Apache-2.0
"""Agent tools for the LLM tool loop — readonly inspection plus governed mutation preflight."""

from __future__ import annotations

import contextvars
import json
import re
from typing import Any, Callable

from aethos_core.execution_brain.provider_tool_registry import list_provider_tools


from aethos_core.execution_brain.agent_tool_catalog import (
    LEGACY_TOOL_ALIASES,
    agent_tool_schemas_from_catalog,
)


# ─────────────────────────────────────────────────────────────────────────────
# §1 Live progress narration — read-only visibility layer.
#
# The agent tool loop emits human-readable step/thought events to an optional
# per-turn *sink* installed by the SSE boundary (see /chat/stream). When no sink
# is installed (e.g. POST /chat) or LIVE_PROGRESS_ENABLED is off, every emit is a
# no-op, so existing behavior is byte-identical. This layer NEVER executes
# anything and NEVER bypasses governance — it only narrates what the loop does.
# Secrets are redacted from every summary before emission.
# ─────────────────────────────────────────────────────────────────────────────

_ProgressSink = Callable[[dict[str, Any]], None]
_progress_sink: contextvars.ContextVar[_ProgressSink | None] = contextvars.ContextVar(
    "aethos_progress_sink", default=None
)


def live_progress_enabled() -> bool:
    """True when the live-progress flag is on (default on)."""
    try:
        from aethos_core.config import get_settings

        return bool(getattr(get_settings(), "live_progress_enabled", True))
    except Exception:  # noqa: BLE001 — visibility must never break the turn.
        return False


def set_progress_sink(fn: _ProgressSink) -> contextvars.Token:
    """Install a per-turn progress sink; returns a token for reset_progress_sink."""
    return _progress_sink.set(fn)


def reset_progress_sink(token: contextvars.Token) -> None:
    try:
        _progress_sink.reset(token)
    except Exception:  # noqa: BLE001
        pass


def emit_progress(event: dict[str, Any]) -> None:
    """Send one progress event to the active sink; no-op when none/flag off."""
    if not live_progress_enabled():
        return
    fn = _progress_sink.get()
    if fn is None:
        return
    try:
        fn(dict(event))
    except Exception:  # noqa: BLE001 — never let narration break a turn.
        pass


# Map raw tool names to a friendly present-tense verb phrase the operator reads.
_TOOL_VERBS: dict[str, str] = {
    "provider_inventory": "Listing resources",
    "provider_logs": "Reading logs",
    "provider_status": "Checking status",
    "provider_exec": "Preparing a governed action",
    "provider_deploy": "Preparing a governed deploy",
    "web_search": "Searching the web",
    "repo_read": "Reading a file",
    "repo_search": "Searching the repo",
    "repo_tree": "Mapping the repo",
    "canvas_render": "Rendering to the Canvas",
    "channel_send": "Preparing a channel message",
    "model_foundry": "Working with Model Foundry",
}


def _short(text: str, limit: int = 160) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def humanize_tool_action(tool: str, tool_input: dict[str, Any]) -> str:
    """A one-line, secret-free sentence describing the tool call about to run."""
    from aethos_core.security.secret_redaction import redact_text

    tool = str(tool or "")
    base = _TOOL_VERBS.get(tool)
    if base is None and tool.startswith("workspace_"):
        base = "Working in the workspace suite"
    if base is None:
        base = f"Running {tool.replace('_', ' ')}" if tool else "Working"
    detail = ""
    provider = str(tool_input.get("provider") or "").strip()
    path = str(tool_input.get("path") or tool_input.get("file") or "").strip()
    query = str(tool_input.get("query") or tool_input.get("q") or "").strip()
    if tool.startswith("provider_") and provider:
        detail = f" on {provider}"
    elif tool in {"repo_read", "repo_tree"} and path:
        detail = f" {path}"
    elif tool in {"web_search", "repo_search"} and query:
        detail = f" for “{_short(query, 60)}”"
    return redact_text(_short(base + detail, 140))


def humanize_tool_result(tool: str, result_text: str) -> tuple[str, str]:
    """Return (status, summary) where status is 'done' or 'failed'.

    The summary is a short, secret-free human sentence. Failures are detected
    from the tool result's JSON (``ok: false`` / ``error`` / ``denied``).
    """
    from aethos_core.security.secret_redaction import redact_text

    raw = result_text or ""
    status = "done"
    summary = ""
    try:
        parsed = json.loads(raw)
    except Exception:  # noqa: BLE001 — non-JSON tool result; treat as text.
        parsed = None
    if isinstance(parsed, dict):
        if parsed.get("ok") is False or parsed.get("error") or parsed.get("denied"):
            status = "failed"
        err = parsed.get("error") or parsed.get("detail") or parsed.get("message")
        if status == "failed" and err:
            summary = f"{err}"
        else:
            for key in ("summary", "message", "status", "result", "detail"):
                val = parsed.get(key)
                if isinstance(val, str) and val.strip():
                    summary = val.strip()
                    break
            if not summary:
                count = parsed.get("count")
                items = parsed.get("items") or parsed.get("results") or parsed.get("resources")
                if isinstance(count, int):
                    summary = f"{count} result(s)"
                elif isinstance(items, list):
                    summary = f"{len(items)} result(s)"
                else:
                    summary = "Done"
    else:
        low = raw.lower()
        if any(t in low for t in ("error", "denied", "rejected", "forbidden", "failed")):
            status = "failed"
        summary = raw.strip() or ("Failed" if status == "failed" else "Done")
    return status, redact_text(_short(summary, 180))


# §2 — email triage is an explicit-intent capability. The model may only call
# workspace_email when the operator clearly asked about email/inbox/mail; it must
# never fire on generic words like "issue", "check", or "this", so an IMAP/“not
# configured” line can never bleed into an unrelated (e.g. Railway) answer.
_EMAIL_INTENT_RX = re.compile(
    r"\b("
    r"e-?mails?"
    r"|inbox(?:es)?"
    r"|mailbox(?:es)?"
    r"|imap"
    r"|unread"
    r"|triage\s+(?:my\s+)?(?:inbox|mail)"
    r"|(?:my\s+)?mail\b"
    r"|urgent\s+mail"
    r")\b",
    re.I,
)


def is_explicit_email_intent(text: str) -> bool:
    """True only when the prompt is explicitly about email/inbox (§2)."""
    return bool(_EMAIL_INTENT_RX.search(text or ""))


def readonly_agent_tool_schemas(
    *,
    for_prompt: str | None = None,
    channel: str = "chat",
    session_id: str = "main",
    surface: str = "",
) -> list[dict[str, Any]]:
    """Anthropic-compatible tool definitions, flag-gated at the tool boundary.

    Workspace suite tools (workspace_*) are only advertised to the model when
    WORKSPACE_SUITE_ENABLED is on (handoff §2/§8), so the agent never attempts a
    disabled capability. When ``for_prompt`` is supplied, the email triage tool
    (workspace_email) is additionally withheld unless the prompt explicitly asks
    about email/inbox (§2) — keeping IMAP status out of unrelated answers.
    """
    from aethos_core.config import get_settings

    settings = get_settings()
    schemas = agent_tool_schemas_from_catalog()
    if not settings.workspace_suite_enabled:
        schemas = [t for t in schemas if not str(t.get("name", "")).startswith("workspace_")]
    if for_prompt is not None and not is_explicit_email_intent(for_prompt):
        schemas = [t for t in schemas if str(t.get("name", "")) != "workspace_email"]
    if not getattr(settings, "channel_gateway_enabled", False):
        schemas = [t for t in schemas if str(t.get("name", "")) != "channel_send"]
    if not getattr(settings, "canvas_surface_enabled", True):
        schemas = [t for t in schemas if str(t.get("name", "")) != "canvas_render"]
    if not getattr(settings, "model_foundry_enabled", False):
        schemas = [t for t in schemas if str(t.get("name", "")) != "model_foundry"]
    if not getattr(settings, "arbiter_enabled", False):
        schemas = [t for t in schemas if str(t.get("name", "")) != "arbiter_run"]
    from aethos_core.execution_brain.agent_tool_policy import filter_tool_schemas

    schemas = filter_tool_schemas(
        schemas,
        channel=channel,
        session_id=session_id,
        surface=surface,
    )

    # Relevance routing (opt-in): trim to the tools this prompt actually needs so simple
    # turns carry a tight toolset (cheaper, less context rot). No-op when disabled, when
    # there's no prompt, or when the catalog already fits under the cap.
    if for_prompt and getattr(settings, "tool_relevance_enabled", False):
        from aethos_core.execution_brain.tool_relevance import select_relevant_tools

        schemas = select_relevant_tools(
            schemas, for_prompt, max_tools=int(getattr(settings, "tool_relevance_max", 14) or 14)
        )

    return schemas


def agent_tool_schemas(
    *,
    for_prompt: str | None = None,
    channel: str = "chat",
    session_id: str = "main",
    surface: str = "",
) -> list[dict[str, Any]]:
    return readonly_agent_tool_schemas(
        for_prompt=for_prompt,
        channel=channel,
        session_id=session_id,
        surface=surface,
    )


def _normalize_legacy_tool_call(
    name: str,
    tool_input: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    if name not in LEGACY_TOOL_ALIASES:
        return name, tool_input
    generic, defaults = LEGACY_TOOL_ALIASES[name]
    merged: dict[str, Any] = {**defaults, **tool_input}
    if generic in {"provider_health", "provider_logs"}:
        target = (
            merged.pop("project_name", None)
            or merged.pop("service_name", None)
            or merged.get("target_name")
            or ""
        )
        if target:
            merged["target_name"] = target
    if generic == "provider_workflows" and "repository" not in merged:
        repo = merged.pop("project_name", None) or merged.get("target_name")
        if repo:
            merged["repository"] = repo
    if generic == "provider_inventory_all":
        merged.setdefault("mode", "full")
    return generic, merged


def execute_agent_tool(
    name: str,
    tool_input: dict[str, Any],
    *,
    session_id: str = "default",
    channel: str = "chat",
    surface: str = "",
) -> str:
    """Run one agent tool; return JSON string for the model.

    Wraps the implementation to attribute tool execution wall-time to the current
    turn (§C5 latency telemetry); the timing hook is best-effort and never affects
    the tool result.
    """
    from time import perf_counter

    started = perf_counter()
    try:
        return _execute_agent_tool_impl(
            name, tool_input, session_id=session_id, channel=channel, surface=surface
        )
    finally:
        try:
            from aethos_core.chat.route_timing import add_tools_ms

            add_tools_ms(int((perf_counter() - started) * 1000))
        except Exception:
            pass


def _execute_agent_tool_impl(
    name: str,
    tool_input: dict[str, Any],
    *,
    session_id: str = "default",
    channel: str = "chat",
    surface: str = "",
) -> str:
    import json

    from aethos_core.execution_brain.agent_tool_policy import is_tool_allowed, policy_denial_payload

    name, tool_input = _normalize_legacy_tool_call(name, tool_input)
    if not is_tool_allowed(name, channel=channel, session_id=session_id, surface=surface):
        return json.dumps(
            policy_denial_payload(name, channel=channel, session_id=session_id)
        )
    if name == "web_search":
        return _execute_web_search(tool_input)
    if name == "provider_catalog":
        from aethos_core.execution_brain.provider_agent_ops import provider_catalog_payload

        return json.dumps(provider_catalog_payload())
    if name == "provider_validate":
        from aethos_core.execution_brain.provider_agent_ops import provider_validate

        provider = str(tool_input.get("provider") or "").strip()
        if not provider:
            return json.dumps({"ok": False, "error": "provider_required"})
        return json.dumps(provider_validate(provider))
    if name == "provider_inventory":
        from aethos_core.execution_brain.provider_agent_ops import provider_inventory

        provider = str(tool_input.get("provider") or "").strip()
        if not provider:
            return json.dumps({"ok": False, "error": "provider_required"})
        return json.dumps(provider_inventory(provider, session_id=session_id))
    if name == "provider_inventory_all":
        from aethos_core.execution_brain.provider_agent_ops import provider_inventory_all

        limit = max(1, min(int(tool_input.get("limit") or 40), 50))
        mode = str(tool_input.get("mode") or "quick")
        return json.dumps(provider_inventory_all(session_id=session_id, limit=limit, mode=mode))
    if name == "provider_health":
        from aethos_core.execution_brain.provider_agent_ops import provider_health

        provider = str(tool_input.get("provider") or "").strip()
        if not provider:
            return json.dumps({"ok": False, "error": "provider_required"})
        return json.dumps(
            provider_health(
                provider,
                target_name=str(tool_input.get("target_name") or tool_input.get("service_name") or tool_input.get("project_name") or ""),
                project_name=str(tool_input.get("project_name") or ""),
                limit=int(tool_input.get("limit") or 3),
                session_id=session_id,
            )
        )
    if name == "provider_logs":
        from aethos_core.execution_brain.provider_agent_ops import provider_logs

        provider = str(tool_input.get("provider") or "").strip()
        target = str(tool_input.get("target_name") or tool_input.get("service_name") or tool_input.get("project_name") or "")
        if not provider or not target:
            return json.dumps({"ok": False, "error": "provider_and_target_name_required"})
        return json.dumps(
            provider_logs(
                provider,
                target_name=target,
                limit=int(tool_input.get("limit") or 20),
                session_id=session_id,
            )
        )
    if name == "provider_workflows":
        from aethos_core.execution_brain.provider_agent_ops import provider_workflows

        provider = str(tool_input.get("provider") or "github").strip()
        repository = str(tool_input.get("repository") or tool_input.get("target_name") or "").strip()
        if not repository:
            return json.dumps({"ok": False, "error": "repository_required"})
        return json.dumps(
            provider_workflows(
                provider,
                repository=repository,
                limit=int(tool_input.get("limit") or 10),
                session_id=session_id,
            )
        )
    if name == "agent_list":
        from aethos_core.agents.runtime.subagent_ops import agent_list_payload

        return json.dumps(agent_list_payload())
    if name == "agent_spawn":
        from aethos_core.agents.runtime.subagent_ops import spawn_subagent_coordination

        goal = str(tool_input.get("goal") or "").strip()
        if not goal:
            return json.dumps({"ok": False, "error": "goal_required"})
        workspace_hint = str(tool_input.get("workspace_hint") or "").strip() or None
        return json.dumps(
            spawn_subagent_coordination(
                goal=goal,
                session_id=session_id,
                workspace_hint=workspace_hint,
            )
        )
    if name == "agent_sessions_list":
        from aethos_core.agents.runtime.subagent_ops import agent_sessions_list_payload

        limit = max(1, min(int(tool_input.get("limit") or 30), 100))
        parent = str(tool_input.get("parent_session_id") or session_id).strip() or session_id
        return json.dumps(agent_sessions_list_payload(parent_session_id=parent, limit=limit))
    if name == "agent_send":
        from aethos_core.agents.runtime.subagent_ops import send_subagent_message

        message = str(tool_input.get("message") or "").strip()
        if not message:
            return json.dumps({"ok": False, "error": "message_required"})
        session_key = str(tool_input.get("session_key") or "").strip() or None
        spawn_id = str(tool_input.get("spawn_id") or "").strip() or None
        if not session_key and not spawn_id:
            return json.dumps({"ok": False, "error": "session_key_or_spawn_id_required"})
        return json.dumps(
            send_subagent_message(
                message=message,
                session_id=session_id,
                session_key=session_key,
                spawn_id=spawn_id,
            )
        )
    if name == "terminal_create_preflight":
        from aethos_core.agents.runtime.cursor_terminal_jobs import create_governed_terminal_preflight

        command = str(tool_input.get("command") or "").strip()
        if not command:
            return json.dumps({"ok": False, "error": "command_required"})
        workspace_hint = str(tool_input.get("workspace_hint") or "").strip() or None
        subagent_key = str(tool_input.get("subagent_session_key") or "").strip() or None
        return json.dumps(
            create_governed_terminal_preflight(
                command=command,
                session_id=session_id,
                workspace_hint=workspace_hint,
                subagent_session_key=subagent_key,
            )
        )
    if name == "provider_exec":
        from aethos_core.agents.runtime.cursor_terminal_jobs import create_provider_exec_preflight

        provider = str(tool_input.get("provider") or "").strip()
        command = str(tool_input.get("command") or "").strip()
        if not provider:
            return json.dumps({"ok": False, "error": "provider_required"})
        if not command:
            return json.dumps({"ok": False, "error": "command_required"})
        return json.dumps(
            create_provider_exec_preflight(
                provider=provider,
                command=command,
                purpose=str(tool_input.get("purpose") or "").strip(),
                session_id=session_id,
                workspace_hint=str(tool_input.get("workspace_hint") or "").strip() or None,
            )
        )
    if name == "cursor_open_preflight":
        from aethos_core.agents.runtime.cursor_terminal_jobs import propose_cursor_workspace_open

        workspace_hint = str(tool_input.get("workspace_hint") or "").strip() or None
        path = str(tool_input.get("path") or "").strip() or None
        subagent_key = str(tool_input.get("subagent_session_key") or "").strip() or None
        return json.dumps(
            propose_cursor_workspace_open(
                workspace_hint=workspace_hint,
                path=path,
                subagent_session_key=subagent_key,
                session_id=session_id,
            )
        )
    if name == "github_read_repo":
        from aethos_core.providers.github.operations.repo_remote_read_api import (
            analyze_github_repo_for_chat,
        )

        repository = str(tool_input.get("repository") or "").strip()
        if not repository:
            return json.dumps({"ok": False, "error": "repository_required"})
        branch = str(tool_input.get("branch") or "").strip() or None
        result = analyze_github_repo_for_chat("", repository=repository, branch=branch)
        return json.dumps(result)
    if name == "github_issues_prs":
        from aethos_core.credentials import get_provider_api_token
        from aethos_core.providers.github.operations.repo_readonly_api import (
            list_open_issues,
            list_open_pull_requests,
        )

        repository = str(tool_input.get("repository") or "").strip()
        if not repository:
            return json.dumps({"ok": False, "error": "repository_required"})
        token = get_provider_api_token("github", require_validated=False)
        if not token:
            return json.dumps(
                {"ok": False, "error": "github_token_unavailable", "detail": "Connect GitHub in Mission Control → Advanced settings → Credentials."}
            )
        limit = int(tool_input.get("limit") or 20)
        issues = list_open_issues(token, repository=repository, limit=limit)
        prs = list_open_pull_requests(token, repository=repository, limit=limit)
        return json.dumps(
            {
                "ok": bool(issues.get("ok")) and bool(prs.get("ok")),
                "repository": repository,
                "open_issue_count": issues.get("count", 0),
                "open_issues": issues.get("issues", []),
                "open_pr_count": prs.get("count", 0),
                "open_pull_requests": prs.get("pull_requests", []),
                "issues_error": issues.get("error"),
                "prs_error": prs.get("error"),
            }
        )
    if name == "list_tracked_jobs":
        from aethos_core.runtime.jobs import job_store

        limit = int(tool_input.get("limit") or 15)
        only_session = bool(tool_input.get("this_session_only"))
        rows: list[dict[str, Any]] = []
        for job in job_store.list_all():
            d = job.to_dict()
            if only_session and str(d.get("session_id") or "") != session_id:
                continue
            rows.append(
                {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "job_type": d.get("job_type"),
                    "status": d.get("status"),
                    "created_at": d.get("created_at"),
                    "updated_at": d.get("updated_at"),
                    "failure_reason": d.get("failure_reason"),
                    "result_summary": d.get("result_summary"),
                }
            )
            if len(rows) >= limit:
                break
        return json.dumps({"ok": True, "count": len(rows), "jobs": rows})
    if name == "approval_inbox":
        from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload

        return json.dumps(approval_inbox_payload(session_id=session_id))
    if name == "repo_overview":
        from aethos_core.local_workspace.readonly.actions import repo_overview

        return json.dumps(
            repo_overview(
                workspace=str(tool_input.get("workspace") or "").strip() or None,
                session_id=session_id,
            )
        )
    if name == "repo_list":
        from aethos_core.local_workspace.readonly.actions import repo_list

        path = str(tool_input.get("path") or "").strip()
        if not path:
            return json.dumps({"ok": False, "error": "path_required"})
        return json.dumps(
            repo_list(path=path, max_depth=int(tool_input.get("max_depth") or 2), session_id=session_id)
        )
    if name == "repo_read":
        from aethos_core.local_workspace.readonly.actions import repo_read

        path = str(tool_input.get("path") or "").strip()
        if not path:
            return json.dumps({"ok": False, "error": "path_required"})
        max_bytes = tool_input.get("max_bytes")
        return json.dumps(
            repo_read(
                path=path,
                max_bytes=int(max_bytes) if max_bytes else None,
                session_id=session_id,
            )
        )
    if name == "repo_grep":
        from aethos_core.local_workspace.readonly.actions import repo_grep

        path = str(tool_input.get("path") or "").strip()
        pattern = str(tool_input.get("pattern") or "").strip()
        if not path:
            return json.dumps({"ok": False, "error": "path_required"})
        if not pattern:
            return json.dumps({"ok": False, "error": "pattern_required"})
        max_results = tool_input.get("max_results")
        return json.dumps(
            repo_grep(
                path=path,
                pattern=pattern,
                max_results=int(max_results) if max_results else None,
                session_id=session_id,
            )
        )
    if name == "skill_recall":
        from aethos_core.execution_brain.agent_skill_recall import recall_skills

        return json.dumps(
            recall_skills(
                query=str(tool_input.get("query") or ""),
                limit=int(tool_input.get("limit") or 3),
            )
        )
    if name == "memory_recall":
        from aethos_core.memory.vector_store import recall

        query = str(tool_input.get("query") or "").strip()
        if not query:
            return json.dumps({"ok": False, "error": "query_required"})
        limit = max(1, min(int(tool_input.get("limit") or 5), 20))
        return json.dumps(recall(query=query, limit=limit))
    if name == "platform_review":
        # Cross-platform status snapshot (deploys, jobs, approvals, monitors, social) so the
        # agent can answer "what's our status / what did we do today / is everything healthy".
        from aethos_core.digest import build_digest

        digest = build_digest(use_llm=False)
        return json.dumps({"ok": True, "review": digest.get("text"), "sections": digest.get("sections")})
    if name == "arbiter_run":
        return _execute_arbiter_run(tool_input, session_id=session_id)
    if name == "research_run":
        from aethos_core.config import get_settings

        topic = str(tool_input.get("topic") or tool_input.get("question") or "").strip()
        if not topic:
            return json.dumps({"ok": False, "error": "topic_required"})
        max_sources = max(1, min(int(tool_input.get("max_sources") or tool_input.get("depth") or 5), 10))
        if getattr(get_settings(), "deep_research_enabled", False):
            from aethos_core.research.deep_research_runtime import run_deep_research_pipeline

            depth = max(1, min(int(tool_input.get("depth") or 2), 6))
            return json.dumps(
                run_deep_research_pipeline(
                    topic,
                    depth=depth,
                    session_id=session_id,
                )
            )
        from aethos_core.execution_brain.agent_research import run_deep_research

        return json.dumps(run_deep_research(topic=topic, max_sources=max_sources, session_id=session_id))
    if name in (
        "workspace_research",
        "workspace_compare",
        "workspace_doc",
        "workspace_notes",
        "workspace_email",
        "workspace_calendar",
    ):
        from aethos_core.config import get_settings

        if not get_settings().workspace_suite_enabled:
            return json.dumps({"ok": False, "error": "workspace_suite_disabled"})
        if name == "workspace_research":
            from aethos_core.execution_brain.agent_research import run_deep_research

            topic = str(tool_input.get("topic") or "").strip()
            if not topic:
                return json.dumps({"ok": False, "error": "topic_required"})
            max_sources = max(1, min(int(tool_input.get("max_sources") or 5), 8))
            return json.dumps(run_deep_research(topic=topic, max_sources=max_sources, session_id=session_id))
        if name == "workspace_doc":
            return _execute_workspace_doc(tool_input)
        if name == "workspace_notes":
            return _execute_workspace_notes(tool_input)
        if name == "workspace_email":
            return _execute_workspace_email(tool_input, session_id=session_id)
        if name == "workspace_calendar":
            return _execute_workspace_calendar(tool_input)
        from aethos_core.research.blind_model_eval import run_blind_model_eval

        prompt = str(tool_input.get("prompt") or "").strip()
        if len(prompt) < 8:
            return json.dumps({"ok": False, "error": "prompt_too_short"})
        return json.dumps(run_blind_model_eval(prompt=prompt))
    if name == "model_foundry":
        return _execute_model_foundry(tool_input)
    if name == "canvas_render":
        from aethos_core.canvas.canvas_store import render_canvas_view

        result = render_canvas_view(
            session_id=session_id,
            view_type=str(tool_input.get("view_type") or ""),
            title=str(tool_input.get("title") or ""),
            data=tool_input.get("data"),
        )
        if not result.get("ok"):
            return json.dumps(result)
        return json.dumps(result)
    if name == "channel_send":
        from aethos_core.channels.outbound_governance import create_outbound_send_preflight

        out = create_outbound_send_preflight(
            channel=str(tool_input.get("channel") or ""),
            to=str(tool_input.get("to") or ""),
            body=str(tool_input.get("body") or ""),
            subject=str(tool_input.get("subject") or ""),
            session_id=session_id,
        )
        return json.dumps(out)
    if name == "provider_create_mutation_preflight":
        return _execute_provider_create_mutation_preflight(tool_input, session_id=session_id)
    return json.dumps({"ok": False, "error": f"unknown_tool:{name}"})


# --- Deep provider implementations (used by provider_agent_ops) ---


def _resolve_vercel_token() -> tuple[str, str] | None:
    from aethos_core.operational_session.vercel_readonly_executor import _resolve_token

    return _resolve_token()


def _run_arbiter_session_sync(
    prompt: str, *, session_id: str, pool: list[dict[str, Any]], fast: bool = False
):
    """Run the async arbiter lifecycle from the sync tool loop, safe under a live loop."""
    import asyncio

    from aethos_core.arbiter.service import run_arbiter_session
    from aethos_core.chat.chat_turn_tenant import chat_turn_scope, resolve_chat_turn_tenant

    captured_tenant = resolve_chat_turn_tenant()

    def _run() -> Any:
        with chat_turn_scope(captured_tenant):
            return asyncio.run(
                run_arbiter_session(
                    prompt,
                    chat_session_id=session_id,
                    model_pool_override=pool,
                    fast=fast,
                )
            )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _run()
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool_exec:
        return pool_exec.submit(_run).result()


def _execute_arbiter_run(tool_input: dict[str, Any], *, session_id: str) -> str:
    """Multi-Model Arbiter chat tool — honest preconditions, never a fake/empty run."""
    from aethos_core.config import get_settings

    _PANEL_HINT = "Open Mission Control → Arbiter for the full per-model detail."
    settings = get_settings()
    if not getattr(settings, "arbiter_enabled", False):
        return json.dumps(
            {
                "ok": False,
                "error": "arbiter_disabled",
                "hint": (
                    "The Multi-Model Arbiter is off. Set ARBITER_ENABLED=true and "
                    "ARBITER_MODEL_POOL to ≥2 models you have keys for (diverse providers "
                    "critique each other best), add the matching provider keys in Mission "
                    "Control, then restart."
                ),
            }
        )

    prompt = str(tool_input.get("prompt") or "").strip()
    if not prompt:
        return json.dumps({"ok": False, "error": "prompt_required"})

    from aethos_core.arbiter.pool import parse_model_pool, parse_model_pool_string, validate_pool

    pool_raw = str(tool_input.get("pool") or "").strip()
    pool = parse_model_pool_string(pool_raw) if pool_raw else parse_model_pool()
    validation = validate_pool(pool)
    if not validation["valid"]:
        return json.dumps(
            {
                "ok": False,
                "error": "pool_insufficient",
                "details": validation["errors"],
                "hint": (
                    "Set ARBITER_MODEL_POOL to ≥2 models you have keys for in the vault "
                    "(e.g. anthropic:claude-sonnet-4-6,openrouter:openai/gpt-4.1). Diverse "
                    "providers critiquing each other give the strongest consensus."
                ),
            }
        )

    # Fast mode: explicit tool flag, or the user asked for a quick/fast run. Skips the
    # peer-critique round for a much faster result (parallel answers, no cross-ranking).
    import re as _re

    fast = bool(tool_input.get("fast")) or bool(
        _re.search(r"\b(fast|quick|quickly|rapid|speedy)\b", prompt, _re.I)
    )

    try:
        session = _run_arbiter_session_sync(prompt, session_id=session_id, pool=pool, fast=fast)
    except Exception as exc:  # noqa: BLE001 — surface honestly, never crash the turn.
        return json.dumps({"ok": False, "error": "arbiter_run_failed", "detail": str(exc)})

    consensus = session.consensus
    # Which provider+model actually participated — so the reply can name them (the user
    # should never have to guess whether it was, say, all Anthropic or truly cross-provider).
    participants = [
        {
            "provider": r.provider,
            "model": r.model_id,
            "label": r.model_label,
            "responded": not r.error,
        }
        for r in session.responses
    ]
    responded = [p for p in participants if p["responded"]]
    payload: dict[str, Any] = {
        "ok": session.status.value not in {"failed"},
        "session_id": session.session_id,
        "status": session.status.value,
        "model_count": len(session.model_pool),
        "responding_models": len(responded),
        "fast_mode": fast,
        "critique_skipped": fast,
        "models": participants,
        "providers": sorted({p["provider"] for p in responded}),
        "participants_line": (
            "Consensus across: " + ", ".join(f"{p['label']} ({p['provider']})" for p in responded)
            if responded
            else ""
        ),
        "rounds_completed": session.rounds_completed,
        "duration_ms": session.duration_ms,
        "artifact_id": session.artifact_id,
        "panel": "Arbiter",
        "hint": _PANEL_HINT,
    }
    if session.error:
        payload["error"] = session.error
    if consensus is not None:
        payload["consensus"] = {
            "reached": consensus.consensus_reached,
            "agreement_score": round(consensus.agreement_score, 3),
            "winning_model": consensus.winning_model_label,
            "summary": consensus.summary,
            "winning_text": (consensus.winning_text or "")[:2000],
            "dissenting_models": list(consensus.dissenting_model_ids),
            "agreeing_models": consensus.agreeing_models,
        }
    return json.dumps(payload)


def _execute_workspace_doc(tool_input: dict[str, Any]) -> str:
    """Draft-only document tool — create/update/get/list. Never publishes."""
    from aethos_core.workspace_suite.documents_store import (
        create_document,
        get_document,
        list_documents,
        update_document,
    )

    action = str(tool_input.get("action") or "").strip().lower()
    if action == "create":
        return json.dumps(
            create_document(
                title=str(tool_input.get("title") or "Untitled"),
                content=str(tool_input.get("content") or ""),
                fmt=str(tool_input.get("format") or "markdown"),
            )
        )
    if action == "update":
        doc_id = str(tool_input.get("doc_id") or "").strip()
        if not doc_id:
            return json.dumps({"ok": False, "error": "doc_id_required"})
        return json.dumps(
            update_document(
                doc_id=doc_id,
                title=tool_input.get("title"),
                content=tool_input.get("content"),
                fmt=tool_input.get("format"),
            )
        )
    if action == "get":
        doc_id = str(tool_input.get("doc_id") or "").strip()
        if not doc_id:
            return json.dumps({"ok": False, "error": "doc_id_required"})
        return json.dumps(get_document(doc_id=doc_id))
    if action == "list":
        return json.dumps(list_documents(limit=int(tool_input.get("limit") or 100)))
    return json.dumps({"ok": False, "error": "unsupported_action", "allowed": ["create", "update", "get", "list"]})


def _execute_workspace_notes(tool_input: dict[str, Any]) -> str:
    """Notes & tasks tool. Scheduled tasks are recorded only — never auto-executed."""
    from aethos_core.workspace_suite.notes_tasks_store import (
        add_note,
        add_task,
        list_notes,
        list_tasks,
        set_task_done,
    )

    action = str(tool_input.get("action") or "").strip().lower()
    if action == "note_add":
        return json.dumps(add_note(text=str(tool_input.get("text") or "")))
    if action == "note_list":
        return json.dumps(list_notes(limit=int(tool_input.get("limit") or 100)))
    if action == "task_add":
        return json.dumps(
            add_task(
                text=str(tool_input.get("text") or ""),
                scheduled_for=tool_input.get("scheduled_for"),
            )
        )
    if action == "task_list":
        return json.dumps(list_tasks(limit=int(tool_input.get("limit") or 200)))
    if action == "task_done":
        task_id = str(tool_input.get("task_id") or "").strip()
        if not task_id:
            return json.dumps({"ok": False, "error": "task_id_required"})
        done = tool_input.get("done")
        return json.dumps(set_task_done(task_id=task_id, done=True if done is None else bool(done)))
    return json.dumps(
        {"ok": False, "error": "unsupported_action", "allowed": ["note_add", "note_list", "task_add", "task_list", "task_done"]}
    )


def _execute_model_foundry(tool_input: dict[str, Any]) -> str:
    """Model Foundry tool — scan/recommend are readonly; serve is a governed preflight."""
    from aethos_core.workspace_suite.model_foundry import (
        create_serve_preflight,
        recommend_models,
        scan_hardware,
    )

    action = str(tool_input.get("action") or "").strip().lower()
    if action == "scan":
        return json.dumps(scan_hardware())
    if action == "recommend":
        return json.dumps(recommend_models())
    if action == "serve_preflight":
        model_id = str(tool_input.get("model_id") or "").strip()
        if not model_id:
            return json.dumps({"ok": False, "error": "model_id_required"})
        return json.dumps(create_serve_preflight(model_id=model_id, port=int(tool_input.get("port") or 11434)))
    return json.dumps({"ok": False, "error": "unsupported_action", "allowed": ["scan", "recommend", "serve_preflight"]})


def _execute_workspace_email(tool_input: dict[str, Any], *, session_id: str) -> str:
    """Email tool — triage is readonly; drafts never auto-send (governed preflight)."""
    from aethos_core.workspace_suite.email_triage import (
        create_draft_reply,
        list_draft_replies,
        send_draft_preflight,
        triage_inbox,
    )

    action = str(tool_input.get("action") or "").strip().lower()
    if action == "triage":
        return json.dumps(triage_inbox(limit=int(tool_input.get("limit") or 20)))
    if action == "draft_reply":
        return json.dumps(
            create_draft_reply(
                to=str(tool_input.get("to") or ""),
                subject=str(tool_input.get("subject") or ""),
                body=str(tool_input.get("body") or ""),
            )
        )
    if action == "drafts_list":
        return json.dumps(list_draft_replies(limit=int(tool_input.get("limit") or 50)))
    if action == "send_preflight":
        draft_id = str(tool_input.get("draft_id") or "").strip()
        if not draft_id:
            return json.dumps({"ok": False, "error": "draft_id_required"})
        return json.dumps(send_draft_preflight(draft_id=draft_id, session_id=session_id))
    return json.dumps(
        {"ok": False, "error": "unsupported_action", "allowed": ["triage", "draft_reply", "drafts_list", "send_preflight"]}
    )


def _execute_workspace_calendar(tool_input: dict[str, Any]) -> str:
    """Calendar tool — local events + .ics import/export; CalDAV sync is readonly."""
    from aethos_core.workspace_suite.calendar_store import (
        add_event,
        caldav_sync,
        export_ics,
        import_ics,
        list_events,
    )

    action = str(tool_input.get("action") or "").strip().lower()
    if action == "list":
        return json.dumps(list_events(limit=int(tool_input.get("limit") or 200)))
    if action == "add":
        return json.dumps(
            add_event(
                summary=str(tool_input.get("summary") or ""),
                start=str(tool_input.get("start") or ""),
                end=str(tool_input.get("end") or ""),
                description=str(tool_input.get("description") or ""),
                calendar=str(tool_input.get("calendar") or "default"),
            )
        )
    if action == "import_ics":
        return json.dumps(
            import_ics(
                ics_text=str(tool_input.get("ics_text") or ""),
                calendar=str(tool_input.get("calendar") or "imported"),
            )
        )
    if action == "export_ics":
        return json.dumps(export_ics())
    if action == "sync":
        return json.dumps(caldav_sync())
    return json.dumps(
        {"ok": False, "error": "unsupported_action", "allowed": ["list", "add", "import_ics", "export_ics", "sync"]}
    )


def _execute_web_search(tool_input: dict[str, Any]) -> str:
    from aethos_core.config import get_settings
    from aethos_core.research.research_config import is_research_search_configured
    from aethos_core.research.research_provider import get_research_provider

    settings = get_settings()
    query = str(tool_input.get("query") or "").strip()
    if not query:
        return json.dumps({"ok": False, "error": "query_required"})
    if not settings.web_research_enabled or not is_research_search_configured(settings):
        return json.dumps({"ok": False, "error": "web_research_not_configured"})

    from aethos_core.governance.net_policy import check_egress

    search_url = f"https://search.aethos.local/?q={query[:200]}"
    allowed, reason = check_egress(search_url)
    if not allowed:
        return json.dumps({"ok": False, "error": "egress_denied", "reason": reason, "query": query})

    max_results = int(tool_input.get("max_results") or 5)
    max_results = max(1, min(max_results, 8))
    provider = get_research_provider()
    results = provider.search(query, max_results=max_results)
    if not results.ok:
        return json.dumps({"ok": False, "error": results.detail or "search_failed", "query": query})
    rows = []
    for row in results.results[:max_results]:
        rows.append(
            {
                "title": row.title,
                "url": row.url,
                "snippet": (row.snippet or "")[:500],
            }
        )
    return json.dumps({"ok": True, "query": query, "results": rows})


def _execute_vercel_validate_connection() -> str:
    from aethos_core.provider_e2e_readiness.vercel_readiness_checks import run_vercel_readiness_checks

    checks = run_vercel_readiness_checks(session_id="default")
    return json.dumps(
        {
            "ok": bool(checks.get("vercel_credential_ok")) and bool(checks.get("vercel_api_connection_ok")),
            "credential_ok": bool(checks.get("vercel_credential_ok")),
            "api_connection_ok": bool(checks.get("vercel_api_connection_ok")),
            "project_count": int(checks.get("vercel_project_count") or 0),
            "detail": checks.get("vercel_api_connection_detail") or checks.get("vercel_credential_detail") or "",
        }
    )


def _execute_vercel_list_projects() -> str:
    auth = _resolve_vercel_token()
    if auth is None:
        return json.dumps({"ok": False, "error": "vercel_token_not_configured"})
    token, _cred = auth
    from aethos_core.providers.vercel.diagnostics.project_diagnostics_api import fetch_projects_list

    payload = fetch_projects_list(token)
    return json.dumps(payload)


def _execute_vercel_deployment_health(tool_input: dict[str, Any]) -> str:
    auth = _resolve_vercel_token()
    if auth is None:
        return json.dumps({"ok": False, "error": "vercel_token_not_configured"})
    token, _cred = auth
    project_name = str(tool_input.get("project_name") or "").strip()
    limit = max(1, min(int(tool_input.get("limit") or 3), 5))

    from aethos_core.providers.vercel.diagnostics.project_diagnostics_api import fetch_projects_list
    from aethos_core.providers.vercel.operations.deployments_api import fetch_deployments

    if project_name:
        payload = fetch_deployments(token, project_name=project_name, limit=limit)
        return json.dumps(_compact_deployment_health(project_name, payload))

    listing = fetch_projects_list(token)
    if not listing.get("ok"):
        return json.dumps({"ok": False, "error": listing.get("error") or "project_list_failed"})
    rows = []
    for project in list(listing.get("projects") or [])[:20]:
        if not isinstance(project, dict):
            continue
        name = str(project.get("name") or "").strip()
        if not name:
            continue
        dep_payload = fetch_deployments(token, project_name=name, limit=limit)
        rows.append(_compact_deployment_health(name, dep_payload, summary=project))
    return json.dumps({"ok": True, "project_count": len(rows), "projects": rows})


def _compact_deployment_health(
    project_name: str,
    payload: dict[str, Any],
    *,
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    deployments = list(payload.get("deployments") or [])
    latest = deployments[0] if deployments else {}
    row: dict[str, Any] = {
        "project_name": project_name,
        "ok": bool(payload.get("ok")),
        "latest_production_state": (summary or {}).get("latest_production_state"),
        "latest_deployment_state": latest.get("state") or "unknown",
        "latest_url": latest.get("url") or "",
        "latest_branch": latest.get("branch") or "",
        "deployment_count": len(deployments),
        "recent_deployments": deployments[:3],
    }
    if payload.get("error"):
        row["error"] = payload.get("error")
    return row


def _execute_railway_list_projects() -> str:
    from aethos_core.provider_skills.runtime import load_provider_skill

    skill = load_provider_skill("railway")
    if skill is None:
        return json.dumps({"ok": False, "error": "railway_skill_unavailable"})
    payload = skill.discover(force=True)
    return json.dumps({"ok": bool(payload.get("ok")), "provider": "railway", "result": payload})


def _execute_railway_list_services(tool_input: dict[str, Any]) -> str:
    from aethos_core.provider_skills.runtime import load_provider_skill

    skill = load_provider_skill("railway")
    if skill is None:
        return json.dumps({"ok": False, "error": "railway_skill_unavailable"})
    payload = skill.discover(force=True)
    project_name = str(tool_input.get("project_name") or "").strip().lower()
    services = list((payload.get("services") or payload.get("result", {}).get("services") or []))
    if project_name:
        services = [
            row
            for row in services
            if isinstance(row, dict)
            and str(row.get("project") or row.get("project_name") or "").lower() == project_name
        ]
    return json.dumps(
        {
            "ok": bool(payload.get("ok")),
            "provider": "railway",
            "service_count": len(services),
            "services": services[:25],
        }
    )


def _execute_railway_inventory_health(tool_input: dict[str, Any]) -> str:
    from aethos_core.operational_planner.adapters.railway_wide_health import collect_railway_service_health_rows
    from aethos_core.provider_skills.runtime import load_provider_skill

    skill = load_provider_skill("railway")
    inventory: dict[str, Any] = {}
    if skill is not None:
        inventory = skill.discover(force=True)
    rows, error = collect_railway_service_health_rows()
    service_name = str(tool_input.get("service_name") or "").strip().lower()
    if service_name:
        rows = [
            row
            for row in rows
            if service_name in str(row.get("service") or "").lower()
            or str(row.get("service") or "").lower() in service_name
        ]
    return json.dumps(
        {
            "ok": bool(inventory.get("ok")) or bool(rows),
            "provider": "railway",
            "inventory": inventory,
            "health_rows": rows[:40],
            "health_error": error,
            "service_count": len(rows),
        }
    )


def _execute_railway_service_health(tool_input: dict[str, Any]) -> str:
    from aethos_core.operational_planner.adapters.railway_wide_health import collect_railway_service_health_rows
    from aethos_core.operational_session.railway_service_hints import filter_railway_health_rows

    service_name = str(tool_input.get("service_name") or "").strip()
    project_name = str(tool_input.get("project_name") or "").strip().lower()
    if not service_name:
        return json.dumps({"ok": False, "error": "service_name_required"})
    rows, error = collect_railway_service_health_rows()
    matched = filter_railway_health_rows(rows, [service_name], text=service_name)
    if project_name:
        matched = [row for row in matched if str(row.get("project") or "").lower() == project_name]
    return json.dumps(
        {
            "ok": bool(matched),
            "provider": "railway",
            "service_name": service_name,
            "rows": matched[:10],
            "error": error if not matched else None,
        }
    )


def _execute_railway_fetch_logs(tool_input: dict[str, Any]) -> str:
    from aethos_core.operational_planner.adapters.railway_wide_health import collect_railway_service_health_rows
    from aethos_core.operational_session.railway_service_hints import filter_railway_health_rows
    from aethos_core.providers.railway.operations.logs_multisource import fetch_railway_service_logs_fast

    service_name = str(tool_input.get("service_name") or "").strip()
    if not service_name:
        return json.dumps({"ok": False, "error": "service_name_required"})
    limit = max(1, min(int(tool_input.get("limit") or 20), 50))
    rows, _error = collect_railway_service_health_rows()
    matched = filter_railway_health_rows(rows, [service_name], text=service_name)
    if not matched:
        return json.dumps({"ok": False, "error": "service_not_found", "service_name": service_name})
    sections: list[dict[str, Any]] = []
    for row in matched[:3]:
        payload = fetch_railway_service_logs_fast(
            service_name=str(row.get("service") or service_name),
            service_id=str(row.get("service_id") or "") or None,
            limit=limit,
        )
        sections.append(
            {
                "project": row.get("project"),
                "environment": row.get("environment"),
                "service": row.get("service"),
                "health": row.get("health"),
                "deployment_state": row.get("deployment_state"),
                "logs": list(payload.get("logs") or [])[:limit],
                "sources_checked": list(payload.get("sources_checked") or []),
            }
        )
    return json.dumps({"ok": True, "provider": "railway", "service_name": service_name, "sections": sections})


def _execute_vercel_fetch_logs(tool_input: dict[str, Any]) -> str:
    auth = _resolve_vercel_token()
    if auth is None:
        return json.dumps({"ok": False, "error": "vercel_token_not_configured"})
    project_name = str(tool_input.get("project_name") or "").strip()
    if not project_name:
        return json.dumps({"ok": False, "error": "project_name_required"})
    limit = max(1, min(int(tool_input.get("limit") or 20), 50))
    token, _cred = auth
    from aethos_core.providers.vercel.operations.logs_api import fetch_deployment_logs

    payload = fetch_deployment_logs(token, project_name=project_name)
    events = list(payload.get("events") or [])
    logs = []
    for row in events[:limit]:
        if not isinstance(row, dict):
            continue
        logs.append(
            {
                "timestamp": str(row.get("created") or "—"),
                "level": str(row.get("type") or "INFO"),
                "message": str(row.get("text") or "").strip(),
            }
        )
    if not logs:
        for line in list(payload.get("log_lines") or [])[:limit]:
            logs.append({"timestamp": "—", "level": "INFO", "message": str(line)})
    return json.dumps(
        {
            "ok": bool(logs) or bool(payload.get("deployment_id")),
            "provider": "vercel",
            "project_name": project_name,
            "deployment_id": payload.get("deployment_id"),
            "deployment_state": (payload.get("deployment") or {}).get("state") if isinstance(payload.get("deployment"), dict) else None,
            "logs": logs,
            "error": payload.get("error"),
        }
    )


def _compose_mutation_user_text(tool_input: dict[str, Any]) -> str:
    explicit = str(tool_input.get("user_text") or "").strip()
    if explicit:
        return explicit
    parts: list[str] = []
    operation = str(tool_input.get("operation") or "restart").strip()
    provider = str(tool_input.get("provider") or "auto").strip()
    service_name = str(tool_input.get("service_name") or "").strip()
    project_name = str(tool_input.get("project_name") or "").strip()
    target = service_name or project_name
    if target:
        parts.append(f"{operation} {target}")
    else:
        parts.append(operation)
    if provider and provider != "auto":
        parts.append(f"on {provider}")
    return " ".join(parts)


def _execute_provider_create_mutation_preflight(tool_input: dict[str, Any], *, session_id: str) -> str:
    from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply

    user_text = _compose_mutation_user_text(tool_input)
    if not user_text:
        return json.dumps({"ok": False, "error": "user_text_required"})
    result = create_mutation_preflight_job_reply(user_text, session_id=session_id)
    if result is None:
        return json.dumps({"ok": False, "error": "mutation_preflight_not_created", "user_text": user_text})
    body, intent, meta = result
    return json.dumps(
        {
            "ok": True,
            "reply": body,
            "intent": intent,
            "meta": meta,
            "user_text": user_text,
            "requires_approval": True,
            "mutation_executed": False,
        }
    )


def provider_tool_requires_approval(tool_id: str) -> bool:
    from aethos_core.execution_brain.provider_tool_registry import get_tool

    tool = get_tool(tool_id)
    if tool is None:
        return True
    return tool.requires_approval


def registry_summary_for_prompt() -> str:
    from aethos_core.execution_brain.agent_tool_catalog import list_model_facing_tool_names

    tools = ", ".join(list_model_facing_tool_names())
    return (
        "Provider agent runtime uses generic Mission Control tools only:\n"
        f"{tools}\n"
        "Always pass `provider` (Mission Control id). Tokens come from Provider Inventory — never chat.\n"
        "Mutations: provider_create_mutation_preflight only — restart, redeploy, stop (approval required before execution)."
    )
