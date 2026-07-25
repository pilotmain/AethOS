# SPDX-License-Identifier: Apache-2.0
"""Conversational surface — user-safe formatting."""

from __future__ import annotations

from aethos_core.presentation_safety.artifact_suppression import suppress_artifacts


def format_for_user(text: str, *, mode: str = "casual") -> str:
    return suppress_artifacts(text, mode=mode)
