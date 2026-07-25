# SPDX-License-Identifier: Apache-2.0
"""Artifact suppression — hide runtime internals."""

from __future__ import annotations

import re

_BRACKET_ID_RX = re.compile(r"\[(?:re|rart|rrun|art|artifact)-[a-f0-9]+\]", re.I)
_BACKTICK_ID_RX = re.compile(r"`(?:re|rart|rrun|art|artifact)-[a-f0-9]+`", re.I)
_BARE_ID_RX = re.compile(r"\b(?:re|rart|rrun|art|artifact)-[a-f0-9]+\b", re.I)
_REPLAY_RX = re.compile(r"(?im)^.*replay:\s*`?[a-z]+-[a-f0-9]+`?\s*$")
_SECTION_RX = re.compile(r"(?im)^##\s*(Artifacts|Sources|Confidence|Limitations|Browser verification)\s*[\n\r]+(?:.*[\n\r]+)*?(?=^##|\Z)")


def suppress_artifacts(text: str, *, mode: str = "casual") -> str:
    if mode in ("engineering", "operator", "debug"):
        return text
    cleaned = _BRACKET_ID_RX.sub("", text)
    cleaned = _BACKTICK_ID_RX.sub("", cleaned)
    cleaned = _BARE_ID_RX.sub("", cleaned)
    cleaned = re.sub(r"Replay:\s*(?:rrun|rart|re)-[a-f0-9]+", "", cleaned, flags=re.I)
    cleaned = _SECTION_RX.sub("", cleaned)
    cleaned = re.sub(r"(?im)^##\s*(Artifacts|Sources|Confidence|Limitations|Browser verification)\s*$", "", cleaned)
    cleaned = re.sub(r"(?im)^-\s*(?:re|rart|rrun|art|artifact)-[a-f0-9]+\s*$", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()
