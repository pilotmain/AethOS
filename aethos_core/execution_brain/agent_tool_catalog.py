# SPDX-License-Identifier: Apache-2.0
"""Agent tool manifest — AethOS model-facing tool contracts."""

from __future__ import annotations

from typing import Any

_PROVIDER_PARAM = {
    "type": "string",
    "description": "Mission Control provider id (vercel, railway, github, render, aws, …)",
}


def _tool(
    name: str,
    description: str,
    *,
    properties: dict[str, Any],
    required: list[str],
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


MODEL_FACING_AGENT_TOOLS: list[dict[str, Any]] = [
    _tool(
        "web_search",
        "Search the public web for docs, comparisons, or facts — not provider mutations.",
        properties={
            "query": {"type": "string"},
            "max_results": {"type": "integer", "description": "1-8"},
        },
        required=["query"],
    ),
    _tool(
        "provider_catalog",
        "List Mission Control Provider Inventory providers and generic agent capabilities.",
        properties={},
        required=[],
    ),
    _tool(
        "provider_validate",
        "Validate vault credentials for one provider (readonly).",
        properties={"provider": _PROVIDER_PARAM},
        required=["provider"],
    ),
    _tool(
        "provider_inventory",
        "Readonly inventory/discovery for one provider using Provider Inventory tokens.",
        properties={"provider": _PROVIDER_PARAM},
        required=["provider"],
    ),
    _tool(
        "provider_inventory_all",
        "Scan providers: mode=quick (connection only, fast) or mode=full (includes inventory).",
        properties={
            "mode": {"type": "string", "enum": ["quick", "full"], "description": "Default quick"},
            "limit": {"type": "integer", "description": "Max providers (default 40)"},
        },
        required=[],
    ),
    _tool(
        "provider_health",
        "Deployment/service/workflow health for a provider. target_name = project, service, or owner/repo.",
        properties={
            "provider": _PROVIDER_PARAM,
            "target_name": {"type": "string", "description": "Optional target filter"},
            "project_name": {"type": "string", "description": "Optional Railway project filter"},
            "limit": {"type": "integer", "description": "Max rows (default 3)"},
        },
        required=["provider"],
    ),
    _tool(
        "provider_logs",
        "Recent logs for a target on vercel (project), railway (service), or github (owner/repo jobs).",
        properties={
            "provider": _PROVIDER_PARAM,
            "target_name": {"type": "string"},
            "limit": {"type": "integer", "description": "1-50"},
        },
        required=["provider", "target_name"],
    ),
    _tool(
        "provider_workflows",
        "List CI workflow runs (github only). repository = owner/repo.",
        properties={
            "provider": _PROVIDER_PARAM,
            "repository": {"type": "string", "description": "owner/repo"},
            "limit": {"type": "integer", "description": "1-25"},
        },
        required=["provider", "repository"],
    ),
    _tool(
        "agent_list",
        "List bounded specialist agents available for spawn (engineering, provider ops, analyst, developer, browser, research).",
        properties={},
        required=[],
    ),
    _tool(
        "agent_sessions_list",
        "List persisted subagent sessions for this chat session.",
        properties={
            "parent_session_id": {"type": "string", "description": "Chat session id (default current)"},
            "limit": {"type": "integer", "description": "Max sessions (default 30)"},
        },
        required=[],
    ),
    _tool(
        "agent_send",
        "Send a follow-up message to an existing subagent session. "
        "Re-runs bounded multi-agent coordination with prior context.",
        properties={
            "message": {"type": "string", "description": "Follow-up instruction or question"},
            "session_key": {"type": "string", "description": "agent:{parent}:subagent:{spawn_id}"},
            "spawn_id": {"type": "string", "description": "Alternative to session_key"},
        },
        required=["message"],
    ),
    _tool(
        "terminal_create_preflight",
        "Create a governed terminal preflight job (npm/pytest/git/cursor). Requires human approval before execute.",
        properties={
            "command": {"type": "string", "description": "Allowlisted command e.g. npm run build, cursor /path/to/repo"},
            "workspace_hint": {"type": "string"},
            "subagent_session_key": {"type": "string", "description": "Link job to subagent session"},
        },
        required=["command"],
    ),
    _tool(
        "provider_exec",
        "Run a provider CLI/API command end-to-end using Mission Control vault "
        "credentials — the credentialed-execution primitive. You compose the actual "
        "command (e.g. `railway logs --service api`, `vercel deploy --prod`, "
        "`vercel env add KEY production`, `supabase projects list`, `stripe products create`, "
        "`gh run rerun <id>`, or `curl https://api.supabase.com/v1/projects`). AethOS "
        "injects the right vault token as env at execution time (never in the command "
        "or chat) and redacts all output. Allowed binaries: railway, vercel, supabase, "
        "stripe, gh, redis-cli, curl, psql, git, npm, npx, pytest. Read-only commands "
        "(logs/list/status/get/inspect/whoami) run immediately; mutating commands "
        "(deploy/up/env add|rm/create/restart/delete/db push/...) return a Mission "
        "Control approval preflight and only run after the operator approves. Never put "
        "secrets in the command; never claim a mutation executed before approval. If a "
        "CLI is missing, prefer the provider HTTP API via curl with the injected token.",
        properties={
            "provider": {
                "type": "string",
                "enum": ["railway", "vercel", "supabase", "stripe", "resend", "redis", "github", "shell"],
                "description": "Which vault credentials to inject for the command.",
            },
            "command": {"type": "string", "description": "The exact CLI/API command to run."},
            "purpose": {"type": "string", "description": "Short human-readable intent (shown on the approval card)."},
        },
        required=["provider", "command"],
    ),
    _tool(
        "cursor_open_preflight",
        "Propose opening the workspace in Cursor via governed terminal preflight (never auto-opens).",
        properties={
            "workspace_hint": {"type": "string"},
            "path": {"type": "string", "description": "Optional path override"},
            "subagent_session_key": {"type": "string"},
        },
        required=[],
    ),
    _tool(
        "github_read_repo",
        "Read-only GitHub API snapshot for owner/repo (or repo name resolved via connected inventory): "
        "recursive tree sample, manifests, README, CI workflows, and enhancement-oriented observations. "
        "Use FIRST on hosted or when the user names a GitHub repo/URL — no local workspace registration. "
        "For laptop paths use repo_overview/repo_list/repo_read instead.",
        properties={
            "repository": {
                "type": "string",
                "description": "owner/repo, GitHub URL, or repo name (e.g. atlas-trader)",
            },
            "branch": {"type": "string", "description": "Optional branch (default: repo default branch)"},
        },
        required=["repository"],
    ),
    _tool(
        "list_tracked_jobs",
        "Read-only list of the operator's recent AethOS jobs (Mission Control → Jobs / Runtime "
        "tracked work): id, title, job_type, status, timestamps, failure reason. Use this when "
        "the user asks to 'list my jobs', 'recent jobs', or 'job status' — these are AethOS "
        "tracked jobs, NOT provider deployments. Set this_session_only=true to scope to the "
        "current chat. Do not substitute a provider deployment list.",
        properties={
            "limit": {"type": "integer", "description": "Max jobs (default 15)"},
            "this_session_only": {"type": "boolean", "description": "Only jobs from this chat session"},
        },
        required=[],
    ),
    _tool(
        "approval_inbox",
        "Read-only Mission Control approval inbox for the current session: pending governed "
        "mutation/execution preflights awaiting the operator's Approve/Reject. Use this when the "
        "user asks about their approval inbox / what's awaiting approval — return the REAL items "
        "(which may be empty); never speculate about what might be pending.",
        properties={},
        required=[],
    ),
    _tool(
        "github_issues_prs",
        "Read-only list of OPEN GitHub issues and pull requests for owner/repo. Use this when "
        "the user asks about issues, PRs, or 'what's open' on a GitHub repo — do NOT guess or "
        "report a credential error; this returns the real counts (which may legitimately be 0). "
        "Returns open_issue_count/open_issues and open_pr_count/open_pull_requests.",
        properties={
            "repository": {"type": "string", "description": "owner/repo, GitHub URL, or repo name"},
            "limit": {"type": "integer", "description": "Max items per list (default 20)"},
        },
        required=["repository"],
    ),
    _tool(
        "repo_overview",
        "Read-only quick summary of a registered Local Workspace repo: detected stack, "
        "package.json/pyproject dependencies, npm scripts, entry points, file counts, and "
        "test presence. Use for LOCAL paths or registered workspaces — on hosted GitHub repos "
        "use github_read_repo instead. Then drill in with repo_list/repo_read/repo_grep. "
        "Read-only, no approval needed.",
        properties={
            "workspace": {
                "type": "string",
                "description": "Workspace name/path hint (e.g. pilotos). Omit for the first registered workspace.",
            },
        },
        required=[],
    ),
    _tool(
        "repo_list",
        "Read-only directory tree for a path inside a registered Local Workspace (bounded depth; "
        "skips .git/node_modules/build dirs). Path must be inside a registered workspace.",
        properties={
            "path": {"type": "string", "description": "Absolute path, or a workspace name/relative path"},
            "max_depth": {"type": "integer", "description": "Tree depth 1-6 (default 2)"},
        },
        required=["path"],
    ),
    _tool(
        "repo_read",
        "Read-only file contents from inside a registered Local Workspace (text only, size-capped, "
        ".env values and obvious secrets redacted). Path must be inside a registered workspace.",
        properties={
            "path": {"type": "string", "description": "Absolute path, or a workspace name/relative path to a file"},
            "max_bytes": {"type": "integer", "description": "Byte cap (default/limit 64000)"},
        },
        required=["path"],
    ),
    _tool(
        "repo_grep",
        "Read-only ripgrep-style search inside a registered Local Workspace. Returns file:line:match "
        "rows (secrets redacted). Path must be inside a registered workspace.",
        properties={
            "path": {"type": "string", "description": "Directory/file path, or a workspace name/relative path"},
            "pattern": {"type": "string", "description": "Regex or literal to search for"},
            "max_results": {"type": "integer", "description": "Max rows 1-120 (default 120)"},
        },
        required=["path", "pattern"],
    ),
    _tool(
        "agent_spawn",
        "Spawn a governed multi-agent coordination run (subagent sessions). "
        "Specialists run sequentially; each receives prior agents' evidence. Readonly — no mutations.",
        properties={
            "goal": {"type": "string", "description": "Investigation or analysis goal in plain language"},
            "workspace_hint": {"type": "string", "description": "Optional repo hint e.g. aethos"},
        },
        required=["goal"],
    ),
    _tool(
        "skill_recall",
        "Load matching operator skills from repo skills/ directory (readonly guidance).",
        properties={
            "query": {"type": "string", "description": "Topic to match skill name/description"},
            "limit": {"type": "integer", "description": "Max skills (default 3)"},
        },
        required=[],
    ),
    _tool(
        "memory_recall",
        "Recall operational vector memory entries (readonly). Requires VECTOR_MEMORY_ENABLED.",
        properties={
            "query": {"type": "string"},
            "limit": {"type": "integer", "description": "Max rows (default 5)"},
        },
        required=["query"],
    ),
    _tool(
        "research_run",
        "Multi-step deep research report from public web sources (readonly). Requires WEB_RESEARCH_ENABLED.",
        properties={
            "topic": {"type": "string"},
            "max_sources": {"type": "integer", "description": "1-8"},
        },
        required=["topic"],
    ),
    _tool(
        "workspace_research",
        "Workspace suite: run a Deep Research report (readonly, cited). "
        "Gated by WORKSPACE_SUITE_ENABLED; wraps the deep research runtime.",
        properties={
            "topic": {"type": "string"},
            "max_sources": {"type": "integer", "description": "1-8"},
        },
        required=["topic"],
    ),
    _tool(
        "workspace_compare",
        "Workspace suite: blind multi-response Compare for operator review (readonly, no labels "
        "revealed pre-reveal). Gated by WORKSPACE_SUITE_ENABLED.",
        properties={
            "prompt": {"type": "string", "description": "Question to compare answers for"},
        },
        required=["prompt"],
    ),
    _tool(
        "workspace_doc",
        "Workspace suite: manage DRAFT documents (markdown/text/csv/html). Draft-only — "
        "never publishes or sends. actions: create, update, get, list. "
        "Gated by WORKSPACE_SUITE_ENABLED.",
        properties={
            "action": {"type": "string", "enum": ["create", "update", "get", "list"]},
            "doc_id": {"type": "string", "description": "Required for update/get"},
            "title": {"type": "string"},
            "content": {"type": "string", "description": "Draft body"},
            "format": {"type": "string", "enum": ["markdown", "text", "csv", "html"]},
        },
        required=["action"],
    ),
    _tool(
        "workspace_notes",
        "Workspace suite: quick notes, checklist tasks, and cron-style scheduled tasks. "
        "Scheduled tasks are RECORDED only — they never auto-execute; any action runs "
        "through the governed preflight->approve path. actions: note_add, note_list, "
        "task_add, task_list, task_done. Gated by WORKSPACE_SUITE_ENABLED.",
        properties={
            "action": {
                "type": "string",
                "enum": ["note_add", "note_list", "task_add", "task_list", "task_done"],
            },
            "text": {"type": "string", "description": "Note/task body (for *_add)"},
            "task_id": {"type": "string", "description": "Required for task_done"},
            "done": {"type": "boolean", "description": "task_done state (default true)"},
            "scheduled_for": {"type": "string", "description": "Optional cron/ISO hint (recorded only)"},
        },
        required=["action"],
    ),
    _tool(
        "workspace_email",
        "Workspace suite: readonly IMAP inbox triage (urgency/tags/summary/spam) and "
        "DRAFT replies. Drafts are NEVER auto-sent — sending routes through the governed "
        "outbound preflight (approval + allowlist). actions: triage, draft_reply, "
        "drafts_list, send_preflight. Gated by WORKSPACE_SUITE_ENABLED.",
        properties={
            "action": {"type": "string", "enum": ["triage", "draft_reply", "drafts_list", "send_preflight"]},
            "to": {"type": "string", "description": "Reply recipient (draft_reply)"},
            "subject": {"type": "string"},
            "body": {"type": "string", "description": "Draft reply body"},
            "draft_id": {"type": "string", "description": "Required for send_preflight"},
            "limit": {"type": "integer", "description": "Max messages/drafts"},
        },
        required=["action"],
    ),
    _tool(
        "workspace_calendar",
        "Workspace suite: local-first calendar. Add/list LOCAL events, import/export .ics, "
        "and readonly CalDAV sync. Remote calendar writes are NOT performed (writes gated). "
        "actions: list, add, import_ics, export_ics, sync. Gated by WORKSPACE_SUITE_ENABLED.",
        properties={
            "action": {"type": "string", "enum": ["list", "add", "import_ics", "export_ics", "sync"]},
            "summary": {"type": "string", "description": "Event title (add)"},
            "start": {"type": "string", "description": "Start, e.g. 20260604T090000Z (add)"},
            "end": {"type": "string"},
            "description": {"type": "string"},
            "calendar": {"type": "string", "description": "Calendar name (default 'default')"},
            "ics_text": {"type": "string", "description": ".ics document text (import_ics)"},
        },
        required=["action"],
    ),
    _tool(
        "model_foundry",
        "Model Foundry: scan local hardware (readonly), recommend open models by "
        "VRAM-aware fit score, or record a GOVERNED serve request (loopback only, never "
        "auto-serves or downloads). actions: scan, recommend, serve_preflight. "
        "Requires MODEL_FOUNDRY_ENABLED.",
        properties={
            "action": {"type": "string", "enum": ["scan", "recommend", "serve_preflight"]},
            "model_id": {"type": "string", "description": "Required for serve_preflight"},
            "port": {"type": "integer", "description": "Loopback port for serve_preflight (default 11434)"},
        },
        required=["action"],
    ),
    _tool(
        "arbiter_run",
        "Run the Multi-Model Arbiter: dispatch a question to a pool of 2+ models in "
        "parallel, run a blind cross-critique round, and return the consensus answer "
        "plus a dissent summary. Use when the operator asks to 'run the arbiter', get a "
        "'multi-model consensus / second opinion', or have models critique each other on "
        "a hard question. Read-only — performs no provider mutations. Gated by "
        "ARBITER_ENABLED; needs ARBITER_MODEL_POOL with ≥2 models whose keys are in the "
        "vault. If those preconditions are unmet, the tool returns the exact fix — never a "
        "fake or empty run. Full per-model detail appears in Mission Control → Arbiter.",
        properties={
            "prompt": {"type": "string", "description": "The question to put to the model pool."},
            "pool": {
                "type": "string",
                "description": "Optional override pool, e.g. 'anthropic:claude-sonnet-4-6,openrouter:openai/gpt-4.1'. Defaults to ARBITER_MODEL_POOL.",
            },
            "fast": {
                "type": "boolean",
                "description": "Fast mode: skip the peer-critique round for a much quicker result "
                "(parallel answers, no cross-ranking). Set true when the user asks for a fast/quick run.",
            },
        },
        required=["prompt"],
    ),
    _tool(
        "canvas_render",
        (
            "Render a read-only structured view to the Live Canvas (status, diff, research_report, "
            "job_timeline, table, markdown). Render surface ONLY — cannot execute mutations. "
            "Requires CANVAS_SURFACE_ENABLED. WHEN TO USE: whenever the user explicitly asks to "
            "render/draw/show/visualize something ON THE CANVAS, you MUST call this tool — do not "
            "print the content into the chat reply as a substitute. The Live Canvas is a separate "
            "surface the operator views in the Canvas tab; it is available whenever the tool is "
            "offered, regardless of the current chat channel. After a successful render, reply with a "
            "short confirmation (e.g. 'Rendered a job timeline to the Canvas — open the Canvas tab to "
            "view'), NOT a full duplicate of the rendered content. If the tool returns "
            "canvas_surface_disabled, name the real fix — set CANVAS_SURFACE_ENABLED=true (Railway "
            "deployment variables on hosted, .env locally) and redeploy/restart — never invent an "
            "in-app/Mission Control settings page. "
            "DATA RULES (enforced — empty views are rejected): populate `data` with REAL content, "
            "never placeholder/blank rows. For `table`, provide `columns` (header strings) AND `rows` "
            "as objects whose KEYS EXACTLY MATCH the column strings, e.g. "
            "columns:['Provider','Status'], rows:[{'Provider':'railway','Status':'failed'}]. For "
            "`job_timeline`, provide `events` (or `rows`) as objects with at least label and status. "
            "If you don't yet have the data, FETCH it first (list jobs/deployments via the provider "
            "tools) and only render once you have real values — never render an empty skeleton."
        ),
        properties={
            "view_type": {
                "type": "string",
                "enum": ["status", "diff", "research_report", "job_timeline", "table", "markdown"],
            },
            "title": {"type": "string"},
            "data": {
                "type": "object",
                "description": (
                    "Structured view payload (read-only). MUST contain real, non-empty content. "
                    "table → {columns:[...], rows:[{<column>:<value>}]}; job_timeline → "
                    "{events:[{label,status,detail?,timestamp?}]}."
                ),
            },
        },
        required=["view_type", "title"],
    ),
    _tool(
        "channel_send",
        "Outbound message send — GOVERNED. Creates an outbound-send preflight (does NOT send). "
        "Requires CHANNEL_GATEWAY_ENABLED; the operator must approve and the recipient must be "
        "allowlisted before the message is delivered. Never fires to non-allowlisted peers.",
        properties={
            "channel": {"type": "string", "description": "telegram, slack, email, discord, ..."},
            "to": {"type": "string", "description": "Recipient chat id / address (must be allowlisted)"},
            "body": {"type": "string", "description": "Message text"},
            "subject": {"type": "string", "description": "Optional subject (email)"},
        },
        required=["channel", "to", "body"],
    ),
    _tool(
        "provider_create_mutation_preflight",
        "Create governed mutation preflight — does NOT execute. "
        "Resolve target via deployment target registry first (provider_inventory if unknown). "
        "Operations: stop, restart, redeploy, deploy, set_env_var, remove_env_var.",
        properties={
            "user_text": {"type": "string"},
            "provider": _PROVIDER_PARAM,
            "operation": {
                "type": "string",
                "enum": ["restart", "redeploy", "stop", "deploy", "set_env_var", "remove_env_var"],
            },
            "project_name": {"type": "string"},
            "service_name": {"type": "string"},
            "target_alias": {"type": "string", "description": "Deployment target registry alias"},
        },
        required=["user_text", "operation"],
    ),
    _tool(
        "platform_review",
        "Review the current state of the AethOS platform across deployments, jobs, pending "
        "approvals, monitors, and connected social — for questions like 'what's our status', "
        "'what are we working on', 'what did we do today', or 'is everything healthy'. Readonly.",
        properties={},
        required=[],
    ),
]

# Legacy aliases — executed but not advertised to the model (backward compat).
LEGACY_TOOL_ALIASES: dict[str, tuple[str, dict[str, Any]]] = {
    "cloud_list_providers": ("provider_catalog", {}),
    "cloud_validate_connection": ("provider_validate", {}),
    "cloud_list_inventory": ("provider_inventory", {}),
    "cloud_list_all_inventory": ("provider_inventory_all", {}),
    "vercel_validate_connection": ("provider_validate", {"provider": "vercel"}),
    "vercel_list_projects": ("provider_inventory", {"provider": "vercel"}),
    "vercel_deployment_health": ("provider_health", {"provider": "vercel"}),
    "vercel_fetch_logs": ("provider_logs", {"provider": "vercel"}),
    "railway_list_projects": ("provider_inventory", {"provider": "railway"}),
    "railway_list_services": ("provider_inventory", {"provider": "railway"}),
    "railway_inventory_health": ("provider_health", {"provider": "railway"}),
    "railway_service_health": ("provider_health", {"provider": "railway"}),
    "railway_fetch_logs": ("provider_logs", {"provider": "railway"}),
}


def list_model_facing_tool_names() -> list[str]:
    return [str(t["name"]) for t in MODEL_FACING_AGENT_TOOLS]


def agent_tool_schemas_from_catalog() -> list[dict[str, Any]]:
    return list(MODEL_FACING_AGENT_TOOLS)
