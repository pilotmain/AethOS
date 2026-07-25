# SPDX-License-Identifier: Apache-2.0
"""FIX 187 — Markdown renderer for independent repository trust expansion."""

from __future__ import annotations

from typing import Any


def render_independent_repository_trust_expansion(
    independent_repository_trust_expansion: dict[str, Any],
) -> str:
    sections = independent_repository_trust_expansion.get("sections") or {}

    lines = [
        "# Independent Repository Trust Expansion (FIX 187 — trust is non-transferable)",
        "",
        f"- session_id: `{independent_repository_trust_expansion.get('session_id', '')}`",
        f"- phase 1 repository: `{independent_repository_trust_expansion.get('phase_1_repository')}`",
        f"- phase 1 complete: **{independent_repository_trust_expansion.get('phase_1_complete', False)}**",
        f"- next phase 2 repo: `{independent_repository_trust_expansion.get('next_phase_2_repository')}`",
        f"- trust transfer enabled: **{independent_repository_trust_expansion.get('trust_transfer_enabled', False)}** _(always false)_",
        f"- automatic inheritance: **{independent_repository_trust_expansion.get('automatic_repo_trust_inheritance_enabled', False)}** _(always false)_",
        f"- pilot execution performed: **{independent_repository_trust_expansion.get('pilot_execution_performed', False)}** _(always false)_",
        "",
        independent_repository_trust_expansion.get("invariant", ""),
        "",
        "_Each repository earns trust independently — success on AethOS does not imply trust elsewhere._",
        "",
        "## Repository trust registry",
        "",
    ]

    for row in sections.get("repository_trust_registry") or []:
        lines.append(f"### `{row.get('repository')}` — **{row.get('trust_state')}**")
        lines.append(f"- Phase: {row.get('phase')}")
        lines.append(f"- Trust inherited from: `{row.get('trust_inherited_from')}`")
        for stage in row.get("pilot_stages") or []:
            mark = "✓" if stage.get("satisfied") else "○"
            lines.append(f"- {mark} {stage.get('label')}")
        req = row.get("expansion_requirements") or {}
        if req.get("eligible_for_pilot_entry") is not None and row.get("phase") == "dogfood_phase_2":
            lines.append(f"- Eligible for pilot entry: **{req.get('eligible_for_pilot_entry')}**")
        lines.append("")

    seq = (sections.get("phase_2_expansion_sequence") or [{}])[0]
    lines.extend(
        [
            "## Phase 2 expansion sequence",
            "",
            f"Order: {', '.join(seq.get('ordered_repositories') or [])}",
            f"Next awaiting approval: `{seq.get('next_repository_awaiting_approval')}`",
            "",
            "## Expansion requirements (before pilot entry)",
            "",
        ]
    )
    for req in (sections.get("expansion_requirements_checklist") or [{}])[0].get("requirements") or []:
        lines.append(f"- {req}")
    lines.append("")
    lines.append("_Trust expansion contract ≠ pilot execution — registry and gates only._")
    return "\n".join(lines)
