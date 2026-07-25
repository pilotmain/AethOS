# SPDX-License-Identifier: Apache-2.0
"""Evidence abstraction — hide internal machinery from human output."""

from __future__ import annotations

import re
from typing import Any

_CITATION_RX = re.compile(r"\s*\[`?(re|rart|rrun|art|artifact)-[a-f0-9]+\`?\]", re.I)
_REPLAY_RX = re.compile(r"(?im)^.*replay:\s*`?rrun-[a-f0-9]+`?\s*$")
_ARTIFACT_SECTION_RX = re.compile(r"(?im)^##\s*(Artifacts|Sources|Confidence|Limitations)\s*$")


def abstract_evidence(text: str) -> str:
    cleaned = _CITATION_RX.sub("", text)
    cleaned = re.sub(r"\[`?(re|rart)-[a-f0-9]+`\]", "", cleaned, flags=re.I)
    return cleaned.strip()


def strip_internal_sections(text: str) -> str:
    lines: list[str] = []
    skip = False
    for line in text.splitlines():
        if _ARTIFACT_SECTION_RX.match(line.strip()):
            skip = True
            continue
        if skip and line.startswith("## "):
            skip = False
        if not skip:
            lines.append(line)
    return "\n".join(lines).strip()
