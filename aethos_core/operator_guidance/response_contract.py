# SPDX-License-Identifier: Apache-2.0
"""Standard blocked/failed-state response contract — opinionated, honest, and navigable.

Every blocked or failed reply should answer four questions in the same shape so the operator
is never confused about who does what or where to go:

1. What happened (one honest line).
2. What I (AethOS) can do autonomously — so the operator knows what NOT to do by hand.
3. What only the operator can do — numbered steps, each with the EXACT verified UI surface
   (resolved through the navigation registry, never a hand-typed label).
4. One safe next command.

Composers pass canonical destination KEYS (e.g. "credentials", "approvals") — never raw
labels — so navigation can never drift from the real UI (enforced by
tests/test_navigation_labels_match_ui.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OperatorStep:
    """A step only the operator can perform."""

    action: str
    # Canonical destination key (resolved via the registry) OR empty for a non-UI step.
    surface: str = ""
    why: str = ""


def _resolve_surface(surface: str) -> str:
    if not surface:
        return ""
    from aethos_core.mission_control.visible_navigation_registry import operator_surface

    return operator_surface(surface)


def compose_operator_guidance(
    *,
    headline: str,
    what_happened: str,
    aethos_can_do: list[str] | None = None,
    you_must_do: list[OperatorStep] | None = None,
    safe_next_command: str = "",
    footer: str = "",
) -> str:
    """Render the standard contract. Sections with no content are omitted."""
    lines: list[str] = [f"**{headline}**", "", what_happened.strip()]

    can = [c.strip() for c in (aethos_can_do or []) if c and c.strip()]
    if can:
        lines += ["", "**What I can do for you:**"]
        lines += [f"- {c}" for c in can]

    must = [s for s in (you_must_do or []) if s and s.action.strip()]
    if must:
        lines += ["", "**What needs you (only you can do this):**"]
        for i, step in enumerate(must, start=1):
            surface = _resolve_surface(step.surface)
            row = f"{i}. {step.action.strip()}"
            if surface:
                row += f" — **{surface}**"
            if step.why:
                row += f" ({step.why.strip()})"
            lines.append(row)

    cmd = (safe_next_command or "").strip()
    if cmd:
        lines += ["", f"**Safe next command:** `{cmd}`"]

    if footer and footer.strip():
        lines += ["", footer.strip()]

    return "\n".join(lines)
