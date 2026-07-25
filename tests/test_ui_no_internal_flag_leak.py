# SPDX-License-Identifier: Apache-2.0
"""Production polish guard: internal env-var/feature-flag names must never appear in the
*end-user* web UI, and end-user copy must not instruct users to 'restart the API'.

A disabled feature on an end-user surface should show a clean message ('… is turned off — ask
AethOS in chat how to enable it'); the assistant provides the exact flag on demand (capability-
truth block). Leaking UPPER_SNAKE flag names like WORKSPACE_SUITE_ENABLED into a daily-use tab is
not Fortune-500 polish.

Operator/admin consoles are deliberately exempt: Mission Control → Advanced settings panels and
the provider settings card are for the person who actually sets the config, so showing the exact
env-var key there is the *more* actionable choice (standard for admin UIs like Datadog / GH
Enterprise). The exemption is path-scoped — see ``_ADMIN_SURFACES``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_COMPONENTS = Path(__file__).resolve().parents[1] / "web" / "components"

# UPPER_SNAKE_..._ENABLED env-var/flag names (API fields are lowercase, so this only catches
# the leaked config keys, not legitimate data).
_FLAG_RX = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*_ENABLED\b")
_RESTART_RX = re.compile(r"restart the API", re.I)

# Operator/admin surfaces where exact config keys are allowed (see module docstring).
_ADMIN_SURFACES = (
    "missionControl",  # Mission Control → Advanced settings consoles
    "settings",        # provider/connection settings
)
_ADMIN_FILES = {"ProviderSettingsCard.tsx"}


def _is_admin_surface(p: Path) -> bool:
    return p.name in _ADMIN_FILES or any(part in _ADMIN_SURFACES for part in p.parts)


def _user_facing_tsx() -> list[Path]:
    if not _COMPONENTS.is_dir():
        return []
    return [
        p
        for p in _COMPONENTS.rglob("*.tsx")
        if "__tests__" not in p.parts and not _is_admin_surface(p)
    ]


@pytest.mark.skipif(not _COMPONENTS.is_dir(), reason="web/components not in this checkout")
def test_no_internal_flag_names_in_ui():
    offenders: list[str] = []
    for p in _user_facing_tsx():
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if "process.env" in line:  # legitimate runtime env read, not display text
                continue
            if _FLAG_RX.search(line):
                offenders.append(f"{p.relative_to(_COMPONENTS)}:{i}: {line.strip()[:100]}")
    assert not offenders, "Internal flag names leaked into user-facing UI:\n" + "\n".join(offenders)


@pytest.mark.skipif(not _COMPONENTS.is_dir(), reason="web/components not in this checkout")
def test_no_restart_the_api_instruction_in_ui():
    offenders = [
        f"{p.relative_to(_COMPONENTS)}"
        for p in _user_facing_tsx()
        if _RESTART_RX.search(p.read_text(encoding="utf-8", errors="ignore"))
    ]
    assert not offenders, "UI tells users to 'restart the API' (operator action, not user copy):\n" + "\n".join(offenders)
