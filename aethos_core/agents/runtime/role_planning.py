# SPDX-License-Identifier: Apache-2.0
"""Role extraction and on-demand agent spawn planning from natural language."""

from __future__ import annotations

import re
from typing import Any

# normalized token -> (display label, capability id)
_ROLE_CAPABILITY: dict[str, tuple[str, str]] = {
    "development": ("Development", "dev_workspace"),
    "dev": ("Development", "dev_workspace"),
    "developer": ("Development", "dev_workspace"),
    "qa": ("QA", "qa_verification"),
    "quality": ("QA", "qa_verification"),
    "quality assurance": ("QA", "qa_verification"),
    "security": ("Security", "code_intelligence"),
    "research": ("Research", "research"),
    "researcher": ("Research", "research"),
    "writer": ("Writer", "research"),
    "analyst": ("Analyst", "operations_analyst"),
    "operations": ("Operations", "operations_analyst"),
    "operations analyst": ("Analyst", "operations_analyst"),
    "code": ("Development", "code_intelligence"),
    "architect": ("Architect", "code_intelligence"),
    "architecture": ("Architect", "code_intelligence"),
    "tester": ("QA", "qa_verification"),
    "test": ("QA", "qa_verification"),
    "testing": ("QA", "qa_verification"),
    "devops": ("DevOps", "operations_analyst"),
    "dev ops": ("DevOps", "operations_analyst"),
    "sre": ("DevOps", "operations_analyst"),
    "marketing": ("Marketing", "research"),
    "marketer": ("Marketing", "research"),
}

_ROLE_SKILLS: dict[str, tuple[str, ...]] = {
    "Development": (
        "code_reasoning_readonly",
        "git_analysis",
        "ci_analysis",
        "engineering_preflight",
        "patch_planning",
    ),
    "QA": (
        "evidence_capture",
        "test_planning",
        "summarize_failures",
        "correlate_evidence",
        "severity_classification",
    ),
    "Security": (
        "dependency_audit",
        "architecture_analysis",
        "evidence_capture",
        "ci_analysis",
    ),
    "Research": ("citations", "summarization", "source_aggregation", "documentation_discovery"),
    "Writer": ("summarization", "citations", "documentation_discovery"),
    "Analyst": (
        "summarize_failures",
        "correlate_evidence",
        "operational_timeline",
        "severity_classification",
    ),
    "Architect": (
        "architecture_analysis",
        "code_reasoning_readonly",
        "dependency_audit",
        "documentation_discovery",
    ),
    "DevOps": (
        "ci_analysis",
        "deployment_readiness",
        "operational_timeline",
        "evidence_capture",
    ),
    "Marketing": ("research", "summarization", "citations", "source_aggregation"),
}

_ONE_ONE_RX = re.compile(
    r"\bone\s+"
    r"(development|dev(?:eloper|elopment)?|qa|quality(?:\s+assurance)?|security|research(?:er)?|writer|analyst|architect(?:ure)?|tester|test(?:ing)?|dev\s*ops|sre|marketing|marketer)\s+"
    r"one\s+"
    r"(development|dev(?:eloper|elopment)?|qa|quality(?:\s+assurance)?|security|research(?:er)?|writer|analyst|architect(?:ure)?|tester|test(?:ing)?|dev\s*ops|sre|marketing|marketer)\b",
    re.I,
)
_ROLE_TOKEN_RX = re.compile(
    r"\b(?:one\s+|a\s+)?"
    r"(development|dev(?:eloper|elopment)?|qa|quality(?:\s+assurance)?|security|research(?:er)?|writer|analyst|architect(?:ure)?|tester|test(?:ing)?|dev\s*ops|sre|marketing|marketer)\b",
    re.I,
)
_NAMED_AND_RX = re.compile(
    r"\b([\w][\w\s]{1,40}?)\s+and\s+([\w][\w\s]{1,40}?)\s+agents?\b",
    re.I,
)
_COUNT_RX = re.compile(
    r"\b(?:create|spawn|stand\s+up)\s+(?:\w+\s+){0,3}"
    r"(one|two|three|four|five|\d+)\s+agents?\b",
    re.I,
)
_SKILL_ATTACH_RX = re.compile(
    r"\bassign\s+(?:them\s+)?skills\b|\battach\s+skills\b|\bwith\s+skills\b",
    re.I,
)
_CREATE_BOILERPLATE_RX = re.compile(
    r"^\s*(?:please\s+)?(?:create|spawn|initialize|stand\s+up)\s+"
    r"(?:(?:one|two|three|four|five|\d+|\w+)\s+)*(?:agents?|specialists?)\s*[,:\-]?\s*",
    re.I,
)


def _normalize_role_key(role: str) -> str:
    return re.sub(r"\s+", " ", (role or "").strip().lower())


# Explicit team listing: "team of/with/: A, B and C to <objective>" — captures the roster
# segment so we can spawn an agent per listed role, known or not (dynamic).
_TEAM_LIST_RX = re.compile(
    r"\b(?:team|squad|crew|panel|group|agents?|specialists?)\s*"
    r"(?:of|:|comprising|consisting of|made up of|with|including)\s+"
    r"(.+?)(?:\s+to\s+|\s+that\s+|\s+who\s+|\s+for\s+|\s+so\s+|$)",
    re.I,
)
# Known role keywords longest-first so multi-word matches win (e.g. "operations analyst").
_KNOWN_KEYWORDS = sorted(_ROLE_CAPABILITY.keys(), key=len, reverse=True)
_ARTICLE_RX = re.compile(r"^(?:a|an|one|the|some|several|our|their|my|first|second|third|senior|junior|lead|chief)\s+", re.I)


def _display_for_item(item: str) -> str:
    """Map a listed roster item to a role label — known role if recognizable, else a
    cleaned dynamic label (so 'a chef', 'a CFO', 'a growth hacker' each become agents)."""
    cleaned = (item or "").strip().strip(".,;:")
    # strip leading articles/seniority qualifiers (possibly stacked, e.g. "a senior")
    prev = None
    while cleaned and cleaned != prev:
        prev = cleaned
        cleaned = _ARTICLE_RX.sub("", cleaned).strip()
    key = _normalize_role_key(cleaned)
    if not key or len(key) > 40:
        return ""
    if key in _ROLE_CAPABILITY:
        return _ROLE_CAPABILITY[key][0]
    for kw in _KNOWN_KEYWORDS:
        if kw in key:
            return _ROLE_CAPABILITY[kw][0]
    # Dynamic role: keep the last up-to-3 words as the role noun, Title Cased.
    words = key.split()
    label = " ".join(words[-3:]).title()
    return label or "Specialist"


def _listed_roles(raw: str) -> list[str]:
    m = _TEAM_LIST_RX.search(raw or "")
    if not m:
        return []
    out: list[str] = []
    for part in re.split(r",|\band\b|/|;|\&", m.group(1)):
        disp = _display_for_item(part)
        if disp and disp not in out:
            out.append(disp)
    return out[:8]


# Article-led enumeration: "a strategist, a researcher, ... and a launch manager".
# Catches a team roster even without a "team/squad" cue (e.g. "launch WITH a X, a Y…").
# Requires ≥3 article-led items in a comma/and list so ordinary prose doesn't trip it.
_ENUM_LIST_RX = re.compile(
    r"((?:(?:a|an|one)\s+[a-z][a-z]*(?:\s+[a-z]+){0,2}\s*,\s*){2,}"
    r"(?:and\s+)?(?:a|an|one)\s+[a-z][a-z]*(?:\s+[a-z]+){0,2})",
    re.I,
)


def _enumerated_roles(raw: str) -> list[str]:
    m = _ENUM_LIST_RX.search(raw or "")
    if not m:
        return []
    out: list[str] = []
    for part in re.split(r",|\band\b", m.group(1)):
        disp = _display_for_item(part)
        if disp and disp not in out:
            out.append(disp)
    return out[:8]


def _display_for_token(token: str) -> str:
    key = _normalize_role_key(token)
    if key in _ROLE_CAPABILITY:
        return _ROLE_CAPABILITY[key][0]
    cleaned = re.sub(r"\s+", " ", (token or "").strip())
    if not cleaned:
        return "Task agent"
    return cleaned.title()


def _capability_for_unknown(display: str) -> str:
    key = _normalize_role_key(display)
    if key in _ROLE_CAPABILITY:
        return _ROLE_CAPABILITY[key][1]
    if "qa" in key or "quality" in key or "test" in key:
        return "qa_verification"
    if "dev" in key or "code" in key or "engineer" in key:
        return "dev_workspace"
    if "research" in key or "writer" in key:
        return "research"
    if "security" in key:
        return "code_intelligence"
    return "operations_analyst"


def extract_requested_roles(user_text: str) -> list[str]:
    """Parse natural phrasings into display role labels (no soak/demo defaults)."""
    raw = (user_text or "").strip()
    if not raw:
        return []

    roles: list[str] = []

    pair = _ONE_ONE_RX.search(raw)
    if pair:
        roles.extend([_display_for_token(pair.group(1)), _display_for_token(pair.group(2))])

    if not roles:
        named = _NAMED_AND_RX.search(raw)
        if named:
            roles.extend([_display_for_token(named.group(1)), _display_for_token(named.group(2))])

    # Explicit "team: A, B, C" listing — spawn an agent per listed role (known OR dynamic).
    if not roles:
        listed = _listed_roles(raw)
        if len(listed) >= 2:
            roles = listed

    # Article-led roster ("with a strategist, a researcher, … and a launch manager")
    # even without a team cue — each item becomes an agent (dynamic if unknown).
    if not roles:
        enumerated = _enumerated_roles(raw)
        if len(enumerated) >= 2:
            roles = enumerated

    if not roles:
        for match in _ROLE_TOKEN_RX.finditer(raw):
            label = _display_for_token(match.group(1))
            if label not in roles:
                roles.append(label)

    if not roles:
        count_match = _COUNT_RX.search(raw)
        if count_match:
            token = count_match.group(1).lower()
            count_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
            n = count_map.get(token, int(token) if token.isdigit() else 1)
            roles = [f"Agent {i}" for i in range(1, min(n, 5) + 1)]

    if not roles:
        roles = ["Task agent"]

    return roles[:8]


def attach_skills_requested(user_text: str) -> bool:
    return bool(_SKILL_ATTACH_RX.search(user_text or ""))


def derive_creation_objective(user_text: str) -> str:
    """Objective from the user prompt — never a canned GTM string."""
    raw = (user_text or "").strip()
    if not raw:
        return ""

    cleaned = _CREATE_BOILERPLATE_RX.sub("", raw)
    cleaned = _ONE_ONE_RX.sub("", cleaned)
    cleaned = _SKILL_ATTACH_RX.sub("", cleaned)
    cleaned = re.sub(r"\bto\s+perform\s+best\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,;:-")
    if len(cleaned) < 8:
        return ""
    return cleaned[:500]


def resolve_role_spec(role: str, *, attach_skills: bool) -> tuple[str, str, list[str]]:
    """Return (display label, capability id, skill ids)."""
    key = _normalize_role_key(role)
    if key in _ROLE_CAPABILITY:
        display, capability = _ROLE_CAPABILITY[key]
    elif role.startswith("Agent ") or role == "Task agent":
        display = role
        capability = "dev_workspace" if "Agent 1" in role else "operations_analyst"
    else:
        display = _display_for_token(role) if _normalize_role_key(role) in _ROLE_CAPABILITY else role.strip().title() or "Task agent"
        capability = _capability_for_unknown(display)

    if attach_skills:
        skills = list(_ROLE_SKILLS.get(display, ()))
        if not skills:
            from aethos_core.agents.runtime.registry import build_agent_spec

            spec = build_agent_spec(capability)
            skills = list(spec.allowed)[:6]
    else:
        skills = []

    return display, capability, skills


def plan_role_spawns(user_text: str) -> list[dict[str, Any]]:
    """Full spawn plan for each requested role."""
    attach = attach_skills_requested(user_text)
    objective = derive_creation_objective(user_text)
    plans: list[dict[str, Any]] = []
    for role in extract_requested_roles(user_text):
        display, capability, skills = resolve_role_spec(role, attach_skills=attach)
        goal = f"{display}: {objective}" if objective else f"On-demand {display} agent — ready for assigned work."
        plans.append(
            {
                "role_label": display,
                "capability": capability,
                "skills": skills,
                "goal": goal,
                "objective": objective,
            }
        )
    return plans
