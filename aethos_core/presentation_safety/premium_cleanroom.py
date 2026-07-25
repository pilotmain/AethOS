# SPDX-License-Identifier: Apache-2.0
"""Premium cleanroom — polished output shaping."""

from __future__ import annotations

import re

from aethos_core.conversation.synthesis_stubs import abstract_evidence, strip_internal_sections
from aethos_core.presentation_safety.artifact_suppression import suppress_artifacts


def cleanroom_polish(text: str, *, mode: str = "casual") -> str:
    if mode in ("engineering", "operator", "debug"):
        return text.strip()
    polished = suppress_artifacts(text, mode=mode)
    polished = strip_internal_sections(polished)
    polished = abstract_evidence(polished)
    polished = re.sub(r"\b(?:overall\s+)?confidence\s*:\s*(?:medium|high|low)\s*/\s*0\.\d+\b", "", polished, flags=re.I)
    polished = re.sub(r"\b(?:medium|high|low)\s*/\s*0\.\d+\b", "", polished, flags=re.I)
    polished = re.sub(r"^#+\s+Research synthesis\s*\n+", "", polished, flags=re.I | re.M)
    polished = re.sub(r"\n{3,}", "\n\n", polished)
    return polished.strip()
