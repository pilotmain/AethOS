# SPDX-License-Identifier: Apache-2.0
"""Operator-visible Mission Control navigation — prevents internal panel leakage in chat."""

from __future__ import annotations

from typing import Any

INTERNAL_SURFACE_MUTATION_APPROVAL = "Operation Preflights"
INTERNAL_SURFACE_TRACKED_JOBS = "JobsTrackedWorkPanel"
INTERNAL_SURFACE_DURABLE_JOBS = "Durable Agent Jobs"

# Operator surfaces MUST match the REAL clickable sidebar labels in
# web/lib/missionControl/flatNavigation.ts (the rendered Flat nav), NOT the deep view-id
# labels in views.ts. The sidebar shows: Approvals, Jobs, Providers, Channels, Agents
# (primary) and Credentials (under the "Advanced settings" expander).
OPERATOR_APPROVAL_INBOX_PATH = "Mission Control → Approvals"
OPERATOR_TRACKED_WORK_PATH = "Mission Control → Jobs"
OPERATOR_CREDENTIALS_PATH = "Mission Control → Advanced settings → Credentials"

OPERATOR_VISIBLE_OPERATIONS = (
    "Operations hub",
    "Recovery monitoring",
    "Active issues",
    "Deployments",
    "Provider status",
    "Runtime actions",
    "Recommendations",
)

OPERATOR_VISIBLE_WORKSPACES = (
    "Workspaces hub",
    "Active investigations",
    "Agent work",
    "Workspaces",
    "Collaboration",
    "Background jobs",
    "Engineering execution",
)

HIDDEN_INTERNAL_PANELS = (
    "Operation Preflights",
    "JobsTrackedWorkPanel",
    "Runtime Fragility Intelligence",
    "Recovery Continuity Intelligence",
    "Durable Agent Jobs",
    "tracked-work",
    "operation-preflights",
)

INTERNAL_TO_VISIBLE_OPERATOR: dict[str, str] = {
    INTERNAL_SURFACE_MUTATION_APPROVAL: OPERATOR_APPROVAL_INBOX_PATH,
    INTERNAL_SURFACE_TRACKED_JOBS: OPERATOR_TRACKED_WORK_PATH,
    INTERNAL_SURFACE_DURABLE_JOBS: OPERATOR_TRACKED_WORK_PATH,
    "Background jobs": OPERATOR_TRACKED_WORK_PATH,
    # Defense-in-depth: rewrite legacy/deep aliases to the REAL Flat-nav labels at runtime
    # (the CI guard blocks them at build time; this catches anything dynamic).
    "Mission Control → Settings → Connections": OPERATOR_CREDENTIALS_PATH,
    "Mission Control → Connections": OPERATOR_CREDENTIALS_PATH,
    "Mission Control → Credential Center": OPERATOR_CREDENTIALS_PATH,
    "Mission Control → Approval Inbox": OPERATOR_APPROVAL_INBOX_PATH,
    "Mission Control → Tracked Work": OPERATOR_TRACKED_WORK_PATH,
    "Mission Control → Provider Inventory": "Mission Control → Providers",
    "Mission Control → Channel Integration": "Mission Control → Channels",
    "Mission Control → Local Workspaces": "Mission Control → Code workspaces",
    # The feature is called "Multi-model arbiter" everywhere, but the real sidebar
    # button is just "Arbiter" — rewrite the nav phrase so directions are clickable.
    "Mission Control → Multi-model arbiter": "Mission Control → Arbiter",
    "Mission Control → Multi-Model Arbiter": "Mission Control → Arbiter",
}

INTERNAL_TO_VISIBLE_DEEP: dict[str, str] = {
    INTERNAL_SURFACE_MUTATION_APPROVAL: "Mission Control → Approvals",
    INTERNAL_SURFACE_TRACKED_JOBS: "Mission Control → Jobs",
    "Mission Control → Jobs": "Mission Control → Jobs",
    INTERNAL_SURFACE_DURABLE_JOBS: "Mission Control → Jobs",
}


def resolve_visible_navigation_path(*, internal_surface: str, mode: str = "operator") -> str:
    """Map internal MC panel names to operator-visible workflow paths."""
    table = INTERNAL_TO_VISIBLE_DEEP if mode == "deep-engineering" else INTERNAL_TO_VISIBLE_OPERATOR
    if internal_surface in table:
        return table[internal_surface]
    for key, path in table.items():
        if key.lower() in internal_surface.lower():
            return path
    if internal_surface.startswith("Mission Control →"):
        return sanitize_operator_navigation_copy(internal_surface, mode=mode)
    return internal_surface


def sanitize_operator_navigation_copy(text: str, *, mode: str = "operator") -> str:
    if mode == "deep-engineering":
        return text
    out = text
    for hidden, visible in INTERNAL_TO_VISIBLE_OPERATOR.items():
        out = out.replace(hidden, visible)
    for hidden in HIDDEN_INTERNAL_PANELS:
        if hidden in ("tracked-work", "operation-preflights"):
            continue
        visible = resolve_visible_navigation_path(internal_surface=hidden, mode=mode)
        out = out.replace(hidden, visible.split(" → ")[-1])
    return out


def contains_hidden_navigation_leakage(text: str, *, mode: str = "operator") -> bool:
    if mode == "deep-engineering":
        return False
    lower = text.lower()
    for label in HIDDEN_INTERNAL_PANELS:
        if label.lower() in lower:
            return True
    # Deep view-id labels that are NOT the real Flat-nav buttons leak internal naming.
    for deep in ("approval inbox", "tracked work", "credential center", "provider inventory"):
        if deep in lower:
            return True
    return False


# Canonical operator destinations → the real, verified UI surface. The single place that
# turns a logical destination (used by guidance composers) into a clickable path, so no
# composer hardcodes a label. Values are the REAL Flat-nav sidebar labels
# (web/lib/missionControl/flatNavigation.ts), enforced by tests/test_navigation_labels_match_ui.py.
OPERATOR_DESTINATIONS: dict[str, str] = {
    "credentials": OPERATOR_CREDENTIALS_PATH,
    "credential_center": OPERATOR_CREDENTIALS_PATH,
    "connections": OPERATOR_CREDENTIALS_PATH,
    "provider_inventory": "Mission Control → Providers",
    "providers": "Mission Control → Providers",
    "integrations": "Mission Control → Channels",
    "channels": "Mission Control → Channels",
    "approvals": OPERATOR_APPROVAL_INBOX_PATH,
    "approval_inbox": OPERATOR_APPROVAL_INBOX_PATH,
    "jobs": OPERATOR_TRACKED_WORK_PATH,
    "tracked_work": OPERATOR_TRACKED_WORK_PATH,
    "orchestration": "Mission Control → Agents",
    "agents": "Mission Control → Agents",
    "canvas": "Canvas tab",
    "arbiter": "Mission Control → Arbiter",
    "env": ".env file",
}


def operator_surface(destination: str) -> str:
    """Resolve a canonical destination key to the real, verified UI path.

    Falls back to sanitizing a free-form surface (so a literal still gets the wrong-label
    rewrite) rather than inventing a screen.
    """
    key = (destination or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key in OPERATOR_DESTINATIONS:
        return OPERATOR_DESTINATIONS[key]
    return sanitize_operator_navigation_copy(destination or "")


# --------------------------------------------------------------------------- #
# §A3 — "Where is X done" truth source.
#
# One place that maps a gated capability to its REAL flag/env var and its REAL
# operator surface, so the agent checks actual state before claiming something
# can't be done and never invents a screen/setting that doesn't exist.
# --------------------------------------------------------------------------- #

# The only operator surfaces the agent is allowed to reference. AethOS config is
# read solely from .env — there is no in-app/Mission Control settings page for flags.
# Every entry MUST be a real, clickable Flat-nav sidebar label
# (web/lib/missionControl/flatNavigation.ts); the rest are real top-level surfaces. The CI
# test tests/test_navigation_labels_match_ui.py enforces this against flatNavigation.ts.
REAL_OPERATOR_SURFACES: tuple[str, ...] = (
    "Canvas tab",
    "Mission Control → Approvals",
    "Mission Control → Jobs",
    "Mission Control → Providers",
    "Mission Control → Channels",
    "Mission Control → Agents",
    "Mission Control → Research",
    OPERATOR_CREDENTIALS_PATH,
    "the Research / Documents / Notes / Email / Calendar / Foundry tabs",
    ".env file",
)

# capability id -> (settings attribute, ENV_VAR, real surface, what it's for)
CAPABILITY_TRUTH: dict[str, dict[str, str]] = {
    "canvas": {
        "flag": "canvas_surface_enabled",
        "env_var": "CANVAS_SURFACE_ENABLED",
        "surface": "Canvas tab",
        "purpose": "render read-only views to the Live Canvas",
    },
    "agent_runtime": {
        "flag": "agent_runtime_enabled",
        "env_var": "AGENT_RUNTIME_ENABLED",
        "surface": "Mission Control → Agents",
        "purpose": "agent tool-loop + multi-agent orchestration",
    },
    "workspace_suite": {
        "flag": "workspace_suite_enabled",
        "env_var": "WORKSPACE_SUITE_ENABLED",
        "surface": "the Research / Documents / Notes / Email / Calendar / Foundry tabs",
        "purpose": "research / compare / doc / notes / email / calendar / model foundry tools",
    },
    "email_imap": {
        "flag": "workspace_suite_enabled",
        "env_var": "WORKSPACE_SUITE_ENABLED",
        "surface": "Mission Control → Advanced settings → Credentials",
        "purpose": "per-account IMAP inbox credentials (then triage in the Email tab)",
    },
    "channels": {
        "flag": "channel_gateway_enabled",
        "env_var": "CHANNEL_GATEWAY_ENABLED",
        "surface": "Mission Control → Channels",
        "purpose": "outbound channel messaging; pairing approve is UI/CLI by design",
    },
    "mutation_execution": {
        "flag": "mutation_execution_enabled",
        "env_var": "MUTATION_EXECUTION_ENABLED",
        "surface": "Mission Control → Approvals",
        "purpose": "execute governed mutations after operator approval",
    },
    "model_foundry": {
        "flag": "model_foundry_enabled",
        "env_var": "MODEL_FOUNDRY_ENABLED",
        "surface": "Mission Control → Approvals",
        "purpose": "serve/manage local models (serve needs approval)",
    },
    "web_research": {
        "flag": "web_research_enabled",
        "env_var": "WEB_RESEARCH_ENABLED",
        "surface": ".env file",
        "purpose": "web search + deep research runs",
    },
    "vector_memory": {
        "flag": "vector_memory_enabled",
        "env_var": "VECTOR_MEMORY_ENABLED",
        "surface": ".env file",
        "purpose": "memory_recall over the vector store",
    },
    "skills_registry": {
        "flag": "skills_registry_enabled",
        "env_var": "SKILLS_REGISTRY_ENABLED",
        "surface": ".env file",
        "purpose": "skill_recall from the skills registry",
    },
    "voice": {
        "flag": "voice_surface_enabled",
        "env_var": "VOICE_SURFACE_ENABLED",
        "surface": ".env file",
        "purpose": "speak/listen voice surface",
    },
}


def capability_truth(cap_id: str) -> dict[str, str] | None:
    return CAPABILITY_TRUTH.get((cap_id or "").strip().lower())


def where_is(cap_id: str) -> str:
    """Honest one-liner: real surface + the real flag that gates it."""
    row = capability_truth(cap_id)
    if not row:
        return ""
    return (
        f"{row['purpose'].capitalize()} → {row['surface']} "
        f"(gated by {row['env_var']} in .env)."
    )


def is_capability_enabled(cap_id: str) -> bool | None:
    """Actual current flag state, or None if the capability id is unknown."""
    row = capability_truth(cap_id)
    if not row:
        return None
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), row["flag"], False))


def render_capability_truth_lines() -> list[str]:
    """System-prompt block: real surfaces + real flag state, so the agent never
    invents a UI location and never claims a capability is off without checking."""
    from aethos_core.config import get_settings

    settings = get_settings()
    lines = [
        "Where things are done (truth source — reference ONLY these surfaces; config is read",
        "solely from .env, there is NO in-app/Mission Control settings page for flags):",
    ]
    for row in CAPABILITY_TRUTH.values():
        enabled = bool(getattr(settings, row["flag"], False))
        state = "ON" if enabled else "OFF"
        if enabled:
            lines.append(f"- {row['purpose']}: {row['surface']} [{row['env_var']}={state}]")
        else:
            lines.append(
                f"- {row['purpose']}: DISABLED — set {row['env_var']}=true in .env and restart "
                f"(then: {row['surface']})"
            )
    # Model selection is a UI affordance, not a flag — steer the agent away from the
    # wrong ".env + restart" answer for "switch model".
    lines.append(
        "- switching the chat model: the user picks it from the model selector in the chat "
        "composer (per-conversation; takes effect on the next message). It is NOT an env var "
        "and needs NO restart — never tell the user to edit .env or restart to change models."
    )
    lines.append("")
    return lines


def visible_navigation_registry(*, mode: str = "operator") -> dict[str, Any]:
    return {
        "mode": mode,
        "operator_visible_operations": list(OPERATOR_VISIBLE_OPERATIONS),
        "operator_visible_workspaces": list(OPERATOR_VISIBLE_WORKSPACES),
        "hidden_internal_panels": list(HIDDEN_INTERNAL_PANELS),
        "mutation_approval_path": resolve_visible_navigation_path(
            internal_surface=INTERNAL_SURFACE_MUTATION_APPROVAL,
            mode=mode,
        ),
        "durable_approval_path": resolve_visible_navigation_path(
            internal_surface=INTERNAL_SURFACE_DURABLE_JOBS,
            mode=mode,
        ),
    }
