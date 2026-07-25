# SPDX-License-Identifier: Apache-2.0
"""Conversational contracts — interaction expectations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConversationalContract:
    calm: bool = True
    no_telemetry: bool = True
    no_artifacts: bool = True
    ranked: bool = False
    followups_allowed: bool = True
