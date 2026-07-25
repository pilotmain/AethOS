# SPDX-License-Identifier: Apache-2.0
"""Workspace policy — allowlists, blocks, approval gates."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.local_workspace.mutations.foundation import BLOCKED_AUTONOMOUS_ACTIONS

_BLOCKED_PATTERNS = (
    re.compile(r"\bsudo\b", re.I),
    re.compile(r"\brm\s+-rf\b", re.I),
    re.compile(r"\bshutdown\b", re.I),
    re.compile(r"\breboot\b", re.I),
    re.compile(r"chmod\s+-R\s+777", re.I),
    re.compile(r"curl\s+.*\|\s*bash", re.I),
    re.compile(r"wget\s+.*\|\s*sh", re.I),
    re.compile(r">\s*/dev/", re.I),
    re.compile(r"\|\s*bash\b", re.I),
    re.compile(r"\|\s*sh\b", re.I),
    re.compile(r";\s*rm\b", re.I),
    re.compile(r"&&\s*rm\b", re.I),
)

_ALLOWED_PREFIXES = (
    "git status",
    "git log",
    "git branch",
    "git diff",
    "git rev-parse",
    "pytest",
    "python -m pytest",
    "npm test",
    "npm run test",
    "npm run build",
    "npm run lint",
    "cursor ",
    "ls",
    "pwd",
    "cat ",
    "head ",
    "tail ",
    "find . -maxdepth",
    "docker ps",
    "docker images",
    "kubectl get",
    # Governed provider CLI auth — still requires Mission Control approval; routed
    # through terminal preflight so deploy steps needing CLI login are not a dead end.
    "vercel login",
    "vercel whoami",
    "railway login",
    "railway whoami",
    "gh auth login",
    "gh auth status",
    "npx vercel login",
)


def evaluate_command_policy(command: str) -> dict[str, Any]:
    """Return policy verdict for a proposed terminal command."""
    cmd = (command or "").strip()
    if not cmd:
        return _deny("empty_command", "Command cannot be empty.")
    if "unrestricted_shell" in BLOCKED_AUTONOMOUS_ACTIONS and _looks_unrestricted(cmd):
        return _deny("unrestricted_shell", "Unrestricted shell is blocked.")
    for rx in _BLOCKED_PATTERNS:
        if rx.search(cmd):
            return _deny("blocked_pattern", f"Blocked pattern: {rx.pattern}")
    if not _is_allowed(cmd):
        return _deny("not_allowlisted", "Command is not on the governed allowlist.")
    return {
        "ok": True,
        "allowed": True,
        "approval_required": True,
        "autonomous_execution_blocked": True,
        "risk_tier": _risk_tier(cmd),
        "command": cmd,
    }


def _is_allowed(cmd: str) -> bool:
    lower = cmd.lower()
    return any(lower.startswith(p.lower()) for p in _ALLOWED_PREFIXES)


def _looks_unrestricted(cmd: str) -> bool:
    lower = cmd.lower()
    return any(tok in lower for tok in ("bash -c", "/bin/bash", "zsh -c", "exec bash", "eval "))


def _risk_tier(cmd: str) -> str:
    lower = cmd.lower()
    if lower.startswith("git ") or lower in ("pwd", "ls"):
        return "W0_readonly"
    if lower.startswith("cursor "):
        return "W1_cursor_open"
    if lower.startswith("pytest") or lower.startswith("python -m pytest") or "npm test" in lower:
        return "W1_scoped_validation"
    if lower.startswith("npm run build") or lower.startswith("npm run lint"):
        return "W2_bounded"
    if "login" in lower or lower.endswith("whoami") or lower.startswith("gh auth"):
        return "W3_provider_auth"
    return "W2_bounded"


def _deny(code: str, reason: str) -> dict[str, Any]:
    return {
        "ok": False,
        "allowed": False,
        "approval_required": False,
        "autonomous_execution_blocked": True,
        "error": code,
        "reason": reason,
        "risk_tier": "W5_blocked",
    }


# --- Credentialed provider execution policy (provider_exec) ---------------------
# Binaries the model may invoke through provider_exec. Block patterns above still
# apply; arbitrary destructive shell stays blocked. npm/pytest/git remain allowed.
PROVIDER_EXEC_BINARIES = frozenset(
    {
        "railway",
        "vercel",
        "supabase",
        "stripe",
        "gh",
        "redis-cli",
        "curl",
        "psql",
        "git",
        "npm",
        "npx",
        "pytest",
    }
)

# Read-only / inspect verbs and subcommands — may run without per-command approval
# (still sandboxed + audited). When unsure we treat a command as mutating.
_READONLY_SUBCOMMANDS = frozenset(
    {
        "logs",
        "log",
        "ls",
        "list",
        "status",
        "get",
        "show",
        "view",
        "inspect",
        "whoami",
        "ps",
        "info",
        "describe",
        "diff",
        "version",
        "--version",
        "-v",
        "help",
        "--help",
        "branch",
        "rev-parse",
        "ping",
        "projects",
        "services",
        "deployments",
    }
)

# Explicit mutating verbs — always require Mission Control approval.
_MUTATING_TOKENS = frozenset(
    {
        "deploy",
        "up",
        "add",
        "rm",
        "remove",
        "restart",
        "redeploy",
        "delete",
        "del",
        "destroy",
        "create",
        "new",
        "init",
        "push",
        "pull",
        "set",
        "unset",
        "update",
        "upgrade",
        "install",
        "uninstall",
        "rollback",
        "reset",
        "drop",
        "migrate",
        "commit",
        "merge",
        "rebase",
        "apply",
        "start",
        "stop",
        "pause",
        "scale",
        "login",
        "link",
        "connect",
        "provision",
        "send",
        "rerun",
        "redeploy",
    }
)

_MUTATING_HTTP_METHODS = frozenset({"post", "put", "delete", "patch"})


def _binary_of(command: str) -> str:
    import shlex

    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    return (parts[0] if parts else "").strip().lower()


def classify_provider_exec_command(command: str) -> dict[str, Any]:
    """Read-only vs mutating classification for a provider CLI/API command.

    Conservative: unknown → mutating (requires approval). curl is read-only only
    for plain GETs; any write HTTP method is mutating.
    """
    import shlex

    cmd = (command or "").strip()
    try:
        tokens = [t.lower() for t in shlex.split(cmd)]
    except ValueError:
        tokens = [t.lower() for t in cmd.split()]
    if not tokens:
        return {"read_only": False, "reason": "empty"}
    binary = tokens[0]
    rest = tokens[1:]
    # Non-flag subcommand tokens — these carry the verb (e.g. `env add`, `run rerun`).
    subs = [t for t in rest if not t.startswith("-")]

    if binary == "curl":
        # Mutating if it carries a write method or a body/data flag.
        if any(t in ("-x", "--request") for t in rest):
            idx = next((i for i, t in enumerate(rest) if t in ("-x", "--request")), -1)
            method = rest[idx + 1] if 0 <= idx < len(rest) - 1 else ""
            if method in _MUTATING_HTTP_METHODS:
                return {"read_only": False, "reason": "http_write_method"}
        if any(t in ("-d", "--data", "--data-raw", "--data-binary", "-f", "--form", "-t", "--upload-file") for t in rest):
            return {"read_only": False, "reason": "http_body"}
        return {"read_only": True, "reason": "http_get"}

    # Any explicit mutating verb among the subcommand tokens makes it mutating.
    if any(tok in _MUTATING_TOKENS for tok in subs):
        return {"read_only": False, "reason": "mutating_verb"}
    if not rest:
        # Bare binary (e.g. `railway`) — treat as read-only help/listing.
        return {"read_only": True, "reason": "bare_binary"}
    # Read-only when an inspect verb appears and no mutating verb was found.
    if any(tok in _READONLY_SUBCOMMANDS for tok in subs):
        return {"read_only": True, "reason": "readonly_subcommand"}
    flag_only = [t for t in rest if t.startswith("-")]
    if not subs and any(f in _READONLY_SUBCOMMANDS for f in flag_only):
        return {"read_only": True, "reason": "readonly_flag"}
    return {"read_only": False, "reason": "unknown_treated_as_mutating"}


def evaluate_provider_exec_policy(command: str) -> dict[str, Any]:
    """Policy verdict for a provider_exec command: block patterns + binary allowlist
    + read-only/mutating tier. Approval is required for mutating commands."""
    cmd = (command or "").strip()
    if not cmd:
        return _deny("empty_command", "Command cannot be empty.")
    if "unrestricted_shell" in BLOCKED_AUTONOMOUS_ACTIONS and _looks_unrestricted(cmd):
        return _deny("unrestricted_shell", "Unrestricted shell is blocked.")
    for rx in _BLOCKED_PATTERNS:
        if rx.search(cmd):
            return _deny("blocked_pattern", f"Blocked pattern: {rx.pattern}")
    binary = _binary_of(cmd)
    if binary not in PROVIDER_EXEC_BINARIES:
        return _deny(
            "binary_not_allowlisted",
            f"`{binary or 'command'}` is not an allowlisted provider binary "
            f"({', '.join(sorted(PROVIDER_EXEC_BINARIES))}).",
        )
    classification = classify_provider_exec_command(cmd)
    read_only = bool(classification.get("read_only"))
    return {
        "ok": True,
        "allowed": True,
        "binary": binary,
        "read_only": read_only,
        "approval_required": not read_only,
        "autonomous_execution_blocked": not read_only,
        "risk_tier": "P0_readonly" if read_only else "P2_mutating",
        "classification": classification,
        "command": cmd,
    }
